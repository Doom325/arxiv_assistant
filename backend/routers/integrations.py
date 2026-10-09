"""Integration endpoints: summarization, email, Google Drive export.

Extracted from papers.py (summarize/email) and library.py (GDrive).
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from config import settings
from database import get_db, SessionLocal
from models import Paper, UserLibrary
from models.paper import (
    SUMMARY_STATUS_FAILED,
    SUMMARY_STATUS_PENDING,
    SUMMARY_STATUS_RUNNING,
    SUMMARY_STATUS_SUCCEEDED,
)
from urllib.parse import urlparse
from services.arxiv_service import arxiv_service
from services.email_service import email_service
from services.gdrive import GoogleDriveService, NeedAuthException
from services.llm_service import (
    get_summarization_provider,
    list_all_summarization_models,
    get_summarization_providers_metadata,
)
from services.summarization_service import summarization_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["integrations"])

# Hardcoded user ID (matches library.py)
USER_ID = 1


# --- Summarization ---

def _record_summary_failure(
    db: Session,
    paper: Paper,
    *,
    code: str,
    message: str,
) -> None:
    """Persist a structured failure for the paper's summarization attempt.

    Does NOT touch ``generated_summary`` — that column is reserved for
    successful model output (or NULL).
    """
    # Naive UTC to match the existing DateTime column (no tzinfo).
    # datetime.utcnow() is deprecated in 3.12+; use aware-then-strip.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    prior_count = 0
    if isinstance(paper.summary_error, dict):
        prior_count = int(paper.summary_error.get("attempt_count") or 0)
    paper.summary_status = SUMMARY_STATUS_FAILED
    paper.summary_error = {
        "code": code,
        "message": message,
        "attempted_at": now.isoformat(),
        "attempt_count": prior_count + 1,
    }
    paper.summary_attempted_at = now
    flag_modified(paper, "summary_error")
    db.commit()


def run_summarization(
    paper_id: int,
    pdf_url: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    endpoint: Optional[str] = None,
):
    """Background task: uses its own DB session (request session may be closed)."""
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return

        # Transition to running so the frontend can distinguish "queued" from
        # "actively processing" if we ever surface it.
        paper.summary_status = SUMMARY_STATUS_RUNNING
        db.commit()

        # Use configured save directory
        pdf_dir = settings.PDF_SAVE_DIR

        # Robust file finding
        filename = f"{paper.arxiv_id}.pdf"
        found = False

        # Check if the exact filename exists first
        if os.path.exists(os.path.join(pdf_dir, filename)):
            found = True
        else:
            # Fallback search
            for f in os.listdir(pdf_dir):
                if f.startswith(paper.arxiv_id):
                    filename = f
                    found = True
                    break

        if not found:
            logger.warning(
                f"PDF not found for paper {paper.arxiv_id} in {pdf_dir}. "
                "Attempting download..."
            )
            filename = f"{paper.arxiv_id}.pdf"
            pdf_path = os.path.join(pdf_dir, filename)
            try:
                arxiv_service.download_pdf(paper.pdf_url, pdf_path)
                found = True
            except Exception as e:
                logger.error(
                    f"Failed to download PDF for {paper.arxiv_id}: {e}"
                )
                _record_summary_failure(
                    db,
                    paper,
                    code="pdf_download_failed",
                    message=f"Failed to download PDF: {e}",
                )
                return

        pdf_path = os.path.join(pdf_dir, filename)

        summary = summarization_service.generate_summary(
            pdf_path,
            model=model,
            temperature=temperature,
            provider=provider,
            endpoint=endpoint,
        )

        # Naive UTC (see _record_summary_failure).
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        paper.generated_summary = summary
        paper.summary_status = SUMMARY_STATUS_SUCCEEDED
        paper.summary_error = None
        paper.summary_attempted_at = now
        db.commit()
        logger.info(f"Generated summary for paper {paper_id}")

    except Exception as e:
        logger.error(f"Summarization failed for paper {paper_id}: {e}")
        try:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                _record_summary_failure(
                    db,
                    paper,
                    code="summarization_failed",
                    message=f"Summarization failed: {e}",
                )
        except Exception:
            # Recovery-path failure (e.g. DB unavailable when trying to
            # record the failure itself). Surface it instead of silently
            # swallowing so operators can find these in logs.
            logger.exception(
                "Failed to record summarization failure for paper %s",
                paper_id,
            )
    finally:
        db.close()


@router.post("/papers/{paper_id}/summarize")
def summarize_paper(
    paper_id: int,
    background_tasks: BackgroundTasks,
    force: bool = False,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if temperature is not None and not (0.0 <= temperature <= 2.0):
        raise HTTPException(
            status_code=400,
            detail=f"temperature must be in [0.0, 2.0], got {temperature}",
        )
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if provider:
        provider = provider.lower().strip()
        if provider not in {"gemini", "nvidia", "local"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider '{provider}'. Must be 'gemini', 'nvidia', or 'local'.",
            )

    if endpoint:
        endpoint = endpoint.strip()
        parsed_url = urlparse(endpoint)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid endpoint URL '{endpoint}'. Must start with http:// or https:// with a valid host.",
            )

    # Validate model selection:
    # 1. Preset models on the curated allowlist are always valid.
    # 2. Custom requests (with explicit provider or endpoint) allow custom model names.
    # 3. Arbitrary model strings without custom provider/endpoint are rejected.
    if model:
        model = model.strip()
        try:
            allowed = {m["id"] for m in list_all_summarization_models()}
        except Exception as e:
            logger.error(f"Failed to load model allowlist: {e}")
            raise HTTPException(status_code=502, detail="Cannot validate model")

        is_allowed_preset = model in allowed
        is_custom_request = bool(provider or endpoint)
        if not is_allowed_preset and not is_custom_request:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model '{model}'. See GET /models/summarization.",
            )

    # A prior failed attempt is retry-eligible without ``force=True``. Only a
    # truly successful summary (generated_summary populated) short-circuits.
    has_success = (
        paper.generated_summary is not None
        and paper.summary_status != SUMMARY_STATUS_FAILED
    )
    if has_success and not force:
        return {
            "message": "Summary already exists",
            "summary": paper.generated_summary,
        }

    # Atomic concurrency claim. Two simultaneous POSTs would otherwise both
    # observe the paper as not-running, both schedule a background task, and
    # both spend tokens on duplicate work. The conditional UPDATE serializes
    # at the DB row lock: exactly one caller observes rowcount==1; the other
    # gets rowcount==0 and is rejected with 409.
    #
    # A prior pending/running attempt is only treated as "in progress" while
    # its ``summary_attempted_at`` is fresh. After the configured stale
    # threshold the attempt is assumed dead (worker crash, lost background
    # task) and the new caller is allowed to override it.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stale_cutoff = now - timedelta(
        seconds=settings.SUMMARY_RUN_STALE_THRESHOLD_SECONDS
    )
    in_progress_states = (SUMMARY_STATUS_PENDING, SUMMARY_STATUS_RUNNING)
    claim = (
        update(Paper)
        .where(Paper.id == paper_id)
        .where(
            or_(
                Paper.summary_status.is_(None),
                Paper.summary_status.notin_(in_progress_states),
                and_(
                    Paper.summary_status.in_(in_progress_states),
                    or_(
                        Paper.summary_attempted_at.is_(None),
                        Paper.summary_attempted_at < stale_cutoff,
                    ),
                ),
            )
        )
        .values(
            summary_status=SUMMARY_STATUS_PENDING,
            summary_error=None,
            summary_attempted_at=now,
        )
    )
    result = db.execute(claim)
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(
            status_code=409,
            detail="Summarization already in progress",
        )

    background_tasks.add_task(
        run_summarization,
        paper_id,
        paper.pdf_url,
        model,
        temperature,
        provider,
        endpoint,
    )
    return {
        "message": "Summarization started",
        "model": model,
        "temperature": temperature,
        "provider": provider,
        "endpoint": endpoint,
    }


@router.get("/models/summarization")
def list_summarization_models():
    """All models the user can pick for summary generation, across providers.
    Each model is tagged with its provider ("gemini", "nvidia", or "local") so the
    frontend can group them. Also returns provider metadata with default models
    and endpoints."""
    try:
        models = list_all_summarization_models()
    except Exception as e:
        logger.error(f"Failed to list summarization models: {e}")
        raise HTTPException(status_code=502, detail="Failed to list models")

    try:
        default_provider, _ = get_summarization_provider(None)
        default = default_provider.default_summarization_model()
    except Exception:
        default = models[0]["id"] if models else None

    return {
        "default_provider": settings.AI_PROVIDER,
        "default": default,
        "models": models,
        "providers": get_summarization_providers_metadata(),
    }


# --- Email ---

class EmailPaperRequest(BaseModel):
    recipient: Optional[str] = None  # If None, sends to all configured recipients


@router.post("/papers/{paper_id}/email")
def email_paper_summary(paper_id: int, request: EmailPaperRequest = EmailPaperRequest(), db: Session = Depends(get_db)):
    """Sends a paper's summary via email."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    recipients = [request.recipient] if request.recipient else settings.RECIPIENT_LIST

    results = []
    for email in recipients:
        success, detail = email_service.send_paper_summary(email.strip(), paper)
        results.append({"email": email.strip(), "sent": success, "detail": detail})

    all_sent = all(r["sent"] for r in results)
    return {
        "message": f"Email sent to {len(recipients)} recipient(s)" if all_sent else "Some emails failed",
        "results": results
    }


@router.get("/papers/email/debug")
def email_debug():
    """Debug endpoint to check email service configuration."""
    try:
        import resend  # noqa: F401
        resend_installed = True
    except ImportError:
        resend_installed = False

    return {
        "resend_installed": resend_installed,
        "resend_api_key_set": bool(settings.RESEND_API_KEY),
        "resend_api_key_preview": settings.RESEND_API_KEY[:10] + "..." if settings.RESEND_API_KEY else "empty",
        "email_sender": email_service.sender_email,
    }


# --- Google Drive Export ---

def _download_pdf_for_export(url: str, arxiv_id: str) -> str:
    """Download PDF for GDrive export (custom UA, existence check)."""
    try:
        pdf_dir = settings.PDF_SAVE_DIR
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)

        target_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        if os.path.exists(target_path):
            return target_path

        logger.info(f"Downloading {url} to {target_path}...")
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            f.write(response.content)
        return target_path
    except Exception as e:
        logger.error(f"Download failed for {arxiv_id}: {e}")
        return None


@router.post("/library/export/gdrive/auth")
def gdrive_auth(code: str, code_verifier: Optional[str] = None):
    try:
        gdrive = GoogleDriveService(
            credentials_path=os.path.join(os.path.dirname(__file__), "..", "credentials.json"),
            token_path=os.path.join(os.path.dirname(__file__), "..", "token.json"),
            catch_auth=False
        )
        gdrive.finish_auth(code, code_verifier=code_verifier)
        return {"message": "Authentication successful! You can now sync your papers."}
    except Exception as e:
        logger.error(f"Auth exchange failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")


def run_gdrive_export(list_name: str, folder_name: str, db: Session):
    try:
        query = db.query(UserLibrary).filter(UserLibrary.user_id == USER_ID)
        if list_name and list_name != "All":
            query = query.filter(UserLibrary.list_name == list_name)
        bookmarks = query.all()

        gdrive = GoogleDriveService(
            credentials_path=os.path.join(os.path.dirname(__file__), "..", "credentials.json"),
            token_path=os.path.join(os.path.dirname(__file__), "..", "token.json")
        )

        folder_id = gdrive.get_or_create_folder(folder_name)
        if not folder_id:
            logger.error("Failed to create GDrive folder")
            return

        for b in bookmarks:
            if not b.paper_id:
                continue
            paper = db.query(Paper).filter(Paper.id == b.paper_id).first()
            if not paper:
                continue

            details = paper.in_drive_details or {}
            if details.get(list_name):
                logger.info(f"Skipping {paper.arxiv_id} (Fast Check): Already synced for list '{list_name}'")
                continue

            pdf_url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
            pdf_path = _download_pdf_for_export(pdf_url, paper.arxiv_id)

            if pdf_path:
                file_id = gdrive.upload_file(pdf_path, folder_id)
                if file_id:
                    details[list_name] = True
                    paper.in_drive_details = details
                    flag_modified(paper, "in_drive_details")
                    db.commit()

        logger.info(f"Background export for {list_name} completed.")
    except Exception as e:
        logger.error(f"Background export failed: {e}")


@router.post("/library/export/gdrive")
def export_to_gdrive(list_name: str, background_tasks: BackgroundTasks, custom_folder_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserLibrary).filter(UserLibrary.user_id == USER_ID)
    if list_name and list_name != "All":
        query = query.filter(UserLibrary.list_name == list_name)

    bookmarks = query.all()
    if not bookmarks:
        return {"message": "No papers found in the specified list"}

    try:
        GoogleDriveService(
            credentials_path=os.path.join(os.path.dirname(__file__), "..", "credentials.json"),
            token_path=os.path.join(os.path.dirname(__file__), "..", "token.json")
        )
    except NeedAuthException as e:
        return {"status": "need_auth", "auth_url": e.auth_url, "code_verifier": e.code_verifier}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initialize GDrive service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize Google Drive service. Check backend logs.")

    folder_name = custom_folder_name or list_name
    background_tasks.add_task(run_gdrive_export, list_name, folder_name, db)

    return {"message": "Sync started in background. Papers will appear in your Google Drive shortly."}
