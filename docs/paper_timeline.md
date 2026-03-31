# Paper Timeline / Evolution View — Detailed Scratchpad

## Problem Statement

Researchers need to understand how ideas evolve. When exploring a topic like "LoRA" or "Chain-of-Thought prompting," the questions are:
- **Who started this?** Which paper introduced the concept?
- **Who extended it?** What are the direct follow-ups and improvements?
- **Where did it fork?** Are there competing approaches or sub-branches?
- **What's the current frontier?** What are the most recent and most impactful papers?

Currently, the arxiv_assistant shows papers as a flat list. The citation graph exists in the database but has no visual representation and no traversal endpoints. There's no way to see the lineage of an idea.

---

## Vision

A user types a topic (e.g., "LoRA fine-tuning") and gets a **visual timeline** showing:

```
2021-06 ──── [LoRA: Low-Rank Adaptation] ◉ (seminal, 847 citations)
              │
              ├── 2022-03 ── [QLoRA: Efficient Finetuning] ● (312 citations)
              │               │
              │               └── 2023-08 ── [QA-LoRA: Quantization-Aware] ○
              │
              ├── 2022-09 ── [AdaLoRA: Adaptive Budget Allocation] ● (89 citations)
              │
              ├── 2023-02 ── [LoRA-FA: Memory-Efficient] ○
              │
              └── 2023-11 ── [DoRA: Weight-Decomposed] ● (45 citations)
                              │
                              └── 2024-06 ── [LoRA+: Efficient Low Rank] ○
```

**Node size** = citation count. **Edges** = citation links. **X-axis** = time. **Branching** = divergent approaches.

---

## User Interaction Flow

### Entry Point 1: Topic Search
1. User navigates to `/timeline`
2. Types a topic query (e.g., "chain of thought reasoning")
3. System runs semantic search → finds top N related papers
4. System builds citation subgraph within those papers
5. Renders interactive timeline

### Entry Point 2: Paper Context
1. User is on a paper detail page or peek sheet
2. Clicks "Show Timeline" / "See Evolution"
3. System uses that paper as the seed → finds citing and cited papers
4. Expands outward (cited-by and cites) up to 2-3 hops
5. Renders timeline centered on that paper

### Entry Point 3: Dashboard Widget
1. Small "Research Lineage" tile showing the timeline for the user's most-bookmarked topic
2. Click to expand to full `/timeline` page

---

## Data Pipeline

### Step 1: Find the Paper Cluster

**Option A: Topic-Based (from search query)**
```
Input: "retrieval augmented generation"
→ Semantic search (embedding similarity) → top 50 papers
→ Filter: only papers with ≥1 citation link to another paper in the set
→ Result: connected subgraph of ~15-30 papers
```

**Option B: Paper-Based (from seed paper)**
```
Input: Paper ID 12345 ("Attention Is All You Need")
→ Find all papers citing this paper (forward citations)
→ Find all papers this paper cites (backward citations)
→ Expand 1-2 more hops from each
→ Filter: keep only papers with embeddings similar to the seed (cosine > 0.7)
→ Result: focused citation tree of ~10-40 papers
```

**Option C: Entity-Based (from entity)**
```
Input: Entity "LoRA" (type: Model)
→ Find all papers with this entity in their entities JSON
→ Sort by published_date
→ Build citation links between them
→ Result: entity-focused timeline
```

### Step 2: Build the Graph

From the paper cluster, construct:

```python
@dataclass
class TimelineNode:
    paper_id: int
    arxiv_id: str
    title: str
    authors: list[str]
    published_date: datetime
    category: str
    citation_count: int       # how many papers in the cluster cite this
    global_citation_count: int # total citations in DB
    entities: list[str]
    summary: str | None
    is_seminal: bool          # earliest paper or most cited
    is_in_library: bool       # user has this bookmarked

@dataclass
class TimelineEdge:
    source_paper_id: int      # the citing paper
    target_paper_id: int      # the cited paper
    edge_type: str            # "cites" (only type for now)

@dataclass
class Timeline:
    topic: str
    nodes: list[TimelineNode]
    edges: list[TimelineEdge]
    time_range: tuple[datetime, datetime]
    root_papers: list[int]    # seminal/earliest papers (entry points)
```

### Step 3: Identify Seminal Papers

A paper is "seminal" (root node) if:
1. It's the **earliest** paper in the cluster by `published_date`, OR
2. It has the **highest citation count** within the cluster (most cited by other cluster papers), OR
3. It has **no incoming edges** from other papers in the cluster (nothing in the cluster cites it — it's a source)

Rank by: `0.5 * normalized_age + 0.5 * normalized_citation_count`

### Step 4: Detect Branches

A **branch** occurs when a seminal paper has ≥2 papers citing it that don't cite each other. Each independent citing paper starts a branch.

Algorithm:
1. Start from each root paper
2. BFS forward through citations
3. At each node, if it has ≥2 citing papers that share no citation link between them → fork
4. Label each branch by the dominant entity or keyword difference

### Step 5: Compute Layout

**Horizontal timeline layout:**
- X-axis = `published_date` (proportional spacing)
- Y-axis = branch assignment (each branch gets a lane)
- Root papers at the left, latest papers at the right

**Layout algorithm (Sugiyama-style for DAGs):**
1. Topological sort of the citation DAG
2. Assign layers by publication date (bucket into months/quarters)
3. Within each layer, order by citation count (most cited = center)
4. Minimize edge crossings using barycentric heuristic
5. Add vertical spacing for branches

---

## Backend Design

### New Service: `timeline_service.py`

```python
class TimelineService:
    def build_timeline_from_topic(self, query: str, db, limit: int = 50) -> Timeline:
        """
        1. Semantic search for top `limit` papers matching query
        2. Fetch citation links between those papers
        3. Filter to connected components only
        4. Identify seminal papers
        5. Return Timeline object
        """

    def build_timeline_from_paper(self, paper_id: int, db, hops: int = 2) -> Timeline:
        """
        1. Start with seed paper
        2. BFS forward (papers citing this) and backward (papers cited by this)
        3. Expand `hops` levels
        4. Filter by embedding similarity to seed (cosine > 0.7)
        5. Return Timeline object
        """

    def build_timeline_from_entity(self, entity: str, db) -> Timeline:
        """
        1. Find all papers with this entity
        2. Build citation links between them
        3. Return Timeline object
        """

    def _get_citation_subgraph(self, paper_ids: list[int], db) -> tuple[list[TimelineNode], list[TimelineEdge]]:
        """
        Given a set of paper IDs, return all citation links between them.
        Single efficient query.
        """

    def _identify_seminal_papers(self, nodes: list[TimelineNode], edges: list[TimelineEdge]) -> list[int]:
        """
        Find root papers: earliest + most cited + no incoming edges.
        """

    def _detect_branches(self, nodes, edges, roots) -> dict[int, int]:
        """
        Assign each node a branch ID by BFS from roots.
        Returns {paper_id: branch_id}
        """

    def _generate_summary(self, timeline: Timeline, db) -> str:
        """
        Use Gemini to generate a 2-3 sentence narrative:
        'This topic originated with [Paper A] in 2021, which introduced [concept].
         It was extended by [Paper B] and [Paper C], which focused on [variant].'
        """
```

### New Router: `routers/timeline.py`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/timeline/topic?q={query}&limit=50` | Build timeline from topic search |
| `GET` | `/timeline/paper/{paper_id}?hops=2` | Build timeline from seed paper |
| `GET` | `/timeline/entity?name={entity}` | Build timeline from entity |

**Response Schema:**

```python
class TimelineNodeResponse(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str
    authors: list[str]
    published_date: str
    category: str
    citation_count: int
    global_citation_count: int
    entities: list[str]
    summary: str | None
    is_seminal: bool
    is_in_library: bool
    branch_id: int
    x_position: float      # normalized [0, 1] for date axis
    y_position: float      # branch lane

class TimelineEdgeResponse(BaseModel):
    source_id: int
    target_id: int
    edge_type: str

class TimelineResponse(BaseModel):
    topic: str
    nodes: list[TimelineNodeResponse]
    edges: list[TimelineEdgeResponse]
    time_range: tuple[str, str]
    root_paper_ids: list[int]
    branch_count: int
    narrative: str | None    # Gemini-generated summary
```

### Citation Graph Traversal Queries

**Forward citations (papers citing a given paper):**
```sql
SELECT p.id, p.arxiv_id, p.title, p.published_date, p.category, p.entities
FROM citation_links cl
JOIN papers p ON p.id = cl.source_paper_id
WHERE cl.resolved_paper_id = :paper_id
   OR cl.target_arxiv_id = :arxiv_id
ORDER BY p.published_date
```

**Backward citations (papers cited by a given paper):**
```sql
SELECT p.id, p.arxiv_id, p.title, p.published_date, p.category, p.entities
FROM citation_links cl
JOIN papers p ON p.id = cl.resolved_paper_id
WHERE cl.source_paper_id = :paper_id
  AND cl.resolved_paper_id IS NOT NULL
ORDER BY p.published_date
```

**Subgraph extraction (all links within a paper set):**
```sql
SELECT cl.source_paper_id, cl.resolved_paper_id
FROM citation_links cl
WHERE cl.source_paper_id IN :paper_ids
  AND cl.resolved_paper_id IN :paper_ids
  AND cl.resolved_paper_id IS NOT NULL
```

**Multi-hop BFS (Python, not SQL):**
```python
def bfs_citations(seed_id: int, db, max_hops: int = 2, direction: str = "both") -> set[int]:
    visited = {seed_id}
    frontier = {seed_id}
    for hop in range(max_hops):
        next_frontier = set()
        for pid in frontier:
            if direction in ("forward", "both"):
                # Papers citing this one
                forward = db.query(CitationLink.source_paper_id).filter(
                    CitationLink.resolved_paper_id == pid
                ).all()
                next_frontier |= {r[0] for r in forward}
            if direction in ("backward", "both"):
                # Papers cited by this one
                backward = db.query(CitationLink.resolved_paper_id).filter(
                    CitationLink.source_paper_id == pid,
                    CitationLink.resolved_paper_id.isnot(None)
                ).all()
                next_frontier |= {r[0] for r in backward}
        next_frontier -= visited
        visited |= next_frontier
        frontier = next_frontier
    return visited
```

---

## Frontend Design

### Visualization Library Choice

**Options evaluated:**

| Library | Pros | Cons | Fit |
|---------|------|------|-----|
| **React Flow** | Purpose-built for node-edge diagrams, React-native, interactive, minimap, controls | New dependency, opinionated styling | Best for structured DAGs |
| **D3.js** | Maximum flexibility, force-directed layouts, timeline layouts | Low-level, steep learning curve, not React-idiomatic | Best for custom layouts |
| **Three.js (existing)** | Already installed, 3D capable, impressive visuals | Overkill for 2D timeline, complex interaction handling | Only if we want 3D |
| **Recharts (existing)** | Already installed, simple API | Not designed for graph/network visualizations | Not suitable |
| **vis-network** | Auto-layout, interactive, clustering | Not React-native, large bundle size | Decent but not ideal |
| **@xyflow/react** (React Flow v12) | Modern, TypeScript, lightweight | New dep | Best option |

**Recommendation: React Flow (`@xyflow/react`)** — purpose-built for node-edge diagrams, React-native, supports custom node rendering, has built-in minimap and zoom controls. Lightweight (~45KB gzipped).

### Timeline Page (`/timeline`)

```
┌─────────────────────────────────────────────────────────────┐
│  Research Timeline                              [🔍 Search]  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Search: [retrieval augmented generation          ] [Go]│  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ Narrative ────────────────────────────────────────────┐  │
│  │ "RAG originated with Lewis et al. (2020), combining    │  │
│  │  retrieval with generation. Key branches: dense         │  │
│  │  retrieval (Karpukhin 2020) and chunk optimization..."  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ Timeline ─────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  2020        2021        2022        2023        2024   │  │
│  │  ──┼───────────┼───────────┼───────────┼───────────┼──  │  │
│  │                                                         │  │
│  │  ◉ RAG ─────── ● DPR ──── ● ColBERT ── ○ BGE-M3      │  │
│  │  (Lewis)       │           │                            │  │
│  │                │           └── ○ ColBERTv2              │  │
│  │                │                                        │  │
│  │                └── ● REALM ── ● Atlas ── ○ Self-RAG     │  │
│  │                                                         │  │
│  │  [Minimap]                          [Zoom +] [Zoom -]   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ Selected Paper ──────────────────────────────────────┐   │
│  │ Title: Retrieval-Augmented Generation for Knowledge-   │   │
│  │        Intensive NLP Tasks                             │   │
│  │ Authors: Lewis et al.  ·  2020-05  ·  cs.CL           │   │
│  │ Citations: 847  ·  Entities: BART, DPR, NQ             │   │
│  │ [Open Peek Sheet]  [Full Details]  [Add to Queue]      │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Custom React Flow Node

```typescript
interface TimelinePaperNode {
    id: string;             // paper_id
    type: "paper";
    position: { x: number; y: number };
    data: {
        title: string;
        arxiv_id: string;
        published_date: string;
        category: string;
        citation_count: number;
        is_seminal: boolean;
        is_in_library: boolean;
        entities: string[];
        summary: string | null;
    };
}
```

**Node rendering:**
- **Seminal papers:** Large circle (◉), gold border, pulsing glow
- **High-citation papers:** Medium circle (●), sized by citation count
- **Regular papers:** Small circle (○), category-colored
- **In-library papers:** Bookmark icon overlay
- **Hover:** Show paper title, authors, date, citation count
- **Click:** Select paper → show detail panel below

### Edge Rendering

- **Solid lines:** Direct citation link
- **Animated dash:** Click to show which paper cites which
- **Color:** Match source paper's category color
- **Arrow:** Points from citing paper → cited paper (chronological direction)

### Interactions

- **Pan & Zoom:** Built into React Flow
- **Click node:** Select → show detail panel
- **Double-click node:** Open peek sheet
- **Hover node:** Tooltip with title + date + citation count
- **Click edge:** Highlight the citation relationship
- **Minimap:** Bottom-right corner for orientation
- **Time axis:** Fixed horizontal axis showing years
- **Branch labels:** Auto-generated or entity-based

### Search Bar

- Same hybrid search as the research page
- Debounced input (300ms)
- Results populate the timeline
- Recent searches in dropdown

### Detail Panel

When a node is selected, show below the timeline:
- Paper title, authors, date, category
- Abstract (truncated)
- Entity badges
- Citation count (in cluster + global)
- Actions: Open Peek Sheet, Full Details, Add to Reading Queue, Bookmark

---

## Edge Cases & Considerations

### Small Clusters (< 5 papers)
- Still render as timeline but with a message: "Limited papers found for this topic in your library"
- Suggest: "Add more papers on this topic to build a richer timeline"

### Disconnected Components
- If the search returns papers with no citation links between them:
  - Show as independent nodes on the timeline (no edges)
  - Sort by date on the X-axis
  - Message: "These papers are related by topic but no direct citations found"

### Very Large Clusters (> 100 papers)
- Cap initial render at 50 papers (most cited + most recent)
- "Show more" button to expand
- Cluster tightly-connected subgroups into expandable mega-nodes

### No Papers Found
- Empty state: "No papers found for this topic. Try a different query."
- Suggest popular topics from the user's library

### Missing Citation Data
- Papers without resolved citations show as isolated nodes
- Tooltip: "Citation data not yet processed"

### Cold Start (New User, Few Papers)
- Timeline still works — shows papers from the global database
- Less personalization (no "in your library" badges)

### Performance
- Semantic search: ~200ms for top 50 papers
- Citation subgraph extraction: ~50ms (indexed queries)
- BFS traversal (2 hops): ~100ms
- Layout computation: client-side, ~50ms for 50 nodes
- Total: <500ms for initial render

---

## API Client Additions (`frontend/lib/api.ts`)

```typescript
// Timeline
getTimelineByTopic: async (query: string, limit?: number) => {
    const params = new URLSearchParams({ q: query });
    if (limit) params.set("limit", String(limit));
    const res = await fetch(`${API_URL}/timeline/topic?${params}`);
    if (!res.ok) throw new Error("Failed to fetch timeline");
    return res.json();
},

getTimelineByPaper: async (paperId: number, hops?: number) => {
    const params = hops ? `?hops=${hops}` : "";
    const res = await fetch(`${API_URL}/timeline/paper/${paperId}${params}`);
    if (!res.ok) throw new Error("Failed to fetch timeline");
    return res.json();
},

getTimelineByEntity: async (entity: string) => {
    const params = new URLSearchParams({ name: entity });
    const res = await fetch(`${API_URL}/timeline/entity?${params}`);
    if (!res.ok) throw new Error("Failed to fetch timeline");
    return res.json();
},
```

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `backend/services/timeline_service.py` | Timeline construction, BFS traversal, branch detection, narrative generation |
| `backend/routers/timeline.py` | API endpoints for timeline |
| `frontend/app/timeline/page.tsx` | Timeline page with search and visualization |
| `frontend/components/TimelineGraph.tsx` | React Flow graph component with custom nodes/edges |
| `frontend/components/TimelineNode.tsx` | Custom paper node rendering for React Flow |
| `frontend/components/TimelineDetailPanel.tsx` | Selected paper detail panel below the timeline |

### Modified Files

| File | Change |
|------|--------|
| `backend/main.py` | Register timeline router |
| `backend/models/__init__.py` | (No new models needed — uses existing Paper + CitationLink) |
| `frontend/lib/api.ts` | Add timeline API methods |
| `frontend/components/Sidebar.tsx` | Add "Timeline" nav link |
| `frontend/package.json` | Add `@xyflow/react` dependency |

### Optional Enhancements (Future)

| File | Purpose |
|------|---------|
| `frontend/components/dashboard/TimelineTile.tsx` | Dashboard "Research Lineage" widget |
| `backend/services/timeline_service.py` | Gemini narrative generation |
| `frontend/components/TimelineEntityFilter.tsx` | Filter timeline by entity type |

---

## Phased Implementation

### Phase 1: Core Timeline (MVP)
- Backend: `timeline_service.py` with `build_timeline_from_topic()` + `build_timeline_from_paper()`
- Backend: `/timeline/topic` and `/timeline/paper/{id}` endpoints
- Frontend: Install `@xyflow/react`
- Frontend: `/timeline` page with topic search
- Frontend: `TimelineGraph` component with basic node rendering
- Frontend: `TimelineDetailPanel` for selected paper

### Phase 2: Visual Polish
- Custom node rendering (size by citations, category colors, seminal glow)
- Animated edges
- Time axis with year markers
- Branch labels from dominant entity
- Minimap and zoom controls
- Responsive layout

### Phase 3: Entry Points
- "Show Timeline" button on paper detail page and peek sheet
- Entity-based timeline (`/timeline/entity`)
- Sidebar navigation link
- Dashboard widget

### Phase 4: Intelligence
- Gemini narrative generation ("This topic originated with...")
- Branch auto-labeling via LLM
- "Research frontier" indicator (most recent + highly cited)
- Comparison of branches (what's different about each approach)

---

## Design Decisions (Resolved)

| # | Question | Decision |
|---|----------|----------|
| 1 | Visualization library | **React Flow (`@xyflow/react`)** — purpose-built for DAGs, React-native, lightweight |
| 2 | Hops for paper-based timeline | **Default 2 hops**, expand to 3 with "Load more". Filter by embedding similarity (cosine > 0.7) to drop tangential papers |
| 3 | Global or library scope | **Global by default** with toggle to filter to "In My Library" only. Highlight library papers with bookmark overlay on global view |
| 4 | Narrative generation | **Background generation** — render graph immediately, fire Gemini call in parallel, fade narrative in when ready. Cache keyed by `(query_hash, paper_ids_hash)` |
| 5 | Unresolved citations | **Ghost nodes with "Import" action** — grayed out nodes with title, dotted edges, click to ingest paper. Cap at 10 most-cited ghost nodes per timeline |
| 6 | Branching strategy | **Hybrid** — citation links as primary structure (solid edges), entity similarity for disconnected papers sharing ≥2 entities (dashed "related" edges, toggleable) |
