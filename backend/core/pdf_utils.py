"""Shared PDF utilities used by both production_worker.py and mac_worker.py."""

import errno
import hashlib
import logging
import os
import tempfile
import time

import requests
from pypdf import PdfReader

from config import settings

logger = logging.getLogger(__name__)

# arXiv asks downloaders to identify themselves and to space requests out.
_PDF_MAGIC = b"%PDF-"
_ARXIV_POLITE_DELAY_SECONDS = 3.0


class PdfDownloadError(Exception):
    """A PDF download failed, with UI-surfaceable structured detail.

    Mirrors the ``summary_error`` shape (code / message / retryable /
    http_status) so callers can persist or return it without re-deriving the
    fields. The message is safe to show a user: it is built from HTTP status
    and error category, never from raw exception text that could leak a URL
    or an API key.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str,
        retryable: bool,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.http_status = http_status


def _user_agent() -> str:
    """arXiv-friendly User-Agent carrying a contact address (no secrets)."""
    return f"arXiv-AI-Assistant/1.0 (mailto:{settings.EMAIL_SENDER})"


def extract_images_from_pdf(
    pdf_path: str,
    output_dir: str,
    min_width: int = 200,
    min_height: int = 200,
) -> list[dict]:
    """Extract images from a PDF using pymupdf/fitz.

    Skips small images (icons, bullets, decorative elements) based on
    *min_width* / *min_height* thresholds (default 200x200).

    Deduplicates by content hash so the same image embedded on multiple
    pages is only saved once.

    Returns a list of metadata dicts:
        [{"filename": str, "page": int, "width": int, "height": int, "ext": str}, ...]
    """
    import fitz  # pymupdf

    os.makedirs(output_dir, exist_ok=True)
    images: list[dict] = []
    seen_hashes: set[str] = set()
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            if not base_image:
                continue

            image_bytes = base_image["image"]
            image_ext = base_image["ext"]  # png, jpeg, etc.
            width = base_image["width"]
            height = base_image["height"]

            # Skip tiny images (icons, bullets, etc.)
            if width < min_width or height < min_height:
                continue

            # Deduplicate by content hash
            content_hash = hashlib.md5(image_bytes).hexdigest()
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            filename = f"page{page_num + 1}_img{img_idx + 1}.{image_ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            images.append({
                "filename": filename,
                "page": page_num + 1,
                "width": width,
                "height": height,
                "ext": image_ext,
            })

    doc.close()
    return images


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract full text from a PDF file using pypdf."""
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""


def _is_nonempty_file(path: str) -> bool:
    """True if *path* exists and is larger than zero bytes.

    A zero-byte file is the fingerprint of the disk-full incident (an
    interrupted download that left an empty ``<id>.pdf``); treat it as absent
    so the next download replaces it rather than reusing a stub that every
    reader then fails to parse.
    """
    try:
        return os.path.getsize(path) > 0
    except OSError:
        return False


def get_local_pdf_path(arxiv_id: str, pdf_dir: str) -> str | None:
    """Return the path to a usable local PDF, or None if absent or empty.

    Tries the versioned id then the version-stripped id. A zero-byte file is
    treated as missing (see :func:`_is_nonempty_file`), so a disk-full stub is
    never returned as "present".
    """
    for candidate in (arxiv_id, arxiv_id.split("v")[0]):
        path = os.path.join(pdf_dir, f"{candidate}.pdf")
        if _is_nonempty_file(path):
            return path
    return None


def _pdf_error_for_http_status(status: int | None) -> PdfDownloadError:
    """Map an upstream HTTP status to a structured, retryable-aware error.

    429 and 5xx are transient (retryable); other 4xx are structural.
    """
    if status is None:
        return PdfDownloadError(
            "Could not reach arXiv to download the PDF.",
            code="pdf_network_error",
            retryable=True,
        )
    retryable = status == 429 or status >= 500
    return PdfDownloadError(
        f"arXiv returned HTTP {status} while downloading the PDF.",
        code="pdf_http_error",
        retryable=retryable,
        http_status=status,
    )


def _fetch_pdf_bytes(url: str, timeout: int, delay_seconds: float) -> bytes:
    """Fetch and validate PDF bytes from *url*, raising PdfDownloadError.

    Honours arXiv politeness (delay + identifying User-Agent) and refuses an
    empty body or a body that does not start with the ``%PDF-`` magic, so an
    HTML error page is never written as a .pdf.
    """
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    try:
        response = requests.get(
            url, headers={"User-Agent": _user_agent()}, timeout=timeout
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        raise _pdf_error_for_http_status(status) from exc
    except requests.exceptions.Timeout as exc:
        raise PdfDownloadError(
            "The PDF download timed out.", code="pdf_timeout", retryable=True
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise PdfDownloadError(
            "Could not reach arXiv to download the PDF.",
            code="pdf_network_error",
            retryable=True,
        ) from exc
    content = response.content
    if not content or not content.startswith(_PDF_MAGIC):
        raise PdfDownloadError(
            "The downloaded file was not a valid PDF.",
            code="pdf_invalid_body",
            retryable=False,
        )
    return content


def _safe_unlink(path: str) -> None:
    """Remove *path* if present, swallowing the race where it is already gone."""
    try:
        os.unlink(path)
    except OSError:
        pass


def _pdf_write_error(exc: OSError) -> PdfDownloadError:
    """Classify a write/replace OSError, surfacing disk-full distinctly."""
    if exc.errno == errno.ENOSPC:
        return PdfDownloadError(
            "No space left on the PDF storage volume.",
            code="pdf_disk_full",
            retryable=False,
        )
    return PdfDownloadError(
        "Failed to write the PDF to local storage.",
        code="pdf_write_error",
        retryable=False,
    )


def _write_pdf_atomic(content: bytes, final_path: str, pdf_dir: str) -> None:
    """Write *content* to *final_path* via a temp file + ``os.replace``.

    A reader never observes a partial or empty file: the bytes land in a temp
    file in the same directory and are renamed into place only once fully
    written. On any failure the temp file is removed, leaving no stub behind.
    """
    fd, tmp_path = tempfile.mkstemp(dir=pdf_dir, prefix=".pdf-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(content)
        os.replace(tmp_path, final_path)
    except OSError as exc:
        raise _pdf_write_error(exc) from exc
    finally:
        _safe_unlink(tmp_path)


def download_pdf_strict(
    url: str,
    arxiv_id: str,
    pdf_dir: str,
    timeout: int = 60,
    *,
    delay_seconds: float = _ARXIV_POLITE_DELAY_SECONDS,
) -> str:
    """Download *url* to ``<pdf_dir>/<arxiv_id>.pdf``, validated and atomic.

    The single download implementation: fetches with arXiv politeness, refuses
    non-PDF/empty bodies, and writes atomically so no partial or zero-byte file
    is ever left behind. Raises :class:`PdfDownloadError` (disk-full vs
    transient network/HTTP) on failure; returns the final path on success.
    """
    os.makedirs(pdf_dir, exist_ok=True)
    final_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
    logger.info("Downloading %s to %s", url, final_path)
    content = _fetch_pdf_bytes(url, timeout, delay_seconds)
    _write_pdf_atomic(content, final_path, pdf_dir)
    return final_path


def download_pdf(url: str, arxiv_id: str, pdf_dir: str, timeout: int = 60) -> str | None:
    """Lenient download: returns the path on success, None on any failure.

    Backwards-compatible wrapper over :func:`download_pdf_strict` for callers
    (workers, batch scripts) that treat a failed download as a skip. New
    callers that must tell the user *why* a download failed (disk full vs
    upstream) should call :func:`download_pdf_strict` and handle
    :class:`PdfDownloadError`.
    """
    try:
        return download_pdf_strict(url, arxiv_id, pdf_dir, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - lenient wrapper must never crash callers
        logger.error("Download failed for %s: %s", arxiv_id, exc)
        return None
