# Batch Embedding Backfill Plan

## Context

The production database has 80,627 papers but embedding coverage is very low — **91% of papers are invisible to semantic search and timeline.** Additionally, the existing 7,386 search embeddings were generated with raw text (no formatting) by the production worker, inconsistent with the proper formatted approach. We need to regenerate everything with correct formats.

We generate three types of embeddings per paper, each with a specific format:

| Type | Task Type | Input Format | Storage |
|------|-----------|--------------|---------|
| **Search** | `RETRIEVAL_DOCUMENT` | `"title: {title} \| document: {content}"` | `paper_embeddings` table |
| **Abstract clustering** | `CLUSTERING` | `"task_type: clustering \| query: {extracted_abstract}"` | `papers.abstract_embedding` |
| **Intro clustering** | `CLUSTERING` | `"task_type: clustering \| query: {extracted_introduction}"` | `papers.introduction_embedding` |

## Production DB State (verified 2026-03-22)

### Overall (80,627 papers)

| Field | Count | Coverage |
|-------|-------|----------|
| `paper_embeddings` (search — wrong format) | 7,386 | 9.2% |
| `abstract_embedding` (clustering — wrong format) | 11,171 | 13.9% |
| `introduction_embedding` (clustering — wrong format) | 11,493 | 14.3% |
| `extracted_abstract` (text available) | 71,317 | 88.5% |
| `extracted_introduction` (text available) | 65,092 | 80.7% |
| `summary` (arXiv abstract, text available) | 80,627 | 100% |

All existing embeddings are **768D** but were generated with incorrect formats (raw text, no task-specific formatting). All will be regenerated.

### cs.AI — First Batch (5,209 papers)

| Embedding Type | Requests | Source Text |
|---------------|----------|-------------|
| Search | 5,209 (all — regenerate) | `extracted_abstract` → `extracted_intro` → `summary` |
| Abstract clustering | 4,433 (papers with extracted abstract) | `extracted_abstract` |
| Intro clustering | 3,994 (papers with extracted intro) | `extracted_introduction` |
| **Total requests** | **13,636** | |

## Plan

### Step 1: Add `prepare_category_batch()` to `batch_embed_manager.py`

New method that generates **3 JSONL files per category**:

#### File 1: `batch_search_{category}.jsonl`
- **All** papers in category (regenerate existing too)
- Content priority: `extracted_abstract` → `extracted_introduction` → `summary`
- JSONL format:
```json
{"key": "search_{arxiv_id}", "request": {"task_type": "RETRIEVAL_DOCUMENT", "title": "Paper Title", "output_dimensionality": 768, "content": {"parts": [{"text": "title: Paper Title | document: content..."}]}}}
```

#### File 2: `batch_abstract_{category}.jsonl`
- Papers with `extracted_abstract IS NOT NULL` (skip `[FAILED]`/`[DOWNLOAD FAILED]`)
- JSONL format:
```json
{"key": "abstract_{arxiv_id}", "request": {"task_type": "CLUSTERING", "output_dimensionality": 768, "content": {"parts": [{"text": "task_type: clustering | query: extracted abstract text..."}]}}}
```

#### File 3: `batch_intro_{category}.jsonl`
- Papers with `extracted_introduction IS NOT NULL` (skip `[FAILED]`/`[DOWNLOAD FAILED]`)
- JSONL format:
```json
{"key": "intro_{arxiv_id}", "request": {"task_type": "CLUSTERING", "output_dimensionality": 768, "content": {"parts": [{"text": "task_type: clustering | query: extracted intro text..."}]}}}
```

#### Ingestion routing (by key prefix)
- `search_*` → DELETE existing `paper_embeddings` row for paper, INSERT new one
- `abstract_*` → UPDATE `papers.abstract_embedding`
- `intro_*` → UPDATE `papers.introduction_embedding`

**File:** `backend/batch_embed_manager.py`
- Add method `prepare_category_batch(category)`
- Add method `ingest_category_results(filename)` with key-prefix routing
- Fix `output_dimensionality`: 3072 → 768
- Add CLI subcommands: `prepare_category --category cs.AI`, `ingest_category --file ...`

### Step 2: Run for cs.AI from Mac via SSH tunnel

```bash
# Terminal 1: SSH tunnel
ssh -L 5434:localhost:5434 khadas@192.168.1.49

# Terminal 2: Prepare, submit, monitor
cd backend
export DATABASE_URL="postgresql://user:password@localhost:5434/arxiv_db"

# Prepare 3 JSONL files for cs.AI
python batch_embed_manager.py prepare_category --category cs.AI

# Submit all batch files
python batch_embed_manager.py submit_all

# Monitor and ingest when complete
python batch_embed_manager.py monitor
```

### Step 3: Verify cs.AI

```sql
-- Search embeddings for cs.AI (should be 5,209)
SELECT COUNT(*) FROM paper_embeddings pe
JOIN papers p ON p.id = pe.paper_id WHERE p.category = 'cs.AI';

-- Abstract embeddings for cs.AI (should be ~4,433)
SELECT COUNT(*) FROM papers
WHERE category = 'cs.AI' AND abstract_embedding IS NOT NULL;

-- Intro embeddings for cs.AI (should be ~3,994)
SELECT COUNT(*) FROM papers
WHERE category = 'cs.AI' AND introduction_embedding IS NOT NULL;

-- Verify dimensions are consistent
SELECT vector_dims(embedding), COUNT(*) FROM paper_embeddings pe
JOIN papers p ON p.id = pe.paper_id WHERE p.category = 'cs.AI' GROUP BY 1;
```

### Step 4: Roll out to remaining categories

```bash
# Get categories by paper count
psql -c "SELECT category, COUNT(*) FROM papers GROUP BY 1 ORDER BY 2 DESC;"

# Run per category
for cat in cs.LG cs.CL cs.CV cs.RO ...; do
  python batch_embed_manager.py prepare_category --category "$cat"
  python batch_embed_manager.py submit_all
  python batch_embed_manager.py monitor
done
```

## Files to Modify

| File | Change |
|------|--------|
| `backend/batch_embed_manager.py` | Add `prepare_category_batch()`, `ingest_category_results()`, fix dimensionality to 768, add CLI subcommands |

## Cost Estimate

- cs.AI: ~13.6K requests → ~$0.14
- All categories: ~220K requests → ~$2.20 total
- Gemini Batch API: 50% discount vs real-time

## Risks & Mitigations

- **Regenerating existing embeddings**: Search results may briefly change. Ingestion is atomic per-row (delete old + insert new).
- **Batch job failure**: Per-category batching limits blast radius. Re-submit the failed category.
- **DB connection drop**: Search embeddings commit every 100 rows. Inline embeddings commit per-row.
- **Papers without extracted text**: Abstract/intro clustering only generated for papers that have the text. Search embedding falls back to `summary`.
- **Turnaround**: Gemini batch SLO is 24h, typically completes in 1-4h.
