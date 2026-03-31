# Functional Requirements Catalog
Last updated: 2026-03-25
These requirements define WHAT the app must do. They say nothing about HOW.
The interface, layout, and interaction patterns for each can be fully redesigned.
The backend endpoints listed are non-negotiable — they define the data contract.

---

## Domain: Discovery

REQ-001 | DISCOVERY | The user can browse a paginated feed of AI research papers fetched from the local index, including all papers regardless of user action.
Backend: GET /api/papers/
UI-agnostic: true

REQ-002 | DISCOVERY | The user can filter the paper feed by arXiv category (e.g., cs.AI, cs.LG, cs.CL, cs.CV, cs.RO, cs.NE, cs.MA, cs.IR, cs.SI, cs.HC, cs.CY).
Backend: GET /api/papers/?category=<value>
UI-agnostic: true

REQ-003 | DISCOVERY | The user can filter the paper feed by publication date range (start date and/or end date).
Backend: GET /api/papers/?start_date=<value>&end_date=<value>
UI-agnostic: true

REQ-004 | DISCOVERY | The user can sort the paper feed by relevance, newest publication date, or title.
Backend: GET /api/papers/?sort_by=<value>
UI-agnostic: true

REQ-005 | DISCOVERY | The user can reset all active filters to view the unfiltered feed.
Backend: GET /api/papers/
UI-agnostic: true

REQ-006 | DISCOVERY | The user can manually trigger a feed refresh to surface newly indexed papers without reloading the page.
Backend: GET /api/papers/
UI-agnostic: true

REQ-007 | DISCOVERY | The user can view a summary statistics snapshot for the cs.AI category, including total paper count, papers published today, and papers published yesterday.
Backend: GET /api/analytics/summary-stats
UI-agnostic: true

REQ-008 | DISCOVERY | The user can view a time-series chart of papers added per day (over the past 14 days, scoped to cs.AI).
Backend: GET /api/analytics/papers-over-time
UI-agnostic: true

REQ-009 | DISCOVERY | The user can view a distribution breakdown of papers by sub-category (over the past 30 days, scoped to cs.AI).
Backend: GET /api/analytics/category-distribution
UI-agnostic: true

REQ-010 | DISCOVERY | The user can add a paper to the local index by providing an arXiv ID or URL.
Backend: POST /api/papers/add
UI-agnostic: true

REQ-011 | DISCOVERY | The user can view a quick preview of any paper (title, abstract, publication date, estimated reading time, AI summary if available) without leaving the current context.
Backend: GET /api/papers/{id}, POST /api/papers/{id}/summarize
UI-agnostic: true

REQ-012 | DISCOVERY | The user can trigger AI-powered paper discovery to surface new papers from the past 7 days that are relevant to their bookmarked library.
Backend: POST /api/queue/discover
UI-agnostic: true

REQ-013 | DISCOVERY | The user can view papers grouped by publication date for chronological orientation within any listing.
Backend: GET /api/papers/ (client-side grouping)
UI-agnostic: true

---

## Domain: Search

REQ-014 | SEARCH | The user can perform a semantic/keyword search across all indexed papers using free-text queries.
Backend: POST /api/papers/search
UI-agnostic: true

REQ-015 | SEARCH | The user can refine a search using structured operators: category (e.g., category:cs.AI), date cutoff (e.g., after:2024), and author (e.g., author:Vaswani).
Backend: POST /api/papers/search
UI-agnostic: true

REQ-016 | SEARCH | The user can sort search results by relevance, publication date, or title.
Backend: POST /api/papers/search?sort_by=<value>
UI-agnostic: true

REQ-017 | SEARCH | The user can search using a global command palette accessible from anywhere in the app, which searches papers in real time with debouncing.
Backend: POST /api/papers/search
UI-agnostic: true

REQ-018 | SEARCH | The user can navigate to any section of the app via the global command palette.
Backend: none
UI-agnostic: true

REQ-019 | SEARCH | The user can navigate to a specific paper's detail view directly from search results.
Backend: GET /api/papers/{id}
UI-agnostic: true

REQ-020 | SEARCH | The user can conduct a conversational query against the paper library, receiving a natural-language answer and a list of source papers that informed the response.
Backend: POST /api/papers/chat
UI-agnostic: true

---

## Domain: Library

REQ-021 | LIBRARY | The user can bookmark any paper into a personal library.
Backend: POST /api/library/{paper_id}
UI-agnostic: true

REQ-022 | LIBRARY | The user can remove a bookmark from the library.
Backend: DELETE /api/library/{paper_id}
UI-agnostic: true

REQ-023 | LIBRARY | The user can organize bookmarked papers into named lists.
Backend: POST /api/library/lists/{list_name}, POST /api/library/{paper_id}?list_name=<value>
UI-agnostic: true

REQ-024 | LIBRARY | The user can add a paper to an existing list or to a new list created on the fly, from any paper context.
Backend: POST /api/library/{paper_id}?list_name=<value>, POST /api/library/lists/{list_name}
UI-agnostic: true

REQ-025 | LIBRARY | The user can remove a paper from a specific named list without removing it from other lists.
Backend: DELETE /api/library/{paper_id}?list_name=<value>
UI-agnostic: true

REQ-026 | LIBRARY | The user can view all bookmarked papers across all lists, or filter to a single named list.
Backend: GET /api/library, GET /api/library?list_name=<value>
UI-agnostic: true

REQ-027 | LIBRARY | The user can sort their library by date added (ascending/descending), publication date (ascending/descending), or title (A–Z / Z–A).
Backend: GET /api/library (client-side sort)
UI-agnostic: true

REQ-028 | LIBRARY | The user can clear all papers from a specific named list.
Backend: DELETE /api/library/{paper_id} (iterated per paper in the list)
UI-agnostic: true

REQ-029 | LIBRARY | The user can export a named list of bookmarked papers to Google Drive.
Backend: POST /api/library/export/gdrive?list_name=<value>
UI-agnostic: true

REQ-030 | LIBRARY | The user can complete a Google OAuth PKCE flow to authorize Google Drive access without storing credentials server-side.
Backend: POST /api/library/export/gdrive/auth
UI-agnostic: true

REQ-031 | LIBRARY | The user can view the reading queue, which aggregates both AI-discovered papers and bookmarked papers pending review.
Backend: GET /api/queue
UI-agnostic: true

REQ-032 | LIBRARY | The user can filter the reading queue by source (discovered vs. bookmarked) and by read status (unread, reading, read, skipped).
Backend: GET /api/queue?status=<value>&source=<value>
UI-agnostic: true

REQ-033 | LIBRARY | The user can sort the reading queue by priority score, publication date, or date added (ascending or descending).
Backend: GET /api/queue (client-side sort)
UI-agnostic: true

REQ-034 | LIBRARY | The user can group queue items by publication day, week, or month.
Backend: GET /api/queue (client-side grouping)
UI-agnostic: true

REQ-035 | LIBRARY | The user can mark a queue item as unread, reading, read, or skipped.
Backend: POST /api/queue/{paper_id}/read, POST /api/queue/{paper_id}/reading, POST /api/queue/{paper_id}/skip
UI-agnostic: true

REQ-036 | LIBRARY | The user can manually override a queue item's priority (high, medium, low, or auto).
Backend: PATCH /api/queue/{paper_id}/priority
UI-agnostic: true

REQ-037 | LIBRARY | The user can remove a paper from the reading queue entirely.
Backend: DELETE /api/queue/{paper_id}
UI-agnostic: true

REQ-038 | LIBRARY | The user can rescore all queue items to recalculate their priority based on current interest signals.
Backend: POST /api/queue/rescore
UI-agnostic: true

REQ-039 | LIBRARY | The user can view queue statistics including counts of discovered, saved, high-priority, and completed papers, and estimated total reading time.
Backend: GET /api/queue/stats
UI-agnostic: true

REQ-040 | LIBRARY | The user can preview a queue item's abstract and AI summary without leaving the queue, and navigate to adjacent items in the same session.
Backend: GET /api/papers/{id}, POST /api/papers/{id}/summarize
UI-agnostic: true

---

## Domain: Analytics

REQ-041 | ANALYTICS | The user can view the top-cited papers within the local library, ranked by how many times they are referenced across all indexed papers.
Backend: GET /api/citations/top/
UI-agnostic: true

REQ-042 | ANALYTICS | The user can filter the top-citations list by arXiv category and by a publication date range.
Backend: GET /api/citations/top/?category=<value>&start_date=<value>&end_date=<value>
UI-agnostic: true

REQ-043 | ANALYTICS | For each top-cited paper, the user can see whether it exists in the local database and navigate to its detail page if it does, or open it on arXiv if it does not.
Backend: GET /api/citations/top/
UI-agnostic: true

REQ-044 | ANALYTICS | The user can browse a taxonomy of research patterns (e.g., agent memory, agent planning, multi-agent, inference, architecture) with paper counts per category and sub-pattern.
Backend: GET /api/patterns/overview
UI-agnostic: true

REQ-045 | ANALYTICS | The user can filter the pattern overview by agentic/non-agentic classification and by publication date range.
Backend: GET /api/patterns/overview?is_agentic=<value>&start_date=<value>&end_date=<value>
UI-agnostic: true

REQ-046 | ANALYTICS | The user can drill into a pattern category to see all sub-patterns and the papers classified under each.
Backend: GET /api/patterns/papers?category=<value>
UI-agnostic: true

REQ-047 | ANALYTICS | The user can drill into a specific sub-pattern to see all papers tagged with that pattern, including confidence scores and supporting evidence text.
Backend: GET /api/patterns/papers?category=<value>&pattern=<value>
UI-agnostic: true

REQ-048 | ANALYTICS | The user can view the chain-of-thought classification reasoning for any pattern-classified paper.
Backend: GET /api/patterns/papers (reasoning field)
UI-agnostic: true

REQ-049 | ANALYTICS | The user can view a paper's complete pattern classification (agentic flag, primary category, all detected patterns with confidence scores and evidence) within the paper's detail view.
Backend: GET /api/patterns/paper/{arxiv_id}
UI-agnostic: true

---

## Domain: Communication

REQ-050 | COMMUNICATION | The user can request an AI-generated summary (powered by Gemini) for any individual paper, triggered on demand.
Backend: POST /api/papers/{paper_id}/summarize
UI-agnostic: true

REQ-051 | COMMUNICATION | The user can regenerate an existing AI summary to get a fresh analysis.
Backend: POST /api/papers/{paper_id}/summarize?force=true
UI-agnostic: true

REQ-052 | COMMUNICATION | The user can email the AI-generated summary of any paper to the configured recipient email address.
Backend: POST /api/papers/{paper_id}/email
UI-agnostic: true

REQ-053 | COMMUNICATION | The user can conduct a multi-turn natural language conversation with the paper library, asking research questions and receiving answers grounded in indexed papers with source citations.
Backend: POST /api/papers/chat
UI-agnostic: true

REQ-054 | COMMUNICATION | The user can launch a chat session from pre-written example prompts covering common research question types.
Backend: POST /api/papers/chat
UI-agnostic: true

REQ-055 | COMMUNICATION | The user can navigate from a chat response source citation directly to the corresponding paper's detail view.
Backend: GET /api/papers/{id}
UI-agnostic: true

---

## Domain: Navigation

REQ-056 | NAVIGATION | The user can navigate between all major sections of the app (Dashboard, Research, Bookmarks, Analysis, Patterns, Deep Dive, Settings, Timeline) from a persistent navigation element.
Backend: none
UI-agnostic: true

REQ-057 | NAVIGATION | The user can open a global command palette to search papers and navigate to any section from anywhere in the app using a keyboard shortcut (Cmd/Ctrl+K).
Backend: POST /api/papers/search
UI-agnostic: true

REQ-058 | NAVIGATION | The user can navigate the paper list using keyboard shortcuts (j/k to move focus, Space to open quick peek, b to bookmark the focused paper).
Backend: none
UI-agnostic: true

REQ-059 | NAVIGATION | The user can navigate directly to any app section using two-key chord shortcuts (g then d/r/c/b/a/p/s).
Backend: none
UI-agnostic: true

REQ-060 | NAVIGATION | The user can view a reference overlay listing all available keyboard shortcuts.
Backend: none
UI-agnostic: true

REQ-061 | NAVIGATION | The user can navigate to a paper's full detail view from any listing (feed, search results, bookmarks, queue, pattern library, chat sources).
Backend: GET /api/papers/{id}
UI-agnostic: true

REQ-062 | NAVIGATION | The user can navigate from a paper's detail view to a citation-graph timeline centered on that paper.
Backend: GET /api/timeline/paper/{paper_id}
UI-agnostic: true

REQ-063 | NAVIGATION | The user can view similar papers recommended alongside any paper's detail view.
Backend: GET /api/papers/{id}/similar
UI-agnostic: true

REQ-064 | NAVIGATION | The user can open a paper's full PDF in a new tab from its detail view or quick-peek preview.
Backend: none (uses stored pdf_url)
UI-agnostic: true

REQ-065 | NAVIGATION | The user can view a citation-graph timeline for a topic or keyword, showing how research in that area has evolved over time.
Backend: GET /api/timeline/topic?q=<value>
UI-agnostic: true

REQ-066 | NAVIGATION | The user can restrict a topic timeline to papers that are present in the local library only.
Backend: GET /api/timeline/topic?q=<value>&library_only=true
UI-agnostic: true

REQ-067 | NAVIGATION | The user can select any node in a timeline graph to view that paper's key metadata (title, authors, citation count, seminal flag, library membership).
Backend: GET /api/timeline/topic or GET /api/timeline/paper/{id} (node data)
UI-agnostic: true

---

## Domain: Settings

REQ-068 | SETTINGS | The user can save a set of research interest keywords that are used to prioritize papers in their daily digest and queue scoring.
Backend: POST /api/users/config
UI-agnostic: true

REQ-069 | SETTINGS | The user can configure an email address for receiving paper summaries and notifications.
Backend: POST /api/users/config
UI-agnostic: true

REQ-070 | SETTINGS | The user can load their previously saved configuration by providing their email address.
Backend: GET /api/users/config/{email}
UI-agnostic: true

REQ-071 | SETTINGS | The user can set the notification frequency for email digests (daily, weekly, or real-time).
Backend: POST /api/users/config
UI-agnostic: true
