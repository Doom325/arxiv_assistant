---
category: review-protocol
subject: pdf-on-demand-acceptance-criteria
---

Pipeline loom_arxiv-pdf-on-demand (feat/pdf-download-on-demand). Feature: on-demand single-paper PDF download from UI + hardening PDF download/lookup after an incident (drive filled, 3710 zero-byte <arxiv_id>.pdf left, summarization failed with generic "Failed to extract text from PDF"). Scope: core/pdf_utils.py, services/arxiv_service.py, routers/integrations.py, routers/papers.py, schemas, frontend lib/api.ts + paper page + error UI.

REVIEW ACCEPTANCE CRITERIA (all must hold before APPROVE):
(a) No code path leaves a zero-byte/partial FINAL pdf: atomic temp+replace, %PDF- magic check, cleanup on EVERY failure incl. ENOSPC/disk-full.
(b) A zero-byte file is treated as MISSING at EVERY lookup site, not just one.
(c) All THREE previous download implementations now funnel through the one helper.
(d) New endpoint is idempotent, validates ids (NO path traversal), follows the router's existing auth conventions, and returns the PR#57-style structured error (code/message/retryable) INCLUDING a distinct disk-full error code.
(e) No per-row filesystem hit on list endpoints.
(f) Frontend shows the real server message and updates state on success.

REVIEWER WORKFLOW CONSTRAINTS (operator directive): do NOT poll inbox / no '/loop receive' (requests are injected). Do review in OWN git worktree off the PR branch (never shared main). Build OWN venv per review (uv venv --python 3.12 .venv; install backend/requirements.txt minus gliner + pytest pytest-timeout; resolver silent 1-2 min, run in background to a file). macOS has no GNU timeout -> use pytest --timeout=90. Scope tests to changed files; don't run full suite while peers active. Require evidence new tests FAIL on old code. Frontend: symlink ~/git/arxiv_assistant/frontend/node_modules into worktree, remove symlink after. Known-unrelated main failures: test_backfill_parallel.py(2), test_batch_submission.py::test_submission, test_citations_remote.py::test_citations; test_email_template/test_summarization/test_summarization_mlx/test_vector_search uncollectable w/o Postgres/ollama/mlx/torch. Always relay verdict on same PR key AND confirm the send succeeded. Severity floor for residue: issue only if reader MISLED / work LOST / gate SILENTLY WRONG; else fix-in-passing or one PR-body line. Coder FORBIDDEN to merge until operator says "GO MERGE" — after APPROVE just send APPROVED, never instruct merge.
