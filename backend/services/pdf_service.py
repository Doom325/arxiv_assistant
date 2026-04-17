"""Unified PDF processing pipeline.

Combines text extraction, section parsing, citation extraction,
embedding generation, and entity extraction into a single service.

Extracted from production_worker.py PDFProcessorLite.
"""

import logging

from core.pdf_utils import extract_text_from_pdf
from core.text_utils import extract_sections
from services.llm_service import llm_service, embedding_service
from services.grobid_service import extract_references_from_pdf

logger = logging.getLogger(__name__)


def extract_citations(pdf_path: str) -> list:
    """Extract cited papers from a PDF using GROBID.

    Sends the PDF to GROBID's /api/processReferences endpoint, which
    returns structured references as TEI-XML. The grobid_service module
    parses these into the {raw, title, authors, url} dicts that
    resolve_citations() in citation_service.py expects.

    Returns an empty list on any failure (GROBID down, malformed PDF, etc.).
    """
    return extract_references_from_pdf(pdf_path)


def process_pdf(pdf_path: str) -> dict | None:
    """Full PDF processing pipeline: extract text, sections, citations, embeddings, entities.

    Returns a dict with keys: file, sections, citations, entities, embeddings.
    Returns None if no text could be extracted.
    """
    logger.info(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        logger.warning(f"No text extracted from {pdf_path}")
        return None

    logger.info(f"Extracting sections from {pdf_path}...")
    sections = extract_sections(text)

    logger.info(f"Extracting citations via GROBID from {pdf_path}...")
    citations = extract_citations(pdf_path)

    # Generate Embeddings using dedicated embedding service (Gemini for MRL quality)
    logger.info(f"Generating embeddings via {embedding_service.__class__.__name__} for {pdf_path}...")

    abstract_text = sections.get('abstract', '') or ""
    intro_text = sections.get('introduction', '') or ""

    abstract_emb = embedding_service.generate_embedding(abstract_text) if abstract_text.strip() else []
    intro_emb = embedding_service.generate_embedding(intro_text) if intro_text.strip() else []

    # Extract Entities (GLiNER or LLM based on ENTITY_EXTRACTION_PROVIDER config)
    logger.info(f"Extracting entities for {pdf_path}...")
    from services.nlp_service import nlp_service
    entity_text = f"{sections.get('abstract', '')}\n{sections.get('introduction', '')}"[:2000]
    entities = nlp_service.extract_entities(entity_text)

    return {
        "file": pdf_path,
        "sections": sections,
        "citations": citations,
        "entities": entities,
        "embeddings": {
            "abstract": abstract_emb,
            "introduction": intro_emb
        }
    }
