# Paper Timeline / Evolution View — Implementation Plan

**Reference:** [paper_timeline.md](paper_timeline.md) (scratchpad with full design details)

## Dependency Graph

```
Phase 1: Core Backend
  TR-1.1 (Citation Traversal) ──→ TR-1.2 (Timeline Service) ──→ TR-1.3 (Router) ──→ TR-1.4 (Register)
                                       │
Phase 2: Core Frontend                │
  TR-2.1 (Install React Flow) ──→ TR-2.2 (API Client) ──→ TR-2.3 (Timeline Graph) ──→ TR-2.4 (Page) ──→ TR-2.5 (E2E)
                                                              │
Phase 3: Visual Polish                                        │
  TR-3.1 (Custom Nodes) ──→ TR-3.2 (Edges & Animations) ──→ TR-3.3 (Time Axis) ──→ TR-3.4 (Minimap & Controls) ──→ TR-3.5 (E2E)
                                                              │
Phase 4: Ghost Nodes & Library Toggle                         │
  TR-4.1 (Ghost Node Backend) ──→ TR-4.2 (Ghost Node Frontend) ──→ TR-4.3 (Import Action)
  TR-4.4 (Library Toggle Backend) ──→ TR-4.5 (Library Toggle Frontend)

Phase 5: Entry Points & Navigation
  TR-5.1 (Sidebar Link) ──→ TR-5.2 (Paper Detail Button) ──→ TR-5.3 (Peek Sheet Button) ──→ TR-5.4 (Entity Timeline)

Phase 6: Intelligence
  TR-6.1 (Narrative Backend) ──→ TR-6.2 (Narrative Frontend) ──→ TR-6.3 (Branch Labels) ──→ TR-6.4 (Dashboard Tile)
```

## Commit Guidance

**Every task and sub-task MUST be committed individually** using conventional commits:

```
feat: TR-X.Y.Z — <short description>
```

Examples:
- `feat: TR-1.1.1 — add forward/backward citation traversal queries`
- `feat: TR-2.3.1 — create TimelineGraph component with React Flow`

If a sub-task is too small for its own commit, group it with the next sub-task under the parent task ID:
- `feat: TR-1.1 — add citation graph traversal queries (forward, backward, subgraph)`

**Never bundle across tasks.** Each task (`TR-X.Y`) gets at least one commit.

---

## Phase 1: Core Backend

**Goal:** Build the backend service that constructs timeline data from the citation graph and semantic search. No frontend yet — API endpoints only.

---

### TR-1.1 — Citation Graph Traversal Queries

**Depends on:** Nothing
**Files:** `backend/services/timeline_service.py`
**Commit after completing all sub-tasks:** `feat: TR-1.1 — add citation graph traversal functions`

#### TR-1.1.1 — Forward citation query
Write a function `get_papers_citing(paper_id, arxiv_id, db)` that returns all papers in the database that cite a given paper.
```sql
SELECT p.* FROM citation_links cl
JOIN papers p ON p.id = cl.source_paper_id
WHERE cl.resolved_paper_id = :paper_id OR cl.target_arxiv_id = :arxiv_id
ORDER BY p.published_date
```
Return list of Paper objects.

#### TR-1.1.2 — Backward citation query
Write a function `get_papers_cited_by(paper_id, db)` that returns all locally-resolved papers cited by a given paper.
```sql
SELECT p.* FROM citation_links cl
JOIN papers p ON p.id = cl.resolved_paper_id
WHERE cl.source_paper_id = :paper_id AND cl.resolved_paper_id IS NOT NULL
ORDER BY p.published_date
```

#### TR-1.1.3 — Subgraph extraction query
Write a function `get_citation_subgraph(paper_ids, db)` that returns all citation links where both source and target are in the given set.
```sql
SELECT cl.source_paper_id, cl.resolved_paper_id
FROM citation_links cl
WHERE cl.source_paper_id IN :paper_ids
  AND cl.resolved_paper_id IN :paper_ids
  AND cl.resolved_paper_id IS NOT NULL
```
Return list of `(source_id, target_id)` tuples.

#### TR-1.1.4 — BFS citation traversal
Write a function `bfs_citations(seed_id, db, max_hops=2, direction="both")` that traverses the citation graph outward from a seed paper up to `max_hops` levels.
- Track visited set to avoid cycles
- Return `set[int]` of all discovered paper IDs
- Direction: "forward" (papers citing seed), "backward" (papers cited by seed), "both"

**Commit:** `feat: TR-1.1 — add citation graph traversal functions`

---

### TR-1.2 — Timeline Service

**Depends on:** TR-1.1
**Files:** `backend/services/timeline_service.py`
**Commit each sub-task separately — they are substantial.**

#### TR-1.2.1 — Define response dataclasses
Create Pydantic models:
- `TimelineNode`: paper_id, arxiv_id, title, authors, published_date, category, citation_count (within cluster), global_citation_count, entities, summary, is_seminal, is_in_library, branch_id, x_position, y_position
- `TimelineEdge`: source_id, target_id, edge_type ("cites" | "related")
- `TimelineResponse`: topic, nodes, edges, time_range, root_paper_ids, branch_count, narrative

**Commit:** `feat: TR-1.2.1 — define timeline response schemas`

#### TR-1.2.2 — Implement `build_timeline_from_topic()`
1. Generate embedding for the query using `llm_service.generate_embedding(query)`
2. Semantic search: find top `limit` papers by embedding L2 distance (reuse search pattern from `routers/search.py`)
3. Extract citation subgraph within those papers using `get_citation_subgraph()`
4. Filter to keep only papers with ≥1 citation link to another paper in the set (connected papers), plus top 5 most-cited isolated papers
5. Build `TimelineNode` list with citation counts and date-based x_position
6. Identify seminal papers (see TR-1.2.4)
7. Detect branches (see TR-1.2.5)
8. Return `TimelineResponse`

**Commit:** `feat: TR-1.2.2 — implement topic-based timeline construction`

#### TR-1.2.3 — Implement `build_timeline_from_paper()`
1. Start with seed paper ID
2. Call `bfs_citations(seed_id, db, max_hops=2, direction="both")`
3. Fetch all discovered papers
4. Filter by embedding similarity to seed paper (cosine > 0.7) — drop tangential papers
5. Extract citation subgraph
6. Build nodes, identify seminal papers, detect branches
7. Return `TimelineResponse` centered on the seed paper

**Commit:** `feat: TR-1.2.3 — implement paper-based timeline construction`

#### TR-1.2.4 — Implement seminal paper identification
Write `_identify_seminal_papers(nodes, edges)`:
- A paper is seminal if:
  - It's the earliest in the cluster by `published_date`, OR
  - It has the highest citation count within the cluster, OR
  - It has no incoming edges (no paper in the cluster cites it)
- Score: `0.5 * normalized_age_rank + 0.5 * normalized_citation_rank`
- Mark top 3 as `is_seminal = True`

**Commit:** `feat: TR-1.2.4 — implement seminal paper identification`

#### TR-1.2.5 — Implement branch detection
Write `_detect_branches(nodes, edges, root_ids)`:
- BFS from each root paper through forward citations
- At each node, if ≥2 children share no edge between them → fork into new branches
- Assign `branch_id` to each node
- Return `dict[int, int]` mapping paper_id → branch_id

**Commit:** `feat: TR-1.2.5 — implement branch detection via BFS`

#### TR-1.2.6 — Implement layout computation
Write `_compute_layout(nodes, edges, branches)`:
- X-axis: normalize `published_date` to [0, 1] range based on timeline time_range
- Y-axis: assign vertical position by `branch_id` (each branch gets a lane, spaced evenly)
- Within same branch and same time bucket, stack vertically by citation count (most cited = center)
- Set `x_position` and `y_position` on each node

**Commit:** `feat: TR-1.2.6 — implement timeline layout computation`

---

### TR-1.3 — Timeline API Router

**Depends on:** TR-1.2
**Files:** `backend/routers/timeline.py`
**Commit after completing all sub-tasks:** `feat: TR-1.3 — add timeline API router`

#### TR-1.3.1 — Create `routers/timeline.py` with endpoints
- `GET /timeline/topic?q={query}&limit=50` → calls `build_timeline_from_topic()`
- `GET /timeline/paper/{paper_id}?hops=2` → calls `build_timeline_from_paper()`
- Validate inputs: `q` is required and non-empty, `limit` between 10-100, `hops` between 1-3
- Return `TimelineResponse` JSON

#### TR-1.3.2 — Add Pydantic request/response validation
- Query params validation via FastAPI `Query()` with defaults
- Response model: `TimelineResponse`

**Commit:** `feat: TR-1.3 — add timeline API router with topic and paper endpoints`

---

### TR-1.4 — Register Router & Test

**Depends on:** TR-1.3
**Files:** `backend/main.py`

#### TR-1.4.1 — Register timeline router in `main.py`
- `from routers.timeline import router as timeline_router`
- `app.include_router(timeline_router)`

**Commit:** `feat: TR-1.4.1 — register timeline router in main.py`

#### TR-1.4.2 — Manual API test
- Start backend locally
- Test `GET /timeline/topic?q=retrieval+augmented+generation` — verify response structure
- Test `GET /timeline/paper/{id}?hops=2` with a known paper ID that has citations
- Verify nodes have positions, edges connect valid IDs, seminal papers are identified

**Commit:** `test: TR-1.4.2 — verify timeline API endpoints manually`

---

## Phase 2: Core Frontend

**Goal:** Build the basic timeline page with React Flow visualization. Functional but not visually polished.

**Depends on:** Phase 1 complete

---

### TR-2.1 — Install React Flow

**Depends on:** Nothing (can start in parallel with Phase 1)
**Files:** `frontend/package.json`

#### TR-2.1.1 — Install `@xyflow/react` package
```bash
cd frontend && npm install @xyflow/react
```
- Verify no peer dependency conflicts
- Verify TypeScript types are included

**Commit:** `chore: TR-2.1.1 — install @xyflow/react for timeline visualization`

---

### TR-2.2 — Add API Client Methods

**Depends on:** TR-1.3 (endpoints must exist)
**Files:** `frontend/lib/api.ts`

#### TR-2.2.1 — Add timeline API methods
Add to the `api` object:
- `getTimelineByTopic(query: string, limit?: number)` → GET `/api/timeline/topic?q=...&limit=...`
- `getTimelineByPaper(paperId: number, hops?: number)` → GET `/api/timeline/paper/{paperId}?hops=...`

Add TypeScript interfaces:
- `TimelineNode` — matching backend schema
- `TimelineEdge` — matching backend schema
- `TimelineResponse` — full response type

**Commit:** `feat: TR-2.2.1 — add timeline API client methods and TypeScript types`

---

### TR-2.3 — Timeline Graph Component

**Depends on:** TR-2.1
**Files:** `frontend/components/TimelineGraph.tsx`, `frontend/components/TimelineNode.tsx`

#### TR-2.3.1 — Create `TimelineGraph` component
- Accept `TimelineResponse` as prop
- Convert `TimelineNode[]` to React Flow `Node[]` format (id, position, data)
- Convert `TimelineEdge[]` to React Flow `Edge[]` format (id, source, target)
- Render `<ReactFlow>` with nodes and edges
- Add `<Background>` (dot grid) and `<Controls>` (zoom buttons)
- Handle node click → emit `onNodeSelect(paperId)` callback

#### TR-2.3.2 — Create `TimelineNode` custom node component
- Basic rendering for MVP: rounded rectangle with paper title (truncated to 60 chars)
- Show published date below title
- Category-colored left border (reuse `getCategoryColor`)
- Node size: fixed for MVP (custom sizing in Phase 3)

**Commit:** `feat: TR-2.3 — create TimelineGraph and TimelineNode components`

---

### TR-2.4 — Timeline Page

**Depends on:** TR-2.2, TR-2.3
**Files:** `frontend/app/timeline/page.tsx`, `frontend/components/TimelineDetailPanel.tsx`

#### TR-2.4.1 — Create `TimelineDetailPanel` component
- Accept selected `TimelineNode` as prop
- Show: title, authors, published_date, category badges, citation count, entities as badges
- Action buttons: "Open Peek Sheet", "Full Details", "Add to Queue" (if reading queue exists), "Bookmark"
- Abstract text (truncated, expandable)

**Commit:** `feat: TR-2.4.1 — create TimelineDetailPanel component`

#### TR-2.4.2 — Create `/timeline` page
- Search bar at top: text input + "Search" button
- On search: call `api.getTimelineByTopic(query)`, store response in state
- Render `TimelineGraph` with the response
- Below graph: render `TimelineDetailPanel` for selected node
- Loading state: skeleton placeholder while API call is in progress
- Empty state: "Search for a topic to see how research evolved over time"
- Error state: "Failed to load timeline. Try a different query."

**Commit:** `feat: TR-2.4.2 — create /timeline page with search and graph`

---

### TR-2.5 — End-to-End Testing (Phase 2)

**Depends on:** TR-2.4

#### TR-2.5.1 — TypeScript check
```bash
cd frontend && npx tsc --noEmit
```
Verify zero errors.

#### TR-2.5.2 — Smoke test
- Start backend + frontend locally
- Navigate to `/timeline`
- Search for a topic with known papers (e.g., "attention mechanism")
- Verify: graph renders, nodes are clickable, detail panel shows paper info
- Verify: edges connect papers, no visual glitches

**Commit:** `test: TR-2.5 — verify timeline page renders and functions end-to-end`

---

## Phase 3: Visual Polish

**Goal:** Make the timeline look production-quality. Custom node rendering, animated edges, time axis, minimap.

**Depends on:** Phase 2 complete

---

### TR-3.1 — Custom Node Rendering

**Depends on:** TR-2.3
**Files:** `frontend/components/TimelineNode.tsx`

#### TR-3.1.1 — Size nodes by citation count
- Seminal papers: large (w:220, h:80), gold border, subtle pulsing glow animation (Framer Motion)
- High-citation (≥10): medium (w:200, h:70), standard border
- Regular (<10): small (w:180, h:60)

**Commit:** `feat: TR-3.1.1 — size timeline nodes by citation count`

#### TR-3.1.2 — Category-colored nodes
- Background: subtle tint of category color (5% opacity)
- Left border: 3px solid category accent color (reuse `getCategoryColor`)
- Category badge in top-right corner

**Commit:** `feat: TR-3.1.2 — category-color timeline nodes`

#### TR-3.1.3 — Library indicator
- If `is_in_library` is true, show a small filled bookmark icon in the top-left corner
- Slightly different border style (indigo glow) for library papers

**Commit:** `feat: TR-3.1.3 — add library bookmark indicator to timeline nodes`

---

### TR-3.2 — Edge Styling & Animations

**Depends on:** TR-3.1
**Files:** `frontend/components/TimelineGraph.tsx`

#### TR-3.2.1 — Style citation edges
- Solid lines for citation links (edge_type = "cites")
- Dashed lines for entity-similarity links (edge_type = "related") — Phase 4 adds these
- Arrow markers pointing from citing paper → cited paper
- Color: match source paper's category color (30% opacity)
- On hover: edge thickens, full opacity, tooltip shows "Paper A cites Paper B"

#### TR-3.2.2 — Animated edge flow
- Subtle animated dash pattern flowing along edges (CSS animation)
- Only active on hover or when connected node is selected

**Commit:** `feat: TR-3.2 — style and animate timeline edges`

---

### TR-3.3 — Time Axis

**Depends on:** TR-2.3
**Files:** `frontend/components/TimelineGraph.tsx`

#### TR-3.3.1 — Add horizontal time axis
- Render year markers along the bottom of the graph
- Vertical dashed lines at each year boundary
- Labels: "2020", "2021", "2022", etc.
- Proportional spacing matching node x_position

**Commit:** `feat: TR-3.3.1 — add horizontal time axis with year markers`

---

### TR-3.4 — Minimap & Controls

**Depends on:** TR-3.1
**Files:** `frontend/components/TimelineGraph.tsx`

#### TR-3.4.1 — Add React Flow minimap and controls
- `<MiniMap>` in bottom-right corner, node colors match category
- `<Controls>` with zoom in/out/fit buttons
- Initial viewport: `fitView` on load so all nodes are visible

#### TR-3.4.2 — Add keyboard navigation
- Arrow keys to pan
- +/- to zoom
- Escape to deselect node

**Commit:** `feat: TR-3.4 — add minimap, zoom controls, and keyboard navigation`

---

### TR-3.5 — Visual Polish Testing

**Depends on:** TR-3.1, TR-3.2, TR-3.3, TR-3.4

#### TR-3.5.1 — Visual review
- Test with various cluster sizes (5, 20, 50 papers)
- Verify node sizing, colors, edge rendering
- Test on different screen sizes (responsive)
- Verify minimap reflects actual graph state

**Commit:** `test: TR-3.5 — verify timeline visual polish across cluster sizes`

---

## Phase 4: Ghost Nodes & Library Toggle

**Goal:** Show unresolved citations as ghost nodes with import action. Add global/library scope toggle.

**Depends on:** Phase 2 complete

---

### TR-4.1 — Ghost Node Backend

**Depends on:** TR-1.2
**Files:** `backend/services/timeline_service.py`

#### TR-4.1.1 — Fetch unresolved citations for cluster papers
Query `CitationLink` where `source_paper_id IN cluster_ids AND resolved_paper_id IS NULL`:
- Return `target_arxiv_id`, `target_title`, `target_url`
- Count how many cluster papers cite each unresolved target
- Cap at top 10 most-cited unresolved targets

#### TR-4.1.2 — Add ghost nodes to TimelineResponse
- Create `TimelineNode` entries with `is_ghost=True` flag (add field to schema)
- Set `paper_id=None`, `arxiv_id=target_arxiv_id`, `title=target_title`
- Position ghost nodes based on `published_year` from CitationLink (X-axis) and branch of most citing papers (Y-axis)
- Add edges from citing cluster papers to ghost nodes

**Commit:** `feat: TR-4.1 — add ghost nodes for unresolved citations to timeline response`

---

### TR-4.2 — Ghost Node Frontend

**Depends on:** TR-4.1, TR-3.1
**Files:** `frontend/components/TimelineNode.tsx`

#### TR-4.2.1 — Render ghost nodes
- Grayed-out appearance: dashed border, 50% opacity, zinc background
- Show title + arxiv_id (if available)
- Dotted edge lines connecting to ghost nodes
- Tooltip: "This paper is not in your database"

**Commit:** `feat: TR-4.2.1 — render ghost nodes with grayed-out styling`

---

### TR-4.3 — Ghost Node Import Action

**Depends on:** TR-4.2
**Files:** `frontend/components/TimelineNode.tsx`, `frontend/components/TimelineDetailPanel.tsx`

#### TR-4.3.1 — Add "Import Paper" button on ghost nodes
- Click ghost node → detail panel shows "Import Paper" button
- Button calls existing `api.addPaper(arxiv_id)` to ingest the paper
- On success: toast "Paper imported! It will appear in the timeline after processing."
- Optimistic UI: change ghost node to a "pending" style (dotted border, loading spinner)

**Commit:** `feat: TR-4.3.1 — add import action for ghost nodes in timeline`

---

### TR-4.4 — Library Toggle Backend

**Depends on:** TR-1.2
**Files:** `backend/routers/timeline.py`, `backend/services/timeline_service.py`

#### TR-4.4.1 — Add `library_only` query parameter
- `GET /timeline/topic?q=...&library_only=true` → filter results to only include papers in user's library (UserLibrary table)
- Default: `library_only=false` (global scope)
- When `library_only=true`, semantic search is restricted to papers where `Paper.id IN (user's bookmarked paper IDs)`

**Commit:** `feat: TR-4.4.1 — add library_only filter to timeline endpoints`

---

### TR-4.5 — Library Toggle Frontend

**Depends on:** TR-4.4
**Files:** `frontend/app/timeline/page.tsx`

#### TR-4.5.1 — Add scope toggle to timeline page
- Toggle switch next to search bar: "All Papers" / "My Library"
- When toggled, re-fetch timeline with `library_only` parameter
- Persist preference in localStorage

**Commit:** `feat: TR-4.5.1 — add global/library scope toggle to timeline page`

---

## Phase 5: Entry Points & Navigation

**Goal:** Make the timeline accessible from multiple places in the app.

**Depends on:** Phase 2 complete

---

### TR-5.1 — Sidebar Navigation Link

**Depends on:** TR-2.4
**Files:** `frontend/components/Sidebar.tsx`

#### TR-5.1.1 — Add "Timeline" link to sidebar
- Add after "Analysis" in the sidebar nav
- Icon: `GitBranch` or `Network` from lucide-react
- Link to `/timeline`

**Commit:** `feat: TR-5.1.1 — add timeline link to sidebar navigation`

---

### TR-5.2 — Paper Detail Page Entry Point

**Depends on:** TR-2.4
**Files:** `frontend/app/paper/[id]/page.tsx`

#### TR-5.2.1 — Add "Show Timeline" button
- Add button in the paper detail page header area
- On click: navigate to `/timeline?paper={paper.db_id}`
- Timeline page reads `paper` query param and calls `getTimelineByPaper()` instead of topic search

**Commit:** `feat: TR-5.2.1 — add Show Timeline button to paper detail page`

---

### TR-5.3 — Peek Sheet Entry Point

**Depends on:** TR-2.4
**Files:** `frontend/components/QuickPeekSheet.tsx`

#### TR-5.3.1 — Add "Timeline" button to peek sheet actions
- Add alongside "Full Details" and "PDF" buttons
- Icon: `GitBranch` from lucide-react
- On click: close peek sheet, navigate to `/timeline?paper={paper.db_id}`

**Commit:** `feat: TR-5.3.1 — add Timeline button to QuickPeekSheet`

---

### TR-5.4 — Entity-Based Timeline

**Depends on:** TR-1.2
**Files:** `backend/services/timeline_service.py`, `backend/routers/timeline.py`, `frontend/app/timeline/page.tsx`

#### TR-5.4.1 — Implement `build_timeline_from_entity()` in service
- Query all papers with the given entity in their `entities` JSON column
- Build citation subgraph between those papers
- Return `TimelineResponse`

#### TR-5.4.2 — Add `GET /timeline/entity?name={entity}` endpoint

#### TR-5.4.3 — Add `getTimelineByEntity()` to frontend API client

#### TR-5.4.4 — Add entity click handler
- On paper detail page and peek sheet, entity badges are clickable
- Click an entity → navigate to `/timeline?entity={entity_name}`
- Timeline page reads `entity` query param and calls `getTimelineByEntity()`

**Commit:** `feat: TR-5.4 — add entity-based timeline with clickable entity badges`

---

## Phase 6: Intelligence

**Goal:** Add LLM-generated narrative summaries, auto-labeled branches, and dashboard integration.

**Depends on:** Phase 3 complete

---

### TR-6.1 — Narrative Generation Backend

**Depends on:** TR-1.2
**Files:** `backend/services/timeline_service.py`

#### TR-6.1.1 — Implement `_generate_narrative()`
- Construct a prompt with: topic, seminal papers (title + date), branch structure, key entities
- Call `llm_service.chat()` (Gemini) with the prompt
- Expected output: 2-3 sentence summary, e.g., "RAG originated with Lewis et al. (2020)..."
- Return as string

#### TR-6.1.2 — Add caching for narratives
- Cache key: hash of `(query, sorted paper_ids)`
- Store in a simple dict or lightweight cache (don't need a new DB table)
- TTL: 7 days (topics don't change that fast)

#### TR-6.1.3 — Fire narrative generation in background
- Timeline endpoint returns response immediately with `narrative: null`
- Spawns background task to generate narrative
- Frontend polls or uses a separate endpoint: `GET /timeline/narrative?cache_key=...`

**Commit:** `feat: TR-6.1 — add Gemini narrative generation for timelines with caching`

---

### TR-6.2 — Narrative Frontend

**Depends on:** TR-6.1
**Files:** `frontend/app/timeline/page.tsx`

#### TR-6.2.1 — Render narrative panel
- Glassmorphism card above the timeline graph
- If `narrative` is null: show skeleton loader or "Generating narrative..."
- If `narrative` is present: render text with fade-in animation (Framer Motion)
- Collapsible with a chevron toggle

**Commit:** `feat: TR-6.2.1 — render narrative panel above timeline with fade-in`

---

### TR-6.3 — Branch Auto-Labeling

**Depends on:** TR-6.1, TR-1.2.5
**Files:** `backend/services/timeline_service.py`

#### TR-6.3.1 — Label branches by dominant entity
- For each branch, collect all entities from papers in that branch
- Find the most frequent entity that differentiates this branch from others
- Set `branch_label` (e.g., "Dense Retrieval", "Chunk Optimization")

#### TR-6.3.2 — Render branch labels in frontend
- Show label at the start of each branch lane
- Styled as a small badge

**Commit:** `feat: TR-6.3 — auto-label timeline branches by dominant entity`

---

### TR-6.4 — Dashboard Timeline Tile

**Depends on:** TR-2.2
**Files:** `frontend/components/dashboard/TimelineTile.tsx`, `frontend/components/DashboardContent.tsx`

#### TR-6.4.1 — Create `TimelineTile` component
- Small card showing a mini timeline for the user's most-bookmarked topic
- Determine topic: find the most common entity across user's bookmarks
- Render 5-8 nodes in a simplified horizontal layout (no React Flow — just CSS positioned dots with lines)
- "Explore Timeline →" link to `/timeline?entity={top_entity}`

#### TR-6.4.2 — Add TimelineTile to dashboard bento grid
- Insert in `DashboardContent.tsx` alongside existing tiles

**Commit:** `feat: TR-6.4 — add Research Lineage tile to dashboard`

---

## Summary

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
TR-2.1 → TR-2.2 → TR-2.3 → TR-2.4 → TR-2.5 (frontend MVP complete)
                                ↓
TR-3.1 → TR-3.2 → TR-3.3 → TR-3.4 → TR-3.5 (visual polish complete)
```

Phases 4 and 5 can run in parallel after Phase 2. Phase 6 can start after Phase 3.

## Files to Create

| File | Phase | Purpose |
|------|-------|---------|
| `backend/services/timeline_service.py` | 1 | Timeline construction, BFS traversal, branch detection, narrative |
| `backend/routers/timeline.py` | 1 | API endpoints |
| `frontend/components/TimelineGraph.tsx` | 2 | React Flow graph wrapper |
| `frontend/components/TimelineNode.tsx` | 2 | Custom node rendering |
| `frontend/components/TimelineDetailPanel.tsx` | 2 | Selected paper detail |
| `frontend/app/timeline/page.tsx` | 2 | Timeline page |
| `frontend/components/dashboard/TimelineTile.tsx` | 6 | Dashboard widget |

## Files to Modify

| File | Phase | Change |
|------|-------|--------|
| `backend/main.py` | 1 | Register timeline router |
| `frontend/lib/api.ts` | 2 | Add timeline API methods + types |
| `frontend/package.json` | 2 | Add `@xyflow/react` |
| `frontend/components/Sidebar.tsx` | 5 | Add Timeline nav link |
| `frontend/app/paper/[id]/page.tsx` | 5 | Add "Show Timeline" button |
| `frontend/components/QuickPeekSheet.tsx` | 5 | Add Timeline button |
| `frontend/components/DashboardContent.tsx` | 6 | Add TimelineTile |
