---
type: subsystem
summary: End-to-end error surfacing for paper summarization: NVIDIA/Gemini/local providers -> summarization_service -> run_summarization background task -> Paper.summary_error (JSON) -> GET /papers/{id} polling -> frontend error UI.
entry_points:
  - NvidiaProvider.summarize_text
  - SummarizationService.generate_summary
  - run_summarization
  - _record_summary_failure
  - formatSummaryError
  - useSummarize
covers:
  - backend/services/llm_service.py
  - backend/routers/integrations.py
  - backend/models/paper.py
  - frontend/lib/useSummarize.ts
  - frontend/lib/summaryError.ts
  - frontend/lib/api.ts
  - frontend/app/paper/[id]/page.tsx
last_commit: 80b54b6
edges:
  - to: pdf-download-storage type: related_to reason: run_summarization downloads missing PDFs via the pdf-download-storage helper and records pdf_download_failed with the real reason
---

- Summarization is a background task, not synchronous. POST /papers/{id}/summarize claims the row (atomic UPDATE, 409 if already pending/running & fresh), schedules run_summarization via FastAPI BackgroundTasks, returns 'Summarization started'. Frontend POLLS GET /papers/{id} every 3s reading summary_status (pending|running|succeeded|failed) + summary_error, with a 30-min client timeout. The POST response body carries no failure — the real error lands in Paper.summary_error. <!-- id:700a -->
- Paper.summary_error is JSON (sqlite) / JSONB (postgres) — adding keys needs NO migration. Shape: {code, message, attempted_at, attempt_count, retryable, http_status?, provider?}. Written ONLY by _record_summary_failure in routers/integrations.py; cleared to None on success. generated_summary holds ONLY successful output or NULL (never an error sentinel). <!-- id:1145 -->
- ProviderError (services/llm_service.py) carries structured upstream failure detail (message, provider, http_status, retryable) end-to-end so the UI shows the real cause. _is_retryable_status(): retryable = status in {408,409,425,429} or >=500 (transient); other 4xx = structural. NvidiaProvider.summarize_text raises ProviderError on every failure path (HTTP via _http_provider_error, timeout/connection via _network_provider_error, empty content / malformed choices via _extract_summary/_shape_provider_error). Missing API key still raises plain ValueError (config error; an existing test asserts it). routers/integrations._summary_failure_fields maps a ProviderError to the summary_error kwargs; non-ProviderError falls back to 'Summarization failed: {e}', retryable=False. <!-- id:16c1 -->
- Frontend: formatSummaryError(summary_error) in lib/summaryError.ts is the single formatter — surfaces message verbatim, appends '(This may be temporary — try again.)' when retryable. Both useSummarize.ts (used by QuickPeekSheet, DashboardQuickPeek, QuickPreviewPanel which render the hook's `error` string) and app/paper/[id]/page.tsx (its own inline poller using alert()) call it. SummaryError type in lib/api.ts gained retryable/http_status/provider. Note: commit 627b492 already surfaced the HTTP-error message end-to-end; this change closes the empty-content/malformed gaps and adds the transient-vs-structural signal. <!-- id:1b56 -->
- Testing/env: backend uses SQLite in-memory (conftest sets DATABASE_URL). System python3 (3.12) has pytest/requests/fastapi; there is NO venv on this machine and the Makefile calls 'python' (missing) — run 'python3 -m pytest' / 'python3 -m compileall' instead. Pre-existing unit failures unrelated to summarization: test_email_template.py, test_batch_submission.py, test_backfill_parallel.py (need live Postgres / API keys). Frontend tests run via 'node --experimental-strip-types --test tests/*.test.ts' (no DOM libs); .ts-extension import errors under tests/ in `tsc` are expected (node runs them, tsc build does not gate them). <!-- id:a4bf -->
- No-secret-leak is a tested invariant: tests/test_llm_service.py::test_nvidia_surfaced_error_never_leaks_key_or_endpoint asserts surfaced ProviderError.message never contains the api_key, 'Authorization', or the base-url host on any path (HTTP 429/500/401/404 + timeout/connection whose raw str(e) carries the host). The property holds because messages are built from HTTP status + parsed upstream body only; str(e) is surfaced on NO path (repr is logged, not surfaced). A future str(e) reintroduction on e.g. the timeout path would leak the endpoint (sk-local on the LiteLLM path analogously) and fail this test. <!-- id:f598 -->
- run_summarization's PDF step changed (feat/pdf-download-on-demand): it now uses core.pdf_utils.get_local_pdf_path (0-byte = missing) + download_pdf_strict instead of arxiv_service.download_pdf + os.listdir/startswith. On download failure it records summary_error code='pdf_download_failed' with the REAL reason (e.g. 'No space left on the PDF storage volume.') and the PdfDownloadError.retryable/http_status — not a generic string. _summary_failure_fields/_record_summary_failure are unchanged. See node pdf-download-storage for the helper + the on-demand POST /papers/{id}/pdf/download endpoint and GET detail pdf_available. <!-- id:4fa1 -->
