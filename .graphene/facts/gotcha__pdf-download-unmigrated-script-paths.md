---
category: gotcha
subject: pdf-download-unmigrated-script-paths
---

PDF download is NOT funneled through core.pdf_utils everywhere. After PR #59 (feat/pdf-download-on-demand, approved at befaaf7) the PRODUCTION paths are atomic/validated via core.pdf_utils.download_pdf_strict (+ lenient download_pdf wrapper): both workers, ArxivService.download_pdf, routers/integrations._download_pdf_for_export, run_summarization, the papers full-text + on-demand endpoints, and scripts/backfill_nemotron.py. download_pdf_strict writes via tempfile.mkstemp + os.replace with makedirs+mkstemp INSIDE the try, so even a dir/temp-creation ENOSPC maps to PdfDownloadError(pdf_disk_full)->507.

STILL UNMIGRATED (own non-core downloaders, non-atomic + 0-byte-blind os.path.exists; none import core.pdf_utils) — tracked in issue #60:
- backend/catchup_pdfs.py: own download_pdf L26 (response.content -> final path L40, non-atomic), os.path.exists L30. The incident recovery tool; its exists-check SKIPS existing zero-byte stubs (treats them present) so running it will NOT repair the ~3710 disk-full stubs and can recreate them on a tight drive.
- backend/batch_embed_manager.py: own download_pdf L166 (response.content write L180), os.path.exists L169 (has a <10000-byte extraction guard, not at download). Live background process per CLAUDE.md.
- backend/bulk_ingest.py: own download_pdf L60 (stream + iter_content write), os.path.exists L151.
The graphene node pdf-download-storage.md (obs aa10) documents this MIGRATED/UNMIGRATED split accurately as of befaaf7.
