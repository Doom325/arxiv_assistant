---
name: inspect-database
description: Uses the PostgreSQL MCP server to directly query the arxiv_assistant database — inspect tables, check paper counts, verify embeddings, debug search queries, examine worker job logs, and diagnose data issues. Use when the user asks about database state, data problems, missing papers, failed jobs, or search quality.
---

# Inspect Database

Use the **postgres** MCP tool to query the arxiv_assistant PostgreSQL database directly. This avoids writing throwaway scripts — just run SQL.

## Connection

The database runs on port **5434** (not 5432). The MCP server connects via `DATABASE_URL` from the environment.

## Common Queries

### Paper Statistics
```sql
-- Total papers
SELECT COUNT(*) FROM papers;

-- Papers by category
SELECT unnest(categories) AS category, COUNT(*) FROM papers GROUP BY category ORDER BY count DESC LIMIT 20;

-- Papers missing embeddings (need worker processing)
SELECT COUNT(*) FROM papers WHERE embedding IS NULL;

-- Papers missing summaries
SELECT COUNT(*) FROM papers WHERE summary IS NULL;

-- Recent papers (last 7 days)
SELECT id, arxiv_id, title, created_at FROM papers ORDER BY created_at DESC LIMIT 20;
```

### Worker Job Health
```sql
-- Recent job failures
SELECT job_type, status, error_message, created_at
FROM job_logs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;

-- Job success rate by type (last 24h)
SELECT job_type,
  COUNT(*) FILTER (WHERE status = 'completed') AS success,
  COUNT(*) FILTER (WHERE status = 'failed') AS failed
FROM job_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY job_type;

-- Stuck/pending batch queue items
SELECT COUNT(*), status FROM batch_queue GROUP BY status;
```

### Search Debugging
```sql
-- Verify tsvector content for a paper
SELECT id, title, ts_rank(search_vector, to_tsquery('english', 'transformer')) AS rank
FROM papers
WHERE search_vector @@ to_tsquery('english', 'transformer')
ORDER BY rank DESC
LIMIT 10;

-- Check pgvector index exists
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'papers' AND indexdef LIKE '%vector%';

-- Embedding dimension check
SELECT id, array_length(embedding::float[], 1) AS dim FROM papers WHERE embedding IS NOT NULL LIMIT 5;
```

### Citation Graph
```sql
-- Most cited papers (by local references)
SELECT p.title, COUNT(cl.id) AS citation_count
FROM citation_links cl
JOIN papers p ON p.id = cl.resolved_paper_id
WHERE cl.resolved_paper_id IS NOT NULL
GROUP BY p.id, p.title
ORDER BY citation_count DESC
LIMIT 20;

-- Unresolved citations
SELECT COUNT(*) FROM citation_links WHERE resolved_paper_id IS NULL;
```

### Entity Extraction
```sql
-- Papers with entities extracted
SELECT COUNT(*) FROM papers WHERE entities_json IS NOT NULL;

-- Sample entities from a paper
SELECT id, title, entities_json FROM papers WHERE entities_json IS NOT NULL LIMIT 3;
```

### User & Library
```sql
-- Bookmarked papers
SELECT ul.list_name, p.title, ul.created_at
FROM user_library ul
JOIN papers p ON p.id = ul.paper_id
ORDER BY ul.created_at DESC
LIMIT 20;
```

## Schema Reference

| Table | Key Columns |
|-------|------------|
| `papers` | id, arxiv_id, title, abstract, authors, categories, full_text, embedding (Vector 3072), search_vector (tsvector), summary, entities_json, sections_json |
| `paper_embeddings` | id, paper_id, embedding, model_name |
| `users` | id, email |
| `user_configs` | id, user_id, keywords, categories, schedule |
| `user_library` | id, user_id, paper_id, list_name |
| `job_logs` | id, job_type, status, error_message, paper_id, created_at |
| `summarization_metrics` | id, paper_id, model, input_tokens, output_tokens, duration_ms |
| `batch_queue` | id, paper_id, status |
| `citation_links` | id, source_paper_id, target_arxiv_id, resolved_paper_id |
| `prompt_templates` | id, name, template, version |
| `pattern_experiment_results` | id, paper_id, is_agentic, primary_category, patterns, confidence |

## Guidelines

- Use `SELECT` queries only for inspection. Never run `UPDATE`, `DELETE`, or `DROP` without explicit user confirmation.
- For large result sets, always use `LIMIT`.
- When debugging embedding issues, check both the `papers.embedding` column and the `paper_embeddings` table.
- The `categories` column is a PostgreSQL array — use `unnest()` or `ANY()` for filtering.
