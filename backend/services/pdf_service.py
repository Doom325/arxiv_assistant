"""Unified PDF processing pipeline.

Combines text extraction, section parsing, citation extraction,
embedding generation, and entity extraction into a single service.

Extracted from production_worker.py PDFProcessorLite.
"""

import logging
import re

from core.pdf_utils import extract_text_from_pdf
from core.text_utils import extract_sections
from services.llm_service import llm_service, embedding_service

logger = logging.getLogger(__name__)

# Try importing MLX (only available on Apple Silicon dev machines)
try:
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

# Reference section header patterns (case-insensitive)
REF_HEADERS = [
    r'(^|\n)\s*(\d+\.?\s*)?references[:.]?\s*(\n|$)',
    r'(^|\n)\s*(\d+\.?\s*)?bibliography[:.]?\s*(\n|$)',
    r'(^|\n)\s*(\d+\.?\s*)?citations[:.]?\s*(\n|$)',
    r'(^|\n)\s*(\d+\.?\s*)?works cited[:.]?\s*(\n|$)',
    r'(^|\n)\s*(\d+\.?\s*)?literature cited[:.]?\s*(\n|$)',
    # Less strict fallbacks
    r'\n\s*references\s*\n',
    r'\n\s*bibliography\s*\n',
]


def find_reference_section(full_text: str) -> str | None:
    """Locate and return the reference section text (up to 5000 chars).

    Returns None if no reference section header is found.
    """
    lower_text = full_text.lower()
    for header in REF_HEADERS:
        match = re.search(header, lower_text)
        if match:
            return full_text[match.end():].strip()[:5000]

    return None


def extract_citations(full_text: str) -> list:
    """Extract cited papers from full PDF text using reference section + LLM parsing."""
    ref_section = find_reference_section(full_text)
    if ref_section is None:
        logger.warning("Reference section not found.")
        return []

    # Use LLM to parse (MLX on Mac, Gemini/Ollama elsewhere)
    if HAS_MLX:
        return _parse_citations_with_mlx(ref_section)
    else:
        return llm_service.parse_citations(ref_section)


def _parse_citations_with_mlx(text: str) -> list:
    """Parse citations using local MLX model (Apple Silicon only)."""
    model_repo = "mlx-community/gemma-3-1b-it-8bit"
    logger.info(f"Loading local citation parser: {model_repo}")
    try:
        model, tokenizer = load(model_repo)

        text = text.replace('\r', '\n')
        text = re.sub(
            r'^(references|bibliography|works cited|citations|literature cited)\s*\n?',
            '', text, flags=re.IGNORECASE
        )

        candidates = re.split(r'\n\s*(?=\[|\d+\.|[A-Z][a-z]+,)', text)
        candidates = [c.strip() for c in candidates if len(c.strip()) > 15]

        results = []
        for raw_c in candidates[:12]:
            data = {"raw": raw_c, "title": "", "authors": [], "url": None}

            # Title extraction
            title_prompt = f"""<start_of_turn>user
            Extract the paper title from this citation. Return ONLY the title text.
            Citation: Vaswani et al. (2017). Attention is all you need.
            Title: Attention is all you need

            Citation: {raw_c}
            Title:<end_of_turn>
            <start_of_turn>model
            """
            title_resp = generate(model, tokenizer, prompt=title_prompt, max_tokens=100).strip().split('\n')[0].strip()
            title_resp = re.sub(r'^(title|output|paper title|citation|result|actual title):\s*', '', title_resp, flags=re.IGNORECASE).strip()
            data["title"] = title_resp.strip('"').strip("'").split('<')[0].strip()

            # Authors extraction
            authors_prompt = f"""<start_of_turn>user
            Extract ONLY the author names. Separate names with semicolons.
            Citation: Vaswani, A., Shazeer, N., Parmar, N. (2017).
            Authors: Vaswani, A.; Shazeer, N.; Parmar, N.

            Citation: {raw_c}
            Authors:<end_of_turn>
            <start_of_turn>model
            """
            authors_resp = generate(model, tokenizer, prompt=authors_prompt, max_tokens=60).strip().split('\n')[0].strip()
            authors_resp = re.sub(r'^(authors|names|output|citation|result|actual authors):\s*', '', authors_resp, flags=re.IGNORECASE).strip()

            raw_authors = authors_resp.split('<')[0]
            sep = ';' if ';' in raw_authors else ','
            candidate_authors = [a.strip() for a in raw_authors.split(sep) if a.strip()]

            cleaned_authors = []
            for auth in candidate_authors:
                if data["title"] and data["title"].lower() in auth.lower():
                    auth = auth[:auth.lower().find(data["title"].lower())].strip()
                auth = re.sub(r'\s*\(?\d{4}\)?.*$', '', auth)
                auth = re.sub(r'[,.;\s]+$', '', auth)
                if len(auth) > 2:
                    cleaned_authors.append(auth)

            data["authors"] = cleaned_authors

            # URL extraction
            url_prompt = f"""<start_of_turn>user
            Extract URL if present.
            Citation: Attention is all you need. https://arxiv.org/abs/1706.03762
            URL: https://arxiv.org/abs/1706.03762

            Citation: {raw_c}
            URL:<end_of_turn>
            <start_of_turn>model
            """
            url_resp = generate(model, tokenizer, prompt=url_prompt, max_tokens=80).strip().split('\n')[0].strip()
            url_resp = re.sub(r'^(url|link|output|none|result|actual url):\s*', '', url_resp, flags=re.IGNORECASE).strip()
            url_val = url_resp.split('<')[0].strip()
            data["url"] = url_val if "http" in url_val.lower() else None

            if data["title"] and len(data["title"]) > 5:
                results.append(data)

        return results
    except Exception as e:
        logger.error(f"MLX granular citation parsing error: {e}")
        return []


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

    logger.info(f"Extracting citations from {pdf_path}...")
    citations = extract_citations(text)

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
