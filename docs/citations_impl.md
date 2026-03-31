# Citation Extraction Implementation

This document provides a detailed technical overview of the citation extraction and resolution pipeline in the ArXiv Assistant project.

## 1. Architecture Overview

The citation pipeline is designed to be hybrid, leveraging Large Language Models (LLMs) for semantic parsing and traditional regex/NLP for structure identification and resolution.

### Core Components
- **`production_worker.py`**: The main execution engine that monitors the database for new papers, downloads PDFs, and triggers extraction.
- **`PDFProcessorLite`**: A lightweight PDF processor using `pypdf` that extracts text and identifies sections (Abstract, Introduction, References).
- **`llm_service.py`**: A provider-agnostic service (Gemini/Ollama) used for high-quality structured parsing of citation blocks.
- **`models.py`**: Defines the `Paper` (JSON metadata) and `CitationLink` (relational graph) models.

---

## 2. The Extraction Workflow

### Phase A: Section Identification
The system first isolates the bibliography using keyword-based regex matching. It searches for common headers such as:
- References
- Bibliography
- Works Cited
- Literature Cited

Once the section is found, the text from that point forward (truncated to 5000 characters to manage context size) is extracted for parsing.

### Phase B: Semantic Parsing
Citations are rarely uniform. To handle various styles (APA, IEEE, BIBTEX, etc.), the system uses one of two paths:

1. **Cloud/Server Path (Default)**:
   The isolated reference block is sent to the LLM (Gemini 2.0 Flash or Ollama) with a specific prompt:
   - **Input**: Raw text block.
   - **Extraction Fields**: `title`, `authors`, `url`, `raw`.
   - **Output**: Structured JSON list.

2. **Local MLX Path (Mac Optimized)**:
   If running on a Mac with `mlx-lm` installed, the system uses a local 1B model (`mlx-community/gemma-3-1b-it-8bit`) for granular parsing to reduce API costs.

### Phase C: Resolution and Linking
After structured citations are extracted, the system attempts to "resolve" them to known papers in the ArXiv Assistant database.

1. **Regex Extraction**: The system scans the `raw` text of each citation for ArXiv ID patterns (e.g., `YYMM.XXXXX`).
2. **Database Lookup**: If an ID is found, it queries the `papers` table to see if that paper is already indexed.
3. **Link Creation**: A record is created in the `citation_links` table:
   - `source_paper_id`: The paper being processed.
   - `target_arxiv_id`: The ID found in the citation.
   - `resolved_paper_id`: Foreign key to the target paper if it exists in the DB.
   - `is_arxiv`: Boolean flag.

---

## 3. Data Structures

### `Paper.citations` (JSON/JSONB)
Stores the raw and parsed data as a snapshot of what the LLM found.
```json
[
  {
    "title": "Attention Is All You Need",
    "authors": ["Vaswani, A.", "Shazeer, N."],
    "url": "https://arxiv.org/abs/1706.03762",
    "raw": "[42] Vaswani, A., et al. (2017). Attention is all you need. arXiv:1706.03762.",
    "resolved_id": "1706.03762"
  }
]
```

### `citation_links` Table
Enables relational queries for "Cited By" and "Cross-references" features.
| Column | Type | Description |
| :--- | :--- | :--- |
| `source_paper_id` | Integer | FK to papers.id (Source) |
| `target_arxiv_id` | String | Extracted ID from text |
| `resolved_paper_id`| Integer | FK to papers.id (Target) |
| `is_arxiv` | Boolean | True if ID matched ArXiv pattern |

---

## 4. Batch Processing

For high-volume ingestion (e.g., backfilling thousands of papers), the system uses `batch_collector_v2.py`.
- **Technique**: Uses the Gemini Batch API to process several hundred papers at once asynchronously.
- **Workflow**: `batch_submitter.js` (Node) sends jobs -> `batch_collector_v2.py` (Python) collects results and updates the database using direct SQL for performance.

---

## 5. Challenges & Heuristics

- **Text Extraction**: PDFs with complex two-column layouts or nested figures can break text flow. `pypdf` is used as a balance between speed and reliability.
- **Deduplication**: The system uses exact ArXiv ID matching for resolution. For non-ArXiv citations, it uses title-based uniqueness heuristics.
- **Cleaning**: `llm_service` includes a `sanitize_text` method to strip null bytes and UTF-16 surrogates that often crash DB drivers or API requests.
