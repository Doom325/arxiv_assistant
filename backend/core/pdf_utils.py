"""Shared PDF utilities used by both production_worker.py and mac_worker.py."""

import hashlib
import os
import logging
import requests
from pypdf import PdfReader

logger = logging.getLogger(__name__)


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


def get_local_pdf_path(arxiv_id: str, pdf_dir: str) -> str | None:
    """Check for local PDF existence, trying both versioned and base ID."""
    path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
    if os.path.exists(path):
        return path
    # Try version-stripped
    base_id = arxiv_id.split('v')[0]
    path = os.path.join(pdf_dir, f"{base_id}.pdf")
    if os.path.exists(path):
        return path
    return None


def download_pdf(url: str, arxiv_id: str, pdf_dir: str, timeout: int = 60) -> str | None:
    """Download a PDF to pdf_dir. Returns the path on success, None on failure."""
    try:
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
        target_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        logger.info(f"Downloading {url} to {target_path}...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            f.write(response.content)
        return target_path
    except Exception as e:
        logger.error(f"Download failed for {arxiv_id}: {e}")
        return None
