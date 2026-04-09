# Download Lists and Patterns Implementation Plan

Provide a brief description of the problem, any background context, and what the change accomplishes.

Currently, users can bookmark papers into lists and view papers by pattern. However, there is no way to download all the local PDF files associated with a list or a pattern matching query in bulk. This change will add two new backend endpoints that package the associated local PDFs into a ZIP archive, and add corresponding "Download" buttons to the frontend React UI.

## Proposed Changes

---

### Backend API Endpoints

#### [MODIFY] [`library.py`](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/routers/library.py)
- **What**: Add a new `GET /library/lists/{list_name}/download` endpoint.
- **Details**:
  - Determine `user_id` (currently hardcoded to `USER_ID = 1`).
  - Fetch all `arxiv_id`s in the specified `list_name` from `UserLibrary`.
  - Use `get_local_pdf_path` from `core.pdf_utils` to check which PDFs are available locally in `settings.PDF_SAVE_DIR`.
  - To be memory-efficient and avoid loading massive ZIPs in RAM, write to a `tempfile.NamedTemporaryFile(suffix=".zip", delete=False)`.
  - Return a `fastapi.responses.FileResponse` pointing to the temporary zip archive.
  - Attach a `fastapi.BackgroundTasks` instance that deletes the temp file after shipping it.

#### [MODIFY] [`patterns.py`](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/routers/patterns.py)
- **What**: Add a new `GET /patterns/papers/download` endpoint.
- **Details**: 
  - Accept the same filter query parameters as `/patterns/papers` (`category`, `pattern`, `is_agentic`, `start_date`, `end_date`).
  - Query checking the `PatternExperimentResult` & `Paper` tables to fetch the matching `arxiv_id`s.
  - Implement a hard limit (e.g., 500 papers maximum) to prevent enormous zip files or server crashes.
  - Zip the local PDFs and serve them using `FileResponse` + `BackgroundTasks` cleanup, similar to library downloads.

---

### Frontend Integrations

#### [MODIFY] [`api.ts`](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/lib/api.ts)
- **What**: Since downloading files via a `fetch` requires holding the Blob in memory (which can crash the browser for large Zips), we will not add a standard JSON fetch method. Instead, we can provide helper functions that return the correct API URL for the resource (e.g. `getLibraryDownloadUrl(listName)`). These URLs will be redirected to via a hidden anchor tag `<a>` or `window.open` so the browser handles the download stream efficiently.

#### [MODIFY] [`bookmarks/page.tsx`](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/app/bookmarks/page.tsx)
- **What**: Add a "Download as ZIP" button.
- **Details**: 
  - Render the button adjacent to the existing list controls (e.g., near "Export to GDrive").
  - On click, navigate the browser to the backend URL to initiate the download stream.

#### [MODIFY] [`patterns/page.tsx`](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/app/patterns/page.tsx)
- **What**: Add a "Download PDFs" button to the Pattern explorer view.
- **Details**: 
  - Render next to the filtering controls (Category dropdown, etc.).
  - Clicking this button builds the query string and points the browser to `/api/patterns/papers/download?...`

## Open Questions

> [!WARNING]
> **1. Missing PDFs Policy:** If a paper doesn't have its PDF downloaded locally yet, should we attempt to download it synchronously (which could timeout for a large list)? Or silently skip/log it? I propose skipping missing PDFs and only including what is on disk, since synchronous arXiv downloads for 100 papers will fail on the 3-second rate limit.
> **2. Maximum Limit for Patterns:** Getting all papers for a broad category could yield 2,000+ PDFs (~4GB). I propose putting a 500 paper ceiling on the Pattern bulk download. Is this acceptable?

## Verification Plan

### Automated Tests
- N/A for frontend UI interacton.

### Manual Verification
- Create a test list, add 3-5 papers, click the UI download button, verify the resulting ZIP opens properly and contains the pdfs.
- Filter a specific pattern locally, click download, verify the ZIP contains the correct papers and respects limits.
