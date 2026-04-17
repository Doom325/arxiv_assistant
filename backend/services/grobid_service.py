"""GROBID client — PDF → structured references.

Replaces the LLM-based citation extraction that previously went through
OllamaProvider.parse_citations + a chunker. GROBID processes a whole PDF
in 1-5s with >95% F1 on academic papers (it's the same extractor Semantic
Scholar, AllenAI, and Inspire-HEP rely on).

The public entry point is `extract_references_from_pdf(pdf_path)` which
returns citation dicts in the shape `resolve_citations()` in
`services/citation_service.py` expects:

    [{"raw": "...", "title": "...", "authors": [...], "url": "..."}]

The `raw` field is the load-bearing contract: `citation_service`'s regex
(ARXIV_ID_PATTERN) scans it for the canonical arXiv ID. We reconstruct
`raw` with the arXiv ID inline so that match still fires.
"""

from __future__ import annotations

import logging
import os

import requests
from lxml import etree

from config import settings

logger = logging.getLogger(__name__)

# TEI namespace used throughout GROBID's output
_TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

# Upper bound for GROBID calls. A single PDF typically completes in 1-5s;
# we've observed up to ~30s for very long reference lists. 180s is the
# established convention for gateway-ish calls in this backend (see
# the HTTP-client patterns in services/llm_service.py).
_REQUEST_TIMEOUT = 180


def _text(node, xpath: str) -> str | None:
    """Extract stripped text at xpath, or None if empty/missing."""
    if node is None:
        return None
    found = node.find(xpath, namespaces=_TEI_NS)
    if found is None or found.text is None:
        return None
    stripped = found.text.strip()
    return stripped or None


def _full_text(node) -> str:
    """Flatten all descendant text of a TEI element into a single
    whitespace-normalized string."""
    if node is None:
        return ""
    parts = node.xpath(".//text()")
    joined = " ".join(p.strip() for p in parts if p and p.strip())
    return " ".join(joined.split())  # collapse runs of whitespace


def _parse_authors(bibl_struct) -> list[str]:
    """Authors rendered as 'Forename Surname' strings. Missing parts are
    elided rather than filled with placeholders."""
    authors = []
    for pers in bibl_struct.iterfind(".//tei:analytic/tei:author/tei:persName", _TEI_NS):
        forename = _text(pers, "tei:forename") or ""
        surname = _text(pers, "tei:surname") or ""
        full = f"{forename} {surname}".strip()
        if full:
            authors.append(full)
    if authors:
        return authors
    # Fallback for monographs (books / theses) where authors live on monogr instead
    for pers in bibl_struct.iterfind(".//tei:monogr/tei:author/tei:persName", _TEI_NS):
        forename = _text(pers, "tei:forename") or ""
        surname = _text(pers, "tei:surname") or ""
        full = f"{forename} {surname}".strip()
        if full:
            authors.append(full)
    return authors


def _parse_title(bibl_struct) -> str:
    """Prefer the analytic title (paper within conference) → monogr level-m
    (the book/journal itself) → anything with @type='main'."""
    for xp in (
        ".//tei:analytic/tei:title[@type='main']",
        ".//tei:analytic/tei:title",
        ".//tei:monogr/tei:title[@level='m']",
        ".//tei:monogr/tei:title",
    ):
        found = bibl_struct.find(xp, namespaces=_TEI_NS)
        if found is not None and found.text:
            t = found.text.strip()
            if t:
                return t
    return ""


def _parse_ids(bibl_struct) -> dict[str, str]:
    """Pull out structured identifiers. Keys match GROBID's @type values."""
    ids: dict[str, str] = {}
    for idno in bibl_struct.iterfind(".//tei:idno", _TEI_NS):
        id_type = (idno.get("type") or "").strip()
        if id_type and idno.text:
            ids[id_type] = idno.text.strip()
    return ids


def _parse_url(bibl_struct) -> str:
    """First <ptr target="..."> URL, or derive from DOI if present."""
    ptr = bibl_struct.find(".//tei:ptr[@target]", namespaces=_TEI_NS)
    if ptr is not None:
        target = ptr.get("target", "").strip()
        if target:
            return target
    ids = _parse_ids(bibl_struct)
    if "DOI" in ids:
        return f"https://doi.org/{ids['DOI']}"
    return ""


def _build_raw(title: str, authors: list[str], ids: dict[str, str], url: str,
               fallback_text: str) -> str:
    """Reconstruct a one-line plaintext citation that includes any arXiv ID
    verbatim — that's what citation_service.ARXIV_ID_PATTERN scans.

    If structured parsing extracted nothing (rare but possible on malformed
    entries), fall back to the flattened TEI text so there's always SOMETHING
    for downstream dedup + display.
    """
    pieces: list[str] = []
    if authors:
        pieces.append(", ".join(authors))
    if title:
        pieces.append(title)
    if "arXiv" in ids:
        pieces.append(f"arXiv:{ids['arXiv']}")
    if "DOI" in ids:
        pieces.append(f"doi:{ids['DOI']}")
    if url and url not in pieces:
        pieces.append(url)
    joined = ". ".join(p for p in pieces if p)
    return joined if joined else fallback_text


def _parse_tei(xml_bytes: bytes) -> list[dict]:
    """Parse GROBID's TEI-XML response into our citation-dict schema."""
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        logger.error(f"GROBID returned malformed TEI: {e}")
        return []

    results: list[dict] = []
    for bibl in root.iterfind(".//tei:biblStruct", _TEI_NS):
        title = _parse_title(bibl)
        authors = _parse_authors(bibl)
        ids = _parse_ids(bibl)
        url = _parse_url(bibl)
        fallback_text = _full_text(bibl)
        raw = _build_raw(title, authors, ids, url, fallback_text)

        # Skip entries with no usable content — GROBID sometimes emits empty
        # biblStructs for malformed citations; no point propagating them.
        if not raw.strip():
            continue

        results.append({
            "raw": raw,
            "title": title,
            "authors": authors,
            "url": url,
            # Non-contract extras useful for UI / future use. resolve_citations
            # ignores these, but it also doesn't reject unknown keys.
            "arxiv_id": ids.get("arXiv", ""),
            "doi": ids.get("DOI", ""),
        })
    return results


def extract_references_from_pdf(pdf_path: str) -> list[dict]:
    """Send a PDF to GROBID's /api/processReferences and parse the response.

    Returns an empty list on any failure (unreachable server, bad response,
    malformed XML). Matches the log-and-return-empty convention used by
    other gateway clients in this backend (see llm_service error handlers).
    """
    if not pdf_path or not os.path.isfile(pdf_path):
        logger.warning(f"GROBID: PDF not found at {pdf_path}")
        return []

    url = f"{settings.GROBID_URL.rstrip('/')}/api/processReferences"
    try:
        with open(pdf_path, "rb") as fh:
            files = {"input": (os.path.basename(pdf_path), fh, "application/pdf")}
            # consolidateCitations=0 — skip external CrossRef lookup for speed.
            # includeRawCitations=1 — ask GROBID to also include the <note
            # type="raw_reference"> node; we currently rebuild `raw` ourselves
            # from the structured fields, but having the source text around
            # means we can fall back to it if needed.
            data = {"consolidateCitations": "0", "includeRawCitations": "1"}
            resp = requests.post(url, files=files, data=data, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"GROBID request failed for {pdf_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"GROBID unexpected error for {pdf_path}: {type(e).__name__}: {e}")
        return []

    return _parse_tei(resp.content)


def is_alive() -> bool:
    """Health probe — returns True if GROBID responds with 'true' at /api/isalive."""
    url = f"{settings.GROBID_URL.rstrip('/')}/api/isalive"
    try:
        resp = requests.get(url, timeout=10)
        return resp.status_code == 200 and resp.text.strip().lower() == "true"
    except Exception:
        return False
