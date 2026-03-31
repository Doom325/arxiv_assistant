# Functional Requirements — Reading Queue (/queue)

Coverage checklist for post-stitch review.
Source: docs/FUNCTIONAL_REQUIREMENTS.md — filtered to REQs served by this page.

---

## Queue Core

REQ-031 | LIBRARY
The user can view the reading queue, which aggregates both AI-discovered papers and bookmarked papers pending review.
Backend: GET /api/queue

REQ-032 | LIBRARY
The user can filter the reading queue by source (discovered vs. bookmarked) and by read status (unread, reading, read, skipped).
Backend: GET /api/queue?status=<value>&source=<value>

REQ-033 | LIBRARY
The user can sort the reading queue by priority score, publication date, or date added (ascending or descending).
Backend: GET /api/queue (client-side sort)

REQ-034 | LIBRARY
The user can group queue items by publication day, week, or month.
Backend: GET /api/queue (client-side grouping)

REQ-035 | LIBRARY
The user can mark a queue item as unread, reading, read, or skipped.
Backend: POST /api/queue/{paper_id}/read, POST /api/queue/{paper_id}/reading, POST /api/queue/{paper_id}/skip

REQ-036 | LIBRARY
The user can manually override a queue item's priority (high, medium, low, or auto).
Backend: PATCH /api/queue/{paper_id}/priority

REQ-037 | LIBRARY
The user can remove a paper from the reading queue entirely.
Backend: DELETE /api/queue/{paper_id}

REQ-038 | LIBRARY
The user can rescore all queue items to recalculate their priority based on current interest signals.
Backend: POST /api/queue/rescore

REQ-039 | LIBRARY
The user can view queue statistics including counts of discovered, saved, high-priority, and completed papers, and estimated total reading time.
Backend: GET /api/queue/stats

REQ-040 | LIBRARY
The user can preview a queue item's abstract and AI summary without leaving the queue, and navigate to adjacent items in the same session.
Backend: GET /api/papers/{id}, POST /api/papers/{id}/summarize

---

## Discovery (triggered from this page)

REQ-012 | DISCOVERY
The user can trigger AI-powered paper discovery to surface new papers from the past 7 days that are relevant to their bookmarked library.
Backend: POST /api/queue/discover

---

## Navigation (active on this page)

REQ-056 | NAVIGATION
The user can navigate between all major sections of the app from a persistent navigation element.
Backend: none

REQ-057 | NAVIGATION
The user can open a global command palette to search papers and navigate to any section from anywhere in the app using a keyboard shortcut (Cmd/Ctrl+K).
Backend: POST /api/papers/search

REQ-058 | NAVIGATION
The user can navigate the paper list using keyboard shortcuts (j/k to move focus, Space to open quick peek, b to bookmark the focused paper).
Backend: none

REQ-059 | NAVIGATION
The user can navigate directly to any app section using two-key chord shortcuts (g then d/r/c/b/a/p/s).
Backend: none

REQ-060 | NAVIGATION
The user can view a reference overlay listing all available keyboard shortcuts.
Backend: none

REQ-061 | NAVIGATION
The user can navigate to a paper's full detail view from any listing.
Backend: GET /api/papers/{id}

REQ-064 | NAVIGATION
The user can open a paper's full PDF in a new tab from its detail view or quick-peek preview.
Backend: none (uses stored pdf_url)

---

## Total applicable REQs: 17
REQ-012, REQ-031, REQ-032, REQ-033, REQ-034, REQ-035, REQ-036, REQ-037, REQ-038, REQ-039, REQ-040, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-064
