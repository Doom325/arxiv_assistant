# Paper Timeline View — UI Description

Use this as a prompt for a UI agent to recreate the timeline view.

---

## Overview

An interactive citation-graph timeline for exploring how research papers relate to each other over time. Built with **React Flow** (`@xyflow/react`) inside a **Next.js** app with a dark theme (zinc-900/950 backgrounds, glassmorphism, Tailwind CSS v4).

The page lives at `/timeline` and has three sections stacked vertically: a **search bar** at the top, a **graph canvas** in the middle, and a **detail panel** at the bottom (visible when a node is selected).

---

## Search Bar

- Full-width input with a search icon and submit button, inside a `max-w-7xl` centered container with `px-4 py-8`.
- Placeholder: "Search for a topic to build a timeline..."
- A **library toggle** switch next to the search bar lets users scope results to "All Papers" or "My Library".
- URL query params drive initial state: `?q={topic}` for topic search, `?paper={id}` for paper-seeded timeline.
- Loading state: spinner replaces the search icon, "Building timeline..." message centered in the graph area.

---

## Graph Canvas

A `w-full h-[650px]` React Flow canvas with:

- **Background:** Dark grid pattern (`#27272a`, 20px gap) inside a `bg-zinc-950/50 border border-white/10 rounded-2xl` container.
- **Minimap:** Bottom-right corner, `bg-zinc-900` with `border-zinc-700`, nodes colored by their arXiv category.
- **Controls:** Zoom +/-, fit-to-view buttons in `bg-zinc-800 border-zinc-700` style, positioned bottom-left.
- **Zoom:** Min 0.2x, max 2.5x. Fit-view with 40% padding on load.

### Nodes (Custom `TimelineNode` Component)

Each node is a paper rendered as a rounded card. There are four visual tiers:

1. **Seminal papers** (top 3 by age + citation score):
   - Largest size (`w-[280px]`), `py-4 px-4`.
   - **Gold/amber border** (`border-amber-500`), pulsing amber glow animation (`shadow-amber-500/15`).
   - Title in `text-sm font-semibold`, truncated to 2 lines.
   - Star icon badge in top-left.

2. **High-citation papers** (≥10 citations within cluster):
   - Medium size (`w-[240px]`), `py-3 px-4`.
   - Border colored by arXiv category.
   - Title in `text-xs font-semibold`.

3. **Regular papers**:
   - Small size (`w-[200px]`), `py-2.5 px-3`.
   - Subtle `border-white/20` border.
   - Title in `text-xs`, truncated to 1 line.

4. **Ghost nodes** (unresolved citations — papers not in the database):
   - Dashed border (`border-dashed border-zinc-600`), `opacity-60`, `bg-zinc-900/50`.
   - Show arXiv ID instead of full metadata.
   - Ghost icon indicator.

**Common node elements:**
- **Left accent border:** 3px solid line in the paper's category color.
- **Category badge:** Small pill (`px-1.5 py-0.5 text-[8px]`) in the top-right corner, background tinted with category color.
- **Library indicator:** Small indigo bookmark icon with `ring-indigo-500/30` glow if the paper is in the user's library.
- **Citation count:** Shown in meta line (`text-[10px] text-zinc-400`), format: "N citations".
- **Date:** Publication date in meta line.
- **Selected state:** `ring-2 ring-indigo-500/70` border with `shadow-indigo-500/50` glow.

**Category colors** come from a lookup function that maps arXiv categories (cs.AI, cs.CL, cs.LG, etc.) to accent/bg/text/border Tailwind classes.

### Edges

- **Type:** Smoothstep edges with arrow markers pointing from citing paper → cited paper.
- **"cites" edges:** Solid stroke, colored by the source paper's category color.
- **"related" edges:** Dashed stroke with animated dash flow.
- **Hover:** Opacity increases on hover.
- **Arrow:** `markerEnd` with a small arrowhead.

### Layout Algorithm (Backend-Computed)

- **X-axis:** Papers positioned by publication date. Earliest paper at x=0, latest at x=1 (normalized). Frontend scales to canvas width.
- **Y-axis:** Papers grouped into **branches** via BFS. A branch forks when a node has 2+ unlinked children in the citation graph. Each branch gets its own horizontal lane (y = branch_id).
- The layout produces a left-to-right chronological flow with vertical branching for citation lineages.

---

## Detail Panel

Appears below the graph when a node is clicked. Shows:

- **Paper title** (large), authors list, publication date, category badge.
- **Abstract/summary** text.
- **Action buttons:**
  - For ghost nodes: "Import Paper" (fetches from arXiv and adds to database).
  - For regular nodes: "Full Details" (navigates to `/paper/{paper_id}`), "arXiv" external link.
  - "Bookmark" toggle button (BookmarkButton component).
- Styled with `bg-zinc-900/90 border border-white/10 rounded-2xl` to match the graph container.

---

## Entry Points

1. **Sidebar:** "Timeline" link with a `GitBranch` (Lucide) icon in the main navigation sidebar.
2. **Quick Peek Sheet:** When viewing a paper in the peek modal, a "Timeline" button with GitBranch icon links to `/timeline?paper={paper.db_id}`.
3. **Paper Detail Page:** Similar "Timeline" button linking to the paper-seeded view.

---

## Data Flow

### Topic-Based Timeline (`GET /timeline/topic?q=...&limit=50&library_only=false`)
1. Generate embedding for the search query.
2. Semantic search (pgvector L2 distance) → top N papers.
3. Extract citation subgraph among those papers.
4. Score seminal papers: 50% age rank + 50% citation count rank → top 3.
5. Detect branches via BFS (fork when a node has ≥2 unlinked children).
6. Compute layout positions (x from date range, y from branch ID).
7. Fetch up to 10 ghost nodes (unresolved citations grouped by target arXiv ID).
8. Return `{ nodes, edges, query }`.

### Paper-Based Timeline (`GET /timeline/paper/{paper_id}?hops=2`)
1. BFS from seed paper, both forward (papers citing it) and backward (papers it cites), up to N hops.
2. Filter by embedding cosine similarity > 0.7 to the seed (drop tangential results).
3. Same seminal detection, branching, layout, and ghost node logic.
4. Return `{ nodes, edges, seed_paper_id }`.

### Response Schema

```typescript
interface TimelineNode {
  paper_id: number | null;    // null for ghost nodes
  arxiv_id: string;
  title: string;
  authors: object;
  summary: string | null;
  published_date: string | null;  // ISO format
  category: string | null;
  citation_count: number;     // within this cluster
  is_seminal: boolean;
  is_in_library: boolean;
  is_ghost: boolean;
  branch_id: number;
  x_position: number;        // 0-1 normalized
  y_position: number;        // branch lane index
}

interface TimelineEdge {
  source_paper_id: number;
  target_paper_id: number;
  edge_type: "cites" | "related";
}

interface TimelineResponse {
  nodes: TimelineNode[];
  edges: TimelineEdge[];
  query?: string;
  seed_paper_id?: number;
}
```

---

## Empty & Error States

- **No search yet:** Centered message "Search for a topic to explore its research timeline" with a GitBranch icon.
- **No results:** "No papers found for this topic. Try a broader search term."
- **Error:** "Failed to load timeline. Try a different query." with retry option.
- **Loading:** Spinner + "Building timeline..." in the center of the graph area.
