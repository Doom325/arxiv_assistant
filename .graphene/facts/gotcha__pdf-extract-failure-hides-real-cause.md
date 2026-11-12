---
category: gotcha
subject: pdf-extract-failure-hides-real-cause
---

The UI error "Summarization failed: Failed to extract text from PDF" is raised by SummarizationService.generate_summary when core.pdf_utils.extract_text_from_pdf returns "". That function swallows every exception and logs only `Error reading PDF <path>: <e>` on the backend host, so the real cause is only in `docker logs arxiv_assistant_backend` on Khadas. It fires before any provider call: it is NOT an NVIDIA/LLM API error, and the provider-error detail from PR #57 does not apply to it.

Incident 2026-11-04 (root cause): the 466G exFAT drive mounted at /app/data was 100% full. Downloads left 0-byte `<arxiv_id>.pdf` files (3,710 found; log line "Cannot read an empty file") and the old lookup treated a 0-byte file as present, so every retry failed. PR #59 fixed the code side: atomic temp+replace download with a %PDF- check, 0-byte treated as missing, distinct 507 disk-full error, and an on-demand POST /papers/{id}/pdf/download plus `pdf_available` on the paper detail response.

Ops actions taken that day on Khadas: deleted the 15,500 oldest PDFs by published_date (2018-06-29 .. 2023-01-30, DB rows kept, about 52 GB) and all 3,710 zero-byte PDFs; free space went 0 -> 53 GB. Papers whose PDF was deleted now show a Download PDF action instead of a failing Summarize. Watch disk use: the worker keeps downloading.

Diagnosis recipe: ssh khadas@192.168.1.49; `docker logs arxiv_assistant_backend | grep -E "Error reading PDF|Summarization failed"`; `docker exec arxiv_assistant_backend df -h /app/data`; `find /app/data -maxdepth 1 -name '*.pdf' -size 0 | wc -l`.
