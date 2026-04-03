---
name: debug-worker
description: Diagnoses and fixes issues in the production worker pipeline (PDF processing, embedding generation, entity extraction, citation parsing, pattern classification). Use when the user reports worker errors, stuck papers, or processing failures.
---

# Debug Worker Pipeline

The production worker (`backend/production_worker.py`) processes papers through a multi-stage pipeline. Use this guide to diagnose failures.

## Pipeline Stages

1. **PDF Download** → `core/pdf_utils.py` downloads PDF to `PDF_SAVE_DIR`
2. **Text Extraction** → `services/pdf_service.py` extracts text and sections
3. **Embedding Generation** → `services/llm_service.py` generates 3072D vector
4. **Entity Extraction** → `services/nlp_service.py` (GLiNER) extracts 8 entity types
5. **Citation Parsing** → `services/citation_service.py` + LLM extracts arXiv IDs
6. **Citation Resolution** → Links extracted IDs to local papers via `CitationLink`
7. **Pattern Classification** → `taxonomy.py` V6 CoT prompt classifies agentic patterns

## Diagnostic Steps

### Step 1: Check JobLog

Query the `JobLog` table for recent failures:

```python
# In a diagnostic script or Python shell
from models import JobLog
from database import SessionLocal
db = SessionLocal()
recent_failures = db.query(JobLog).filter(JobLog.status == 'failed').order_by(JobLog.created_at.desc()).limit(10).all()
```

### Step 2: Identify the Failing Stage

Check which stage failed by examining the `job_type` field in `JobLog`. Common failures:
- `pdf_download`: Network timeout, arXiv rate limiting (3s delay required), 404 for withdrawn papers
- `text_extraction`: Corrupted PDF, scanned-only PDF (no extractable text)
- `embedding`: API quota exceeded (Gemini), model not loaded (Ollama)
- `entity_extraction`: GLiNER model OOM, malformed text input
- `citation_parsing`: LLM timeout, malformed response parsing
- `pattern_classification`: V6 CoT prompt issues, model refusal

### Step 3: Check Provider Status

- **Gemini:** Check API quota in Google Cloud Console. Rate limits apply.
- **Ollama:** Verify models are running: `curl http://localhost:11434/api/tags`
- **GLiNER:** Check memory usage — GLiNER loads a large model into RAM.

### Step 4: Examine the Paper Record

```python
paper = db.query(Paper).filter(Paper.id == paper_id).first()
# Check: paper.full_text (None = extraction failed)
# Check: paper.embedding (None = embedding failed)
# Check: paper.entities_json (None = entity extraction failed)
```

### Step 5: Manual Reprocessing

The worker picks up unprocessed papers automatically. To force reprocessing:
- Set the relevant field to NULL in the database
- The worker will re-pick it on the next poll cycle (15 seconds)

## Common Fixes

- **arXiv 429 errors:** Increase the rate limit delay in `arxiv_service.py` (currently 3s)
- **Embedding dimension mismatch:** Verify `EMBEDDING_PROVIDER` config matches the expected 3072D
- **Worker stuck in loop:** Check for papers that consistently fail — add to a skip list or fix the root cause
- **OOM on GLiNER:** Reduce batch size in worker or increase container memory limits
