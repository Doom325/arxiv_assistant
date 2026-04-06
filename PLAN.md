# arxiv_assistant — Master Implementation Plan

This document contains all active feature implementation plans.

---

# Feature 1: Reading Queue with Priority Scoring

## Overview

Build an intelligent reading queue that automatically ranks unread bookmarked papers by relevance to the user's research interests, paper impact, and freshness.

## Dependency Graph

```
Phase 1: Core MVP
  P1.1 (DB Models) ──┬──→ P1.3 (Service) ──→ P1.4 (Router) ──→ P1.7 (Auto-Sync)
  P1.2 (Migration) ──┘        │                    │
                               │                    └──→ P1.5 (Scheduler)
                               │
                               └──→ P1.6 (API Client) ──→ P1.8 (Queue Page) ──→ P1.9 (E2E Test)

Phase 2: Enhanced Scoring (depends on P1.3, P1.4)
  P2.1 ──┐
  P2.2 ──┼──→ P2.5 (Scoring Breakdown Storage) ──→ P2.6 (Explanation API) ──→ P2.7 (FE Tooltip)
  P2.3 ──┤
  P2.4 ──┘

Phase 3: Dashboard Integration (depends on P1.8, P1.6)
  P3.1 (Up Next Tile) ──┐
  P3.2 (Sidebar Badge) ──┼──→ P3.5 (E2E Test)
  P3.3 (Velocity Stats) ─┤
  P3.4 (Analytics Page) ─┘

Phase 4: Smart Features (depends on Phase 2, Phase 3)
  P4.1 (Auto-detect Status)
  P4.2 (Stale Archiving)
  P4.3 (Post-Read Recs)
  P4.4 (Email Digest)
```

---

## Phase 1: Core MVP

**Goal:** Bookmarked papers appear in a prioritized queue with basic scoring (interest similarity + freshness). Users can mark papers as read/skipped.

---

### P1.1 — Define Database Models

**Depends on:** Nothing
**Files:** `backend/models/queue.py`, `backend/models/__init__.py`

#### P1.1.1 — Create ReadingQueue model
- Table: `reading_queue`
- Columns: `id`, `user_id` (FK users), `paper_id` (FK papers), `priority_score` (Float), `interest_similarity` (Float), `citation_impact` (Float), `freshness_score` (Float), `category_score` (Float), `entity_overlap` (Float), `peer_reads_score` (Float), `read_status` (String: unread/reading/read/skipped), `manual_priority` (Integer, nullable), `added_at`, `scored_at`, `read_at`
- Unique constraint on `(user_id, paper_id)`
- Index on `(user_id, read_status, priority_score DESC)` for efficient queue queries

#### P1.1.2 — Create UserInterestProfile model
- Table: `user_interest_profiles`
- Columns: `id`, `user_id` (FK users, unique), `interest_vector` (Vector(768)), `top_categories` (JSON), `top_entities` (JSON), `papers_used` (Integer), `computed_at` (DateTime)

#### P1.1.3 — Export new models from `__init__.py`
- Add `ReadingQueue`, `UserInterestProfile` to `backend/models/__init__.py`

---

### P1.2 — Create Database Migration

**Depends on:** P1.1
**Files:** `backend/migrate_reading_queue.py`

#### P1.2.1 — Write migration script
- Create `reading_queue` table
- Create `user_interest_profiles` table
- Add indexes: `(user_id, read_status)`, `(user_id, paper_id)` unique
- Idempotent: check if tables exist before creating

#### P1.2.2 — Run migration on local dev DB
- Test against local PostgreSQL
- Verify tables, columns, indexes created correctly

#### P1.2.3 — Run migration on Khadas production DB
- Execute via deploy script or SSH

---

### P1.3 — Implement Reading Queue Service

**Depends on:** P1.1
**Files:** `backend/services/reading_queue_service.py`

#### P1.3.1 — Implement `compute_user_interest_vector()`
- Query all papers the user has engaged with (has `generated_summary` OR exists in `UserLibrary`)
- Fetch their 768D embeddings from `Paper.embedding`
- Apply exponential time-decay weighting (half-life 30 days based on `published_date`)
- Average the weighted embeddings into a single 768D vector
- Handle cold start: return `None` if no engaged papers have embeddings

#### P1.3.2 — Implement `score_paper()` (MVP: 2 signals)
- **Interest similarity:** Cosine similarity between paper embedding and user interest vector (weight 0.35). Skip if no interest vector (cold start → score 0).
- **Freshness:** `exp(-0.03 * days_since_publication)` (weight 0.15)
- MVP total: `(0.35 * interest_similarity) + (0.15 * freshness_score)`, normalized to [0, 1]
- Return dict with individual scores + combined `priority_score`

#### P1.3.3 — Implement `sync_queue_from_library()`
- Query all `UserLibrary` entries for the user (with `paper_id IS NOT NULL`)
- Query all `ReadingQueue` entries for the user
- Add missing papers to queue with status "unread"
- Remove queue entries for papers no longer in library
- Return counts: `(added, removed)`

#### P1.3.4 — Implement `rescore_queue()`
- Call `compute_user_interest_vector()` to get/update the user's interest profile
- Cache the profile in `UserInterestProfile` table
- Query all unread/reading queue entries
- Call `score_paper()` for each
- Bulk update `priority_score`, `scored_at`, and individual signal scores
- Return count of papers rescored

#### P1.3.5 — Implement `get_queue()`
- Query `ReadingQueue` joined with `Paper` for the user
- Filter by `read_status` if provided
- Order by: manual_priority DESC NULLS LAST, then priority_score DESC
- Paginate with `limit`/`offset`
- Return list of queue items with paper metadata

#### P1.3.6 — Implement `mark_read()`, `mark_reading()`, `mark_skipped()`
- Update `read_status` on the queue entry
- For `mark_read`: also set `read_at = datetime.utcnow()`
- For `mark_skipped`: paper stays in queue but sorts to bottom

#### P1.3.7 — Implement `update_manual_priority()`
- Set `manual_priority` (1=low, 2=medium, 3=high, None=auto)
- Manual priority overrides auto score for sort ordering

#### P1.3.8 — Implement `remove_from_queue()`
- Delete the queue entry (paper stays in library)

---

### P1.4 — Create Queue API Router

**Depends on:** P1.3
**Files:** `backend/routers/queue.py`, `backend/main.py`

#### P1.4.1 — Create `routers/queue.py` with prefix `/queue`
- `GET /queue` — paginated queue with status filter, calls `get_queue()`
- `GET /queue/stats` — total unread, avg priority, estimated reading time
- `POST /queue/{paper_id}/read` — mark as read
- `POST /queue/{paper_id}/reading` — mark as reading
- `POST /queue/{paper_id}/skip` — mark as skipped
- `PATCH /queue/{paper_id}/priority` — set manual priority (body: `{"priority": 1|2|3|null}`)
- `POST /queue/rescore` — manually trigger rescoring
- `DELETE /queue/{paper_id}` — remove from queue

#### P1.4.2 — Register router in `main.py`
- `app.include_router(queue_router)`

#### P1.4.3 — Add Pydantic response schemas
- `QueueItemResponse`: paper metadata + priority_score + read_status + scoring breakdown + relevance_reason
- `QueueStatsResponse`: total_unread, total_reading, total_read, avg_priority, estimated_reading_hours

---

### P1.5 — Add Scheduler Job

**Depends on:** P1.3
**Files:** `backend/scheduler.py`

#### P1.5.1 — Add `rescore_reading_queues()` function
- Query all users
- For each: call `sync_queue_from_library()` then `rescore_queue()`
- Log results

#### P1.5.2 — Register job with APScheduler
- CronTrigger: daily at 2 AM IST (20:30 UTC)
- Add alongside existing paper_poll, email_digest, batch_summarization jobs

---

### P1.6 — Add API Client Methods (Frontend)

**Depends on:** P1.4
**Files:** `frontend/lib/api.ts`

#### P1.6.1 — Add queue API methods to `api` object
- `getQueue(status?, limit?, offset?)` → GET `/api/queue`
- `getQueueStats()` → GET `/api/queue/stats`
- `markRead(paperId)` → POST `/api/queue/{paperId}/read`
- `markReading(paperId)` → POST `/api/queue/{paperId}/reading`
- `markSkipped(paperId)` → POST `/api/queue/{paperId}/skip`
- `setManualPriority(paperId, priority)` → PATCH `/api/queue/{paperId}/priority`
- `rescoreQueue()` → POST `/api/queue/rescore`
- `removeFromQueue(paperId)` → DELETE `/api/queue/{paperId}`

---

### P1.7 — Hook Library Add/Remove to Queue Sync

**Depends on:** P1.3, P1.4
**Files:** `backend/routers/library.py`

#### P1.7.1 — On `POST /library/{paper_id}` (add bookmark)
- After successful bookmark, add paper to ReadingQueue with status "unread"
- Compute quick score (interest similarity + freshness only) inline
- If interest profile doesn't exist yet, skip scoring (will be scored on next scheduler run)

#### P1.7.2 — On `DELETE /library/{paper_id}` (remove bookmark)
- After successful removal, delete corresponding ReadingQueue entry if exists

---

### P1.8 — Build Queue Page (Frontend)

**Depends on:** P1.6
**Files:** `frontend/app/queue/page.tsx`, `frontend/components/QueueCard.tsx`

#### P1.8.1 — Create `QueueCard` component
- Priority badge: HIGH (score >= 0.7, orange), MEDIUM (0.4-0.7, yellow), LOW (<0.4, blue)
- Priority bar: visual fill width = score * 100%
- Paper title (clickable → opens peek sheet via existing QuickPeekSheet)
- Meta line: score, category, date, reading time estimate
- Quick actions: Mark Read (check), Skip (circle-slash), priority override buttons
- Category accent bar (reuse existing `getCategoryColor`)

#### P1.8.2 — Create `/queue` page
- Stats bar at top: unread count, estimated reading time, high-priority count
- Filter bar: status tabs (All/Unread/Reading/Read/Skipped), sort dropdown, category filter
- Queue list: render QueueCard for each item
- Pagination or infinite scroll (reuse pattern from DashboardContent)
- "Completed" section at bottom (collapsed by default, shows read papers)
- Empty state: "Bookmark some papers to build your reading queue"
- Rescore button in header

#### P1.8.3 — Add `/queue` route to Sidebar
- Add "Reading Queue" link with unread badge count
- Position after "Bookmarks" in sidebar nav

#### P1.8.4 — Wire QueueCard actions to API
- Mark Read → call `api.markRead(paperId)`, optimistic UI update
- Skip → call `api.markSkipped(paperId)`, move to bottom
- Priority override → call `api.setManualPriority(paperId, priority)`
- Click title → open QuickPeekSheet (reuse existing component)

---

### P1.9 — End-to-End Testing (Phase 1)

**Depends on:** P1.7, P1.8

#### P1.9.1 — Backend tests
- Test `compute_user_interest_vector()` with known embeddings
- Test `score_paper()` returns correct scores
- Test `sync_queue_from_library()` adds/removes correctly
- Test `rescore_queue()` updates scores
- Test all router endpoints (GET/POST/PATCH/DELETE)
- Test cold start behavior (no bookmarks)

#### P1.9.2 — Frontend smoke test
- TypeScript type check (`npx tsc --noEmit`)
- Dev server loads without errors
- `/queue` page renders with mock data
- QueueCard actions trigger correct API calls

#### P1.9.3 — Integration test
- Bookmark a paper → appears in queue
- Mark as read → moves to completed section
- Remove bookmark → disappears from queue
- Manual rescore → scores update

---

## Phase 2: Enhanced Scoring

**Goal:** Add citation impact, entity overlap, category alignment, and peer reads signals. Show scoring breakdown and relevance explanation to users.

**Depends on:** Phase 1 complete (P1.3, P1.4 specifically)

---

### P2.1 — Add Citation Impact Signal

**Depends on:** P1.3
**Files:** `backend/services/reading_queue_service.py`

#### P2.1.1 — Implement citation count scoring
- Query `CitationLink` table: count citations where `target_arxiv_id = paper.arxiv_id` OR `resolved_paper_id = paper.id`
- Normalize: `min(citation_count / max_citations_in_queue, 1.0)`
- Weight: 0.20

---

### P2.2 — Add Entity Overlap Signal

**Depends on:** P1.3
**Files:** `backend/services/reading_queue_service.py`

#### P2.2.1 — Build user entity set
- Collect all entities from user's engaged papers (`Paper.entities` JSON column)
- Flatten into a set of unique entity strings

#### P2.2.2 — Compute overlap score
- `|paper_entities ∩ user_entity_set| / max(|paper_entities|, 1)`
- Weight: 0.10

---

### P2.3 — Add Category Alignment Signal

**Depends on:** P1.3
**Files:** `backend/services/reading_queue_service.py`

#### P2.3.1 — Compute category distribution from library
- Count papers per category in user's library
- Normalize to [0, 1] (most common category = 1.0)
- Store in `UserInterestProfile.top_categories` JSON

#### P2.3.2 — Score paper by category match
- Look up paper's category in the distribution
- Weight: 0.10

---

### P2.4 — Add Peer Reads Signal

**Depends on:** P1.3
**Files:** `backend/services/reading_queue_service.py`

#### P2.4.1 — Count library papers that cite this paper
- Query `CitationLink` where `source_paper_id IN (user's library paper IDs)` AND `target_arxiv_id = paper.arxiv_id`
- Normalize: `min(peer_cite_count / 5, 1.0)` (cap at 5)
- Weight: 0.10

---

### P2.5 — Store Full Scoring Breakdown

**Depends on:** P2.1, P2.2, P2.3, P2.4
**Files:** `backend/services/reading_queue_service.py`

#### P2.5.1 — Update `score_paper()` to compute all 6 signals
- Combine: `(0.35 * interest) + (0.20 * citations) + (0.15 * freshness) + (0.10 * category) + (0.10 * entity) + (0.10 * peer_reads)`
- Store each individual score in ReadingQueue columns

#### P2.5.2 — Update `rescore_queue()` to persist breakdown
- Write all 6 signal values per queue entry on rescore

---

### P2.6 — Add Explanation API

**Depends on:** P2.5
**Files:** `backend/routers/queue.py`, `backend/services/reading_queue_service.py`

#### P2.6.1 — Implement `generate_explanation()`
- Identify the dominant scoring signal (highest individual score)
- Select template from map: interest → "Closely matches your reading on {entity}", citations → "Highly cited ({count} citations)", etc.
- Fill template with paper/profile context
- Return one-line string

#### P2.6.2 — Add `GET /queue/{paper_id}/explain` endpoint
- Return full scoring breakdown + generated explanation string

#### P2.6.3 — Include `relevance_reason` in `GET /queue` response
- Pre-compute explanation for each queue item on rescore
- Store in a new `explanation` column or compute on-the-fly

---

### P2.7 — Frontend: Score Breakdown & Explanation

**Depends on:** P2.6, P1.8
**Files:** `frontend/components/QueueCard.tsx`

#### P2.7.1 — Add relevance reason line to QueueCard
- Display one-line explanation below the score/meta line
- Italic, lighter text color

#### P2.7.2 — Add score breakdown tooltip
- On hover over priority badge or score, show tooltip with all 6 signal scores
- Bar chart or simple list: "Interest: 0.92, Citations: 0.65, Fresh: 0.81, ..."

---

## Phase 3: Dashboard Integration

**Goal:** Surface the queue in the dashboard and sidebar. Add reading velocity stats.

**Depends on:** P1.6, P1.8

---

### P3.1 — "Up Next" Dashboard Tile

**Depends on:** P1.6
**Files:** `frontend/components/dashboard/QueueTile.tsx`, `frontend/components/DashboardContent.tsx`

#### P3.1.1 — Create `QueueTile` component
- Fetch top 3 queue items via `api.getQueue("unread", 3)`
- Show paper title, score badge, category, date for each
- "View Queue →" link at bottom
- Empty state: "No papers in queue. Bookmark papers to get started."

#### P3.1.2 — Add QueueTile to dashboard bento grid
- Insert in `DashboardContent.tsx` alongside existing StatsTile, SparklineTile, CategoryHeatmap

---

### P3.2 — Sidebar Unread Badge

**Depends on:** P1.6
**Files:** `frontend/components/Sidebar.tsx`

#### P3.2.1 — Fetch queue stats on mount
- Call `api.getQueueStats()` in Sidebar component
- Display unread count as badge next to "Reading Queue" link
- Badge style: small indigo circle with white number

---

### P3.3 — Reading Velocity Stats

**Depends on:** P1.4
**Files:** `backend/routers/queue.py`, `frontend/components/QueueCard.tsx`

#### P3.3.1 — Add velocity calculation to `/queue/stats`
- Count papers marked as read in the last 7/14/28 days
- Compute papers/week (trailing 4 weeks)
- Return as part of `QueueStatsResponse`

#### P3.3.2 — Display velocity in queue page stats bar
- "Reading 3.5 papers/week" alongside unread count and estimated time

---

### P3.4 — Queue Insights in Analytics Page

**Depends on:** P3.3
**Files:** `frontend/app/analysis/page.tsx`

#### P3.4.1 — Add queue stats section to analytics page
- Papers read over time (line chart)
- Queue growth vs consumption (dual line)
- Top categories in queue vs read

---

### P3.5 — End-to-End Testing (Phase 3)

**Depends on:** P3.1, P3.2, P3.3, P3.4

#### P3.5.1 — Verify dashboard tile renders with queue data
#### P3.5.2 — Verify sidebar badge shows correct unread count
#### P3.5.3 — Verify analytics page shows queue insights

---

## Phase 4: Smart Features

**Goal:** Auto-detect reading status, suggest archiving stale papers, post-read recommendations, weekly digest integration.

**Depends on:** Phase 2, Phase 3

---

### P4.1 — Auto-Detect Reading Status

**Depends on:** P1.8
**Files:** `frontend/components/QuickPeekSheet.tsx`, `frontend/app/paper/[id]/page.tsx`

#### P4.1.1 — Track peek sheet open duration
- On QuickPeekSheet open, start a timer
- If open > 30 seconds with the same paper, call `api.markReading(paperId)`

#### P4.1.2 — Auto-mark reading on "Analyze with Gemini"
- When user triggers summarization from peek sheet, call `api.markReading(paperId)`

#### P4.1.3 — Suggest marking as read when summary completes
- After summary arrives (polling completes), show a toast: "Mark as read?" with action button

---

### P4.2 — Stale Paper Archiving Suggestions

**Depends on:** P1.4
**Files:** `backend/services/reading_queue_service.py`, `frontend/app/queue/page.tsx`

#### P4.2.1 — Identify stale papers (> 90 days unread in queue)
- Add to `/queue/stats` response: `stale_count` (papers in queue > 90 days)

#### P4.2.2 — Frontend stale paper banner
- If stale_count > 0, show banner at top of queue page: "X papers have been in your queue for 90+ days. Archive them?"
- "Archive" button → bulk mark as skipped

---

### P4.3 — Post-Read Recommendations

**Depends on:** P2.5, P1.3
**Files:** `backend/routers/queue.py`, `frontend/app/queue/page.tsx`

#### P4.3.1 — On mark-read, find similar unread papers
- After marking a paper as read, query the top 3 most similar unread papers in queue (by embedding cosine similarity)
- Return as `recommendations` in the mark-read response

#### P4.3.2 — Frontend: "Read next" suggestion
- After marking read, show a toast or inline card: "Based on what you just read: [Paper Title]" with "Read Next" button

---

### P4.4 — Weekly Reading Report in Email Digest

**Depends on:** P3.3
**Files:** `backend/scheduler.py`, `backend/services/email_service.py`

#### P4.4.1 — Add reading queue section to weekly digest
- Papers read this week (count + titles)
- Current queue size
- Top 3 recommended papers from queue
- Reading velocity trend

#### P4.4.2 — Create email template section
- HTML template for the reading queue digest section
- Integrate into existing email service

---

## Summary

| Phase | Tasks | Sub-tasks | New Files | Modified Files |
|-------|-------|-----------|-----------|----------------|
| **Phase 1: Core MVP** | 9 | 28 | 5 | 5 |
| **Phase 2: Enhanced Scoring** | 7 | 11 | 0 | 3 |
| **Phase 3: Dashboard Integration** | 5 | 8 | 2 | 3 |
| **Phase 4: Smart Features** | 4 | 9 | 0 | 5 |
| **Total** | **25** | **56** | **7** | **16** |

## Critical Path

```
P1.1 → P1.2 → P1.3 → P1.4 → P1.7 → P1.9 (backend complete)
                P1.3 → P1.6 → P1.8 → P1.9 (frontend complete)
                P1.3 → P1.5 (scheduler)
```

Phase 1 is the critical path. Phases 2-4 can be worked on incrementally after Phase 1 ships.

---
---

# Feature 2: Paper Timeline / Evolution View

## Overview

Build an interactive timeline visualization showing how research ideas evolve over time. Users search a topic and see a DAG of papers with citation links, branching for divergent approaches, seminal paper identification, and ghost nodes for unresolved citations.

**Reference:** [docs/paper_timeline.md](docs/paper_timeline.md) (detailed scratchpad)

## Design Decisions

| # | Decision |
|---|----------|
| 1 | **React Flow (`@xyflow/react`)** for visualization |
| 2 | **Default 2 hops** for paper-based timeline, expandable to 3 |
| 3 | **Global scope** by default with library toggle |
| 4 | **Background narrative generation** with caching |
| 5 | **Ghost nodes with "Import" action** for unresolved citations (cap 10) |
| 6 | **Hybrid branching**: citation edges (solid) + entity similarity edges (dashed, toggleable) |

## Commit Guidance

**Every task and sub-task MUST be committed individually** using conventional commits:

```
feat: TR-X.Y.Z — <short description>
```

If a sub-task is too small for its own commit, group it with the next sub-task under the parent task ID. **Never bundle across tasks.** Each task (`TR-X.Y`) gets at least one commit.

## Dependency Graph

```
Phase 1: Core Backend
  TR-1.1 (Citation Traversal) ──→ TR-1.2 (Timeline Service) ──→ TR-1.3 (Router) ──→ TR-1.4 (Register)

Phase 2: Core Frontend
  TR-2.1 (Install React Flow) ──→ TR-2.2 (API Client) ──→ TR-2.3 (Timeline Graph) ──→ TR-2.4 (Page) ──→ TR-2.5 (E2E)

Phase 3: Visual Polish
  TR-3.1 (Custom Nodes) ──→ TR-3.2 (Edges & Animations) ──→ TR-3.3 (Time Axis) ──→ TR-3.4 (Minimap & Controls) ──→ TR-3.5 (E2E)

Phase 4: Ghost Nodes & Library Toggle
  TR-4.1 (Ghost Node Backend) ──→ TR-4.2 (Ghost Node Frontend) ──→ TR-4.3 (Import Action)
  TR-4.4 (Library Toggle Backend) ──→ TR-4.5 (Library Toggle Frontend)

Phase 5: Entry Points & Navigation
  TR-5.1 (Sidebar Link) ──→ TR-5.2 (Paper Detail Button) ──→ TR-5.3 (Peek Sheet Button) ──→ TR-5.4 (Entity Timeline)

Phase 6: Intelligence
  TR-6.1 (Narrative Backend) ──→ TR-6.2 (Narrative Frontend) ──→ TR-6.3 (Branch Labels) ──→ TR-6.4 (Dashboard Tile)
```

---

## Phase 1: Core Backend

**Goal:** Build the backend service that constructs timeline data from the citation graph and semantic search.

---

### TR-1.1 — Citation Graph Traversal Queries

**Depends on:** Nothing
**Files:** `backend/services/timeline_service.py`
**Commit:** `feat: TR-1.1 — add citation graph traversal functions`

#### TR-1.1.1 — Forward citation query
`get_papers_citing(paper_id, arxiv_id, db)` — returns all papers citing a given paper.

#### TR-1.1.2 — Backward citation query
`get_papers_cited_by(paper_id, db)` — returns all locally-resolved papers cited by a given paper.

#### TR-1.1.3 — Subgraph extraction query
`get_citation_subgraph(paper_ids, db)` — returns all citation links where both source and target are in the given set.

#### TR-1.1.4 — BFS citation traversal
`bfs_citations(seed_id, db, max_hops=2, direction="both")` — traverses the citation graph outward from a seed paper up to `max_hops` levels. Returns `set[int]` of discovered paper IDs.

---

### TR-1.2 — Timeline Service

**Depends on:** TR-1.1
**Files:** `backend/services/timeline_service.py`
**Commit each sub-task separately.**

#### TR-1.2.1 — Define response dataclasses
Pydantic models: `TimelineNode`, `TimelineEdge`, `TimelineResponse`.
**Commit:** `feat: TR-1.2.1 — define timeline response schemas`

#### TR-1.2.2 — Implement `build_timeline_from_topic()`
Semantic search → top N papers → extract citation subgraph → filter to connected papers → identify seminal → detect branches → return `TimelineResponse`.
**Commit:** `feat: TR-1.2.2 — implement topic-based timeline construction`

#### TR-1.2.3 — Implement `build_timeline_from_paper()`
Seed paper → BFS 2 hops → filter by embedding similarity (cosine > 0.7) → build subgraph → return `TimelineResponse`.
**Commit:** `feat: TR-1.2.3 — implement paper-based timeline construction`

#### TR-1.2.4 — Implement seminal paper identification
Score by `0.5 * normalized_age_rank + 0.5 * normalized_citation_rank`. Mark top 3 as seminal.
**Commit:** `feat: TR-1.2.4 — implement seminal paper identification`

#### TR-1.2.5 — Implement branch detection
BFS from root papers. Fork when a node has ≥2 children with no edge between them. Assign `branch_id`.
**Commit:** `feat: TR-1.2.5 — implement branch detection via BFS`

#### TR-1.2.6 — Implement layout computation
X-axis: normalized `published_date`. Y-axis: branch lanes. Set `x_position` and `y_position` on each node.
**Commit:** `feat: TR-1.2.6 — implement timeline layout computation`

---

### TR-1.3 — Timeline API Router

**Depends on:** TR-1.2
**Files:** `backend/routers/timeline.py`
**Commit:** `feat: TR-1.3 — add timeline API router`

#### TR-1.3.1 — Create endpoints
- `GET /timeline/topic?q={query}&limit=50`
- `GET /timeline/paper/{paper_id}?hops=2`

#### TR-1.3.2 — Add Pydantic request/response validation

---

### TR-1.4 — Register Router & Test

**Depends on:** TR-1.3
**Files:** `backend/main.py`

#### TR-1.4.1 — Register timeline router in `main.py`
**Commit:** `feat: TR-1.4.1 — register timeline router in main.py`

#### TR-1.4.2 — Manual API test
Test both endpoints with real data. Verify response structure.
**Commit:** `test: TR-1.4.2 — verify timeline API endpoints`

---

## Phase 2: Core Frontend

**Goal:** Build the basic timeline page with React Flow visualization.

**Depends on:** Phase 1 complete

---

### TR-2.1 — Install React Flow

**Depends on:** Nothing
**Commit:** `chore: TR-2.1.1 — install @xyflow/react`

#### TR-2.1.1 — `npm install @xyflow/react` in frontend

---

### TR-2.2 — Add API Client Methods

**Depends on:** TR-1.3
**Files:** `frontend/lib/api.ts`
**Commit:** `feat: TR-2.2.1 — add timeline API client methods and TypeScript types`

#### TR-2.2.1 — Add `getTimelineByTopic()`, `getTimelineByPaper()`, TypeScript interfaces

---

### TR-2.3 — Timeline Graph Component

**Depends on:** TR-2.1
**Files:** `frontend/components/TimelineGraph.tsx`, `frontend/components/TimelineNode.tsx`
**Commit:** `feat: TR-2.3 — create TimelineGraph and TimelineNode components`

#### TR-2.3.1 — Create `TimelineGraph` (React Flow wrapper, node/edge conversion, click handler)
#### TR-2.3.2 — Create `TimelineNode` (basic node: title, date, category border)

---

### TR-2.4 — Timeline Page

**Depends on:** TR-2.2, TR-2.3
**Files:** `frontend/app/timeline/page.tsx`, `frontend/components/TimelineDetailPanel.tsx`

#### TR-2.4.1 — Create `TimelineDetailPanel` (selected paper detail, actions)
**Commit:** `feat: TR-2.4.1 — create TimelineDetailPanel component`

#### TR-2.4.2 — Create `/timeline` page (search bar, graph, detail panel, loading/empty states)
**Commit:** `feat: TR-2.4.2 — create /timeline page with search and graph`

---

### TR-2.5 — End-to-End Testing

**Depends on:** TR-2.4

#### TR-2.5.1 — TypeScript check (`npx tsc --noEmit`)
#### TR-2.5.2 — Smoke test (search, render, click, detail panel)
**Commit:** `test: TR-2.5 — verify timeline page end-to-end`

---

## Phase 3: Visual Polish

**Goal:** Production-quality visuals. Custom nodes, animated edges, time axis, minimap.

**Depends on:** Phase 2 complete

---

### TR-3.1 — Custom Node Rendering

**Files:** `frontend/components/TimelineNode.tsx`

#### TR-3.1.1 — Size nodes by citation count (seminal = large gold glow, high = medium, regular = small)
**Commit:** `feat: TR-3.1.1 — size timeline nodes by citation count`

#### TR-3.1.2 — Category-colored nodes (tint, border, badge)
**Commit:** `feat: TR-3.1.2 — category-color timeline nodes`

#### TR-3.1.3 — Library bookmark indicator
**Commit:** `feat: TR-3.1.3 — add library bookmark indicator to timeline nodes`

---

### TR-3.2 — Edge Styling & Animations

**Files:** `frontend/components/TimelineGraph.tsx`

#### TR-3.2.1 — Style edges (solid for cites, dashed for related, arrows, hover effects)
#### TR-3.2.2 — Animated dash flow on hover/selection
**Commit:** `feat: TR-3.2 — style and animate timeline edges`

---

### TR-3.3 — Time Axis

#### TR-3.3.1 — Horizontal time axis with year markers and vertical grid lines
**Commit:** `feat: TR-3.3.1 — add horizontal time axis with year markers`

---

### TR-3.4 — Minimap & Controls

#### TR-3.4.1 — React Flow `<MiniMap>` and `<Controls>`, `fitView` on load
#### TR-3.4.2 — Keyboard navigation (arrows to pan, +/- to zoom, Escape to deselect)
**Commit:** `feat: TR-3.4 — add minimap, zoom controls, and keyboard navigation`

---

### TR-3.5 — Visual Polish Testing

#### TR-3.5.1 — Test with 5, 20, 50 node clusters. Verify sizing, colors, responsiveness.
**Commit:** `test: TR-3.5 — verify timeline visual polish`

---

## Phase 4: Ghost Nodes & Library Toggle

**Goal:** Ghost nodes for unresolved citations with import action. Global/library scope toggle.

**Depends on:** Phase 2 complete

---

### TR-4.1 — Ghost Node Backend

**Depends on:** TR-1.2
**Files:** `backend/services/timeline_service.py`

#### TR-4.1.1 — Fetch top 10 most-cited unresolved citations for cluster papers
#### TR-4.1.2 — Add ghost nodes (`is_ghost=True`) to `TimelineResponse` with positions and edges
**Commit:** `feat: TR-4.1 — add ghost nodes for unresolved citations`

---

### TR-4.2 — Ghost Node Frontend

**Depends on:** TR-4.1, TR-3.1
**Files:** `frontend/components/TimelineNode.tsx`

#### TR-4.2.1 — Render ghost nodes (grayed-out, dashed border, 50% opacity, dotted edges)
**Commit:** `feat: TR-4.2.1 — render ghost nodes with grayed-out styling`

---

### TR-4.3 — Ghost Node Import Action

**Depends on:** TR-4.2

#### TR-4.3.1 — "Import Paper" button on ghost nodes → calls `api.addPaper(arxiv_id)` → toast + optimistic UI
**Commit:** `feat: TR-4.3.1 — add import action for ghost nodes`

---

### TR-4.4 — Library Toggle Backend

**Depends on:** TR-1.2

#### TR-4.4.1 — Add `library_only` query param to timeline endpoints (default false)
**Commit:** `feat: TR-4.4.1 — add library_only filter to timeline endpoints`

---

### TR-4.5 — Library Toggle Frontend

**Depends on:** TR-4.4

#### TR-4.5.1 — Toggle switch on timeline page: "All Papers" / "My Library", persist in localStorage
**Commit:** `feat: TR-4.5.1 — add global/library scope toggle to timeline page`

---

## Phase 5: Entry Points & Navigation

**Goal:** Make timeline accessible from sidebar, paper detail, peek sheet, and entity badges.

**Depends on:** Phase 2 complete

---

### TR-5.1 — Sidebar Navigation Link

#### TR-5.1.1 — Add "Timeline" link with `GitBranch` icon after "Analysis"
**Commit:** `feat: TR-5.1.1 — add timeline link to sidebar navigation`

---

### TR-5.2 — Paper Detail Page Entry Point

#### TR-5.2.1 — "Show Timeline" button → navigates to `/timeline?paper={id}`
**Commit:** `feat: TR-5.2.1 — add Show Timeline button to paper detail page`

---

### TR-5.3 — Peek Sheet Entry Point

#### TR-5.3.1 — "Timeline" button alongside "Full Details" and "PDF" in peek sheet
**Commit:** `feat: TR-5.3.1 — add Timeline button to QuickPeekSheet`

---

### TR-5.4 — Entity-Based Timeline

**Depends on:** TR-1.2

#### TR-5.4.1 — Implement `build_timeline_from_entity()` in service
#### TR-5.4.2 — Add `GET /timeline/entity?name={entity}` endpoint
#### TR-5.4.3 — Add `getTimelineByEntity()` to frontend API client
#### TR-5.4.4 — Clickable entity badges → navigate to `/timeline?entity={name}`
**Commit:** `feat: TR-5.4 — add entity-based timeline with clickable entity badges`

---

## Phase 6: Intelligence

**Goal:** LLM-generated narrative, auto-labeled branches, dashboard widget.

**Depends on:** Phase 3 complete

---

### TR-6.1 — Narrative Generation Backend

#### TR-6.1.1 — `_generate_narrative()` via Gemini (topic + seminal papers + branches → 2-3 sentence summary)
#### TR-6.1.2 — Cache narratives (key: query_hash + paper_ids_hash, TTL 7 days)
#### TR-6.1.3 — Background generation (return `narrative: null` initially, poll for result)
**Commit:** `feat: TR-6.1 — add Gemini narrative generation with caching`

---

### TR-6.2 — Narrative Frontend

#### TR-6.2.1 — Glassmorphism card above graph, skeleton while loading, fade-in on arrival, collapsible
**Commit:** `feat: TR-6.2.1 — render narrative panel above timeline`

---

### TR-6.3 — Branch Auto-Labeling

#### TR-6.3.1 — Label branches by dominant differentiating entity
#### TR-6.3.2 — Render branch labels as badges at start of each lane
**Commit:** `feat: TR-6.3 — auto-label timeline branches by dominant entity`

---

### TR-6.4 — Dashboard Timeline Tile

#### TR-6.4.1 — `TimelineTile` component (mini timeline of user's top entity, 5-8 nodes, CSS layout)
#### TR-6.4.2 — Add to dashboard bento grid
**Commit:** `feat: TR-6.4 — add Research Lineage tile to dashboard`

---

## Timeline Feature Summary

| Phase | Tasks | Sub-tasks | New Files | Modified Files |
|-------|-------|-----------|-----------|----------------|
| **Phase 1: Core Backend** | 4 | 14 | 2 | 1 |
| **Phase 2: Core Frontend** | 5 | 8 | 4 | 1 |
| **Phase 3: Visual Polish** | 5 | 8 | 0 | 2 |
| **Phase 4: Ghost Nodes & Library Toggle** | 5 | 5 | 0 | 4 |
| **Phase 5: Entry Points** | 4 | 7 | 0 | 4 |
| **Phase 6: Intelligence** | 4 | 8 | 1 | 3 |
| **Total** | **27** | **50** | **7** | **15** |

## Critical Path

```
TR-1.1 → TR-1.2 → TR-1.3 → TR-1.4 (backend complete)
                                ↓
TR-2.1 → TR-2.2 → TR-2.3 → TR-2.4 → TR-2.5 (frontend MVP)
                                ↓
TR-3.1 → TR-3.2 → TR-3.3 → TR-3.4 → TR-3.5 (visual polish)
```

Phases 4 and 5 can run in parallel after Phase 2. Phase 6 starts after Phase 3.

---
---

# Feature 3: Query Embedding Cache

> **Design doc:** `docs/query_embedding_cache_proposal.md`
> **Detailed plan:** `docs/query_embedding_cache_plan.md`
> **Approach:** Hybrid — In-Memory LRU + PostgreSQL

## Overview

Every search, chat, and timeline request generates a fresh embedding via a synchronous Gemini API call (~100-500ms). There is zero caching — identical queries trigger duplicate API calls. This feature adds a two-tier cache: an in-memory LRU for hot queries (sub-microsecond hits) backed by a PostgreSQL table for warm queries (survives restarts, provides analytics).

## Dependency Graph

```
Phase 0: Bug Fix (standalone)
  P0.1 (Fix chat task_type) ──→ Phase 1

Phase 1: Data Layer
  P1.1 (ORM Model) ──┬──→ P1.3 (Migration) ──→ Phase 2
  P1.2 (Config)    ──┘

Phase 2: Cache Service
  P2.1 (Cache Class) ──→ P2.2 (Validation) ──→ P2.3 (Logging) ──→ Phase 3

Phase 3: Integration (depends on Phase 2)
  P3.1 (Search) ──┐
  P3.2 (Chat)   ──┼──→ Phase 4
  P3.3 (Timeline)─┘

Phase 4: Maintenance (depends on Phase 3)
  P4.1 (Scheduler Cleanup) ──┐
  P4.2 (Model Invalidation) ─┴──→ Phase 5

Phase 5: Testing (depends on all)
  P5.1 (Unit Tests) ──→ P5.2 (Integration Tests) ──→ P5.3 (Production Verification)
```

## Phase 0: Fix Chat task_type Bug

### P0.1 — Fix chat endpoint task_type
- **File:** `backend/routers/search.py`
- Change `llm_service.generate_embedding(query)` → `llm_service.generate_embedding(query, task_type="retrieval_query")`
- Deployed as a **separate commit** before caching work — behavior change should be validated independently

## Phase 1: Data Layer

### P1.1 — QueryEmbedding ORM model
- **File:** `backend/models/query_cache.py` (new)
- Fields: `query_hash` (SHA256, unique), `query_text` (truncated 1000 chars), `task_type`, `embedding` (Vector(768)), `model_name` (from `llm_service.embedding_model`), `hit_count`, `created_at`, `last_used_at`
- **File:** `backend/models/__init__.py` — add export

### P1.2 — Config setting
- **File:** `backend/config.py`
- Add `QUERY_CACHE_LRU_SIZE: int = 1024`

### P1.3 — Migration script
- **File:** `backend/migrate_query_cache.py` (new)
- `CREATE TABLE IF NOT EXISTS query_embeddings` — idempotent
- Run against local and production DB

## Phase 2: Cache Service

### P2.1 — QueryEmbeddingCache class
- **File:** `backend/services/query_embedding_cache.py` (new)
- `_lru: OrderedDict` (max from config), `_lock: threading.Lock`
- `_normalize()` — lowercase, strip, collapse spaces, truncate 1000 chars
- `_cache_key()` — SHA256 of `normalized|task_type|model_name`
- Singleton: `query_cache = QueryEmbeddingCache()`

### P2.2 — Validation & safety
- `_validate(embedding)` — returns True only if `list` with `len == 768`
- Never cache empty/malformed embeddings (Gemini returns `[]` on failure)
- `INSERT ON CONFLICT DO NOTHING` for PostgreSQL writes (handles concurrent races)
- `threading.Lock` on all LRU dict operations

### P2.3 — Logging & observability
- Structured log on every interaction: `event=hit|miss|error|skip_invalid`, `source=lru|postgres|gemini`, `latency_ms`

### Lookup flow:
```
1. Normalize + truncate query
2. Compute cache key (SHA256)
3. LRU check (under lock) → hit? return (no DB write)
4. PostgreSQL check by query_hash → hit? update last_used_at (only if >24h stale), populate LRU, return
5. Gemini API call → validate embedding (must be 768D, non-empty)
6. Write to PostgreSQL (INSERT ON CONFLICT DO NOTHING)
7. Write to LRU (under lock)
8. Return embedding
```

## Phase 3: Integration

### P3.1 — Search endpoint
- **File:** `backend/routers/search.py` line ~83
- Replace `llm_service.generate_embedding(...)` → `query_cache.get_or_generate(..., db=db)`

### P3.2 — Chat endpoint
- **File:** `backend/routers/search.py` line ~191
- Replace `llm_service.generate_embedding(...)` → `query_cache.get_or_generate(..., db=db)`

### P3.3 — Timeline topic search
- **File:** `backend/services/timeline_service.py` line ~594
- Replace `llm_service.generate_embedding(...)` → `query_cache.get_or_generate(..., db=db)`

## Phase 4: Maintenance

### P4.1 — Scheduled cleanup
- **File:** `backend/scheduler.py`
- Weekly job (Sunday 3 AM IST): delete entries with `last_used_at > 30 days`

### P4.2 — Model migration helper
- **File:** `backend/services/query_embedding_cache.py`
- `invalidate_model(old_model, db)` — deletes stale model entries + flushes LRU

## Phase 5: Testing

### P5.1 — Unit tests
- **File:** `backend/tests/test_query_cache.py` (new)
- Normalization, truncation, cache key determinism, LRU eviction, thread safety, validation, negative caching prevention

### P5.2 — Integration tests
- Full cache hit/miss flow against local DB
- Verify LRU → PostgreSQL → Gemini fallback chain
- Verify normalization produces cache hits for case variants

### P5.3 — Production verification
- SQL queries to check cache population, hit rates, popular queries

## File Summary

| File | Action | Phase |
|------|--------|-------|
| `backend/routers/search.py` | Fix chat task_type bug | 0 |
| `backend/models/query_cache.py` | New — ORM model | 1 |
| `backend/models/__init__.py` | Add export | 1 |
| `backend/config.py` | Add LRU size setting | 1 |
| `backend/migrate_query_cache.py` | New — migration script | 1 |
| `backend/services/query_embedding_cache.py` | New — cache service | 2 |
| `backend/routers/search.py` | Use cache in search + chat | 3 |
| `backend/services/timeline_service.py` | Use cache in timeline | 3 |
| `backend/scheduler.py` | Add weekly cleanup job | 4 |
| `backend/tests/test_query_cache.py` | New — tests | 5 |

**New files:** 4 | **Modified files:** 5 | **Estimated lines:** ~200 new, ~15 modified

## Design Invariants

1. **Query embeddings are corpus-independent.** New paper ingestion does NOT invalidate the cache. Only model changes or task_type changes require invalidation.
2. **Never cache invalid embeddings.** `generate_embedding()` returns `[]` on failure — this must NOT be cached.
3. **LRU is per-process.** PostgreSQL is the shared durable layer.

---
---

# Master Summary

| Feature | Tasks | Sub-tasks | New Files | Modified Files |
|---------|-------|-----------|-----------|----------------|
| **Reading Queue** | 25 | 56 | 7 | 16 |
| **Paper Timeline** | 27 | 50 | 7 | 15 |
| **Query Embedding Cache** | 12 | 20 | 4 | 5 |
| **Grand Total** | **64** | **126** | **18** | **36** |

---
---

# Feature 4: Parallel Pattern Backfill Optimization

## Overview
Scale the ArXiv pattern classification pipeline by implementing a robust, multithreaded backfill process. Optimizes Ollama for parallel inference (`OLLAMA_NUM_PARALLEL=4`, `q8_0` KV cache), uses a hash-partitioned `backfill_parallel.py` script for fault-tolerant execution, and tracks performance with mitmproxy/Prometheus/Grafana.

## Dependencies

```
Phase 0: Observability ──→ Phase 1: Environment Tuning ──→ Phase 2: Backfill Script ──→ Phase 3: Unit Tests ──→ Phase 4: Production Run
```

## Phase 0: Observability Stack (PR 1)
| ID | Task | Status |
|---|---|---|
| T0.1 | Create `ollama_metrics_addon.py` | DONE |
| T0.2 | Create `prometheus.yml` | DONE |
| T0.3 | Create Grafana datasource | DONE |
| T0.4 | Update `docker-compose.framework.yml` | DONE |
| T0.5 | Start monitoring stack | PENDING |
| T0.6 | PR 1: Submit `feat/mitmproxy-metrics-addon` | DONE |

## Phase 1: Environment & Host Configuration (PR 2)
| ID | Task | Status |
|---|---|---|
| T1.1 | Update Ollama `override.conf` | PENDING |
| T1.2 | Diagnostics: single baseline | DONE |
| T1.3 | Diagnostics: parallel stress | DONE |
| T1.4 | Verify mitmproxy under load | PENDING |
| T1.5 | PR 2: Submit `config/ollama-parallel` | DONE |

## Phase 2: Backend Script Implementation (PR 3)
| ID | Task | Status |
|---|---|---|
| T2.1 | `backfill_parallel.py` boilerplate | DONE |
| T2.2 | Deterministic partitioning (MD5 map) | DONE |
| T2.3 | Direct HTTP POST | DONE |
| T2.4 | DB Micro-commits & tagging | DONE |
| T2.5 | Queue-based JSONL observer | DONE |
| T2.6 | Progress metrics | DONE |
| T2.7 | PR 3: Submit `feat/backfill-parallel-script` | PENDING |

## Phase 3: Testing & Verification (PR 4)
| ID | Task | Status |
|---|---|---|
| T3.1 | Test partition distribution | DONE |
| T3.2 | Test concurrent sessions | DONE |
| T3.3 | Test worker recovery/resume | DONE |
| T3.4 | PR 4: Submit `test/backfill-parallel` | DONE |

## Phase 4: Production Backfill
| ID | Task | Status |
|---|---|---|
| T4.1 | Execute Dry-run | PENDING |
| T4.2 | Monitor memory spike | PENDING |
| T4.3 | Execute real batch (`--category cs.AI`) | PENDING |
