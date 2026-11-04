---
type: subsystem
summary: PDF download + local-storage layer. ONE real download impl: core/pdf_utils.download_pdf_strict (atomic temp+os.replace, %PDF-validated, arXiv-polite, raises structured PdfDownloadError); download_pdf is a lenient str|None wrapper over it for workers/scripts. get_local_pdf_path treats 0-byte as missing. ArxivService.download_pdf, routers/integrations._download_pdf_for_export, and run_summarization all route through it. API: GET /papers/{id} exposes pdf_available; POST /papers/{id}/pdf/download fetches one PDF on demand with structured errors.
entry_points:
  - download_pdf_strict
  - download_pdf
  - get_local_pdf_path
  - PdfDownloadError
  - ArxivService.download_pdf
  - _download_pdf_for_export
  - run_summarization
  - download_paper_pdf
  - _resolve_paper
covers:
  - backend/core/pdf_utils.py
  - backend/services/arxiv_service.py
  - backend/routers/integrations.py
  - backend/routers/papers.py
  - backend/production_worker.py
  - backend/mac_worker.py
last_commit: 80b54b6
edges:
  - to: summarization-errors type: related_to reason: run_summarization downloads missing PDFs via the pdf-download-storage helper and records pdf_download_failed with the real reason
---

- AS-FOUND (pre feat/pdf-download-on-demand): THREE divergent download impls, none atomic/validated. (1) core/pdf_utils.download_pdf(url,arxiv_id,pdf_dir,timeout=60)->str|None writes response.content straight to final path, no %PDF validation, no UA/delay, returns None on failure. (2) services/arxiv_service.ArxivService.download_pdf(pdf_url,save_path) sleeps 3s + UA, writes direct, raises. (3) routers/integrations._download_pdf_for_export(url,arxiv_id)->str|None returns an existing path even if 0 bytes, writes direct. A partial/empty write leaves a file later reads treat as present. <!-- id:7ff9 -->
- INCIDENT (2026-11): PDF_SAVE_DIR (466G exFAT on Khadas) hit 100% full; downloads left ~3710 zero-byte <id>.pdf files. get_local_pdf_path used os.path.exists so 0-byte counted present; run_summarization found files by os.listdir+startswith(arxiv_id) (loose prefix, also treats 0-byte present); extract_text_from_pdf swallows all exceptions -> '' so UI only saw generic 'Failed to extract text from PDF'. Operator deleted zero-byte files + ~15.5k oldest PDFs (DB rows intact), so many papers now have NO local PDF. <!-- id:9a6b -->
- CALL-SITE MAP for core download_pdf's str|None contract (must not break): production_worker._download_step + mac_worker call via thin wrappers and check `if pdf_path:`; bulk_ingest.py/catchup_pdfs.py call a 2-arg worker wrapper; scripts/backfill_nemotron.py calls core 3-arg; routers/papers full-text wraps in try/except (raises->503). get_local_pdf_path callers all want a valid PDF. Changing download_pdf to RAISE would ripple widely -> keep download_pdf str|None, add a raising variant for new structured-error callers. <!-- id:de15 -->
- No auth on any router (hardcoded USER_ID=1; main.py only adds CORS allow_origins=['*']). `make lint` is just compileall/py_compile (NOT ruff, despite AGENTS.md). Backend tests: SQLite in-memory via conftest; `client` fixture overrides get_db to yield the same `db_session`, so tests insert via db_session and read via client. AGENTS.md rule 79 'never process PDFs synchronously in API handlers' is in tension with the on-demand single-download endpoint (pre-existing full-text endpoint already downloads+extracts synchronously) -> note in PR body. <!-- id:fb0b -->
- IMPLEMENTED (feat/pdf-download-on-demand): core/pdf_utils now has ONE real impl, download_pdf_strict(url,arxiv_id,pdf_dir,timeout=60,*,delay_seconds=3.0)->str: arXiv politeness delay + identifying UA, refuses empty/non-%PDF bodies, writes via tempfile.mkstemp + os.replace (atomic; temp removed on any failure -> never a 0-byte/partial final file). Raises PdfDownloadError(code,message,retryable,http_status) — disk-full (ENOSPC)=code pdf_disk_full retryable False; 429/5xx/timeout/conn = retryable True. download_pdf(...)->str|None is now a lenient wrapper over strict (broad-catch -> None) so workers/scripts/bulk_ingest/catchup are unchanged yet gain atomicity+validation. <!-- id:f6b2 -->
- IMPLEMENTED call-site unification + API: get_local_pdf_path now treats a 0-byte file as missing (_is_nonempty_file). ArxivService.download_pdf and routers/integrations._download_pdf_for_export both delegate to download_pdf_strict. run_summarization uses get_local_pdf_path + download_pdf_strict and records summary_error code='pdf_download_failed' with the REAL reason (e.g. disk full) + retryable. NEW: GET /papers/{id} detail adds pdf_available:bool (one stat; list endpoints leave it null via PaperResponse default). NEW idempotent POST /papers/{id_or_arxiv}/pdf/download (no auth, matches router) -> 200 available|downloaded, or HTTPException 507 (disk_full) / 502 (upstream) with detail {code,message,retryable,http_status?}. arxiv_id comes from the DB row, never the raw path. _resolve_paper() shared id/arxiv lookup in papers.py. <!-- id:a96e -->
