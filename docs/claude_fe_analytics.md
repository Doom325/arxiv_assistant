# Detailed Plan: Analytics Views

## Overview

Replace the current basic citation-list Analysis page with a full analytics dashboard. The new `/analytics` route provides multiple visualization panels showing trends, distributions, and network relationships across the paper library.

---

## New Backend Endpoints Required

### GET /analytics/papers-over-time
```
Params: granularity (day|week|month), category (optional), start_date, end_date
Response: [
  { "date": "2024-03-01", "count": 23, "category_counts": { "cs.AI": 12, "cs.LG": 8, "cs.CL": 3 } },
  ...
]
```
Implementation: SQL `GROUP BY date_trunc(granularity, published_date), category` on papers table.

### GET /analytics/category-distribution
```
Params: start_date (optional), end_date (optional)
Response: [
  { "category": "cs.AI", "count": 1234, "pct": 0.32 },
  ...
]
```
Implementation: `SELECT category, COUNT(*) FROM papers GROUP BY category ORDER BY count DESC`.

### GET /analytics/top-authors
```
Params: limit (default 20), category (optional), start_date, end_date
Response: [
  { "author": "Yann LeCun", "paper_count": 45, "categories": ["cs.LG", "cs.AI"] },
  ...
]
```
Implementation: Unnest JSON authors array, group by author name, count papers.

### GET /analytics/pattern-trends
```
Params: granularity (week|month), start_date, end_date
Response: [
  { "date": "2024-W12", "total": 50, "agentic": 20, "categories": { "agent_planning": 8, ... } },
  ...
]
```
Implementation: Group `pattern_experiment_results` by date + primary_category.

### GET /analytics/library-growth
```
Params: user_id (default 1)
Response: [
  { "date": "2024-03-01", "cumulative": 45, "added": 3 },
  ...
]
```
Implementation: Group `user_library.added_at` by date, running cumulative sum.

### GET /citations/network
```
Params: paper_id (optional), depth (1-3, default 2), limit (default 100)
Response: {
  "nodes": [
    { "id": "2402.12345", "title": "...", "category": "cs.AI", "citation_count": 42, "in_library": true },
    ...
  ],
  "edges": [
    { "source": "2402.12345", "target": "1706.03762", "type": "cites" },
    ...
  ]
}
```
Implementation: Recursive CTE on citation_links, resolve to papers table for metadata.

All endpoints go in a new `backend/routers/analytics.py` router, registered in `main.py`.

---

## Analytics Dashboard Layout

### Page Structure (`/analytics`)

```
┌─────────────────────────────────────────────────────────────┐
│  Analytics                                                   │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 1,247    │ │ +23      │ │ 12       │ │ 38%      │      │
│  │ Papers   │ │ Today    │ │ Categories│ │ Agentic  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                              │
│  ┌─ Global Filters ────────────────────────────────────────┐│
│  │ [This Month] [3 Months] [6 Months] [1 Year] [All]      ││
│  │ Category: [All ▼]                                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ═══════════════════════════════════════════════════════════ │
│                                                              │
│  Panels below (scrollable)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Stat Cards (Top Row)
Four summary cards with:
- Large number (animated count-up on load)
- Label
- Trend indicator: ↑12% or ↓5% vs previous period (green/red)
- Mini sparkline (last 14 days)

---

## Panel 1: Papers Over Time (Area Chart)

### Visualization
Stacked area chart showing paper volume by category over time.

```
Papers Published
    ▲
120 │         ████
    │       ██████████
 80 │     ████████████████
    │   ████████████████████
 40 │ ████████████████████████
    │████████████████████████████
  0 └──────────────────────────────►
    Jan    Feb    Mar    Apr    May

    ■ cs.AI  ■ cs.LG  ■ cs.CL  ■ Other
```

### Features
- Granularity toggle: Day / Week / Month
- Hover tooltip: date, total count, per-category breakdown
- Click a date range to zoom in
- Category legend is clickable to toggle visibility
- Smooth animation on data change

### Component: `components/charts/PapersOverTimeChart.tsx`
- Uses Recharts `<AreaChart>` with `<Area>` per category
- Category colors from shared `categoryColors.ts`
- Responsive container

---

## Panel 2: Category Distribution (Treemap)

### Visualization
Treemap where each rectangle's area represents paper count for that category.

```
┌────────────────┬──────────┬──────┐
│                │          │cs.CV │
│    cs.AI       │  cs.LG   │  98  │
│    1,234       │   892    ├──────┤
│                │          │cs.RO │
├────────────────┤          │  45  │
│    cs.CL       ├──────────┴──────┤
│     567        │     Others      │
└────────────────┴─────────────────┘
```

### Features
- Color-coded by category (matching area chart)
- Hover: category name, paper count, percentage
- Click: filters all other panels to that category
- Animated transitions when filters change

### Component: `components/charts/CategoryTreemap.tsx`
- Uses Recharts `<Treemap>` with custom content renderer
- Shows label + count inside each rectangle
- Min rectangle size threshold (collapse tiny categories into "Other")

---

## Panel 3: Top Authors (Horizontal Bar Chart)

### Visualization
Top 20 most prolific authors as horizontal bars.

```
Yann LeCun       ████████████████████  45
Geoffrey Hinton   ██████████████████   42
Ilya Sutskever    ████████████████     38
Demis Hassabis    ██████████████       34
...
```

### Features
- Bars colored by primary category of author's papers
- Hover: author name, paper count, list of categories
- Click author: filters dashboard to their papers (or navigates to search with `author:Name`)
- Animated bar entrance (staggered, left-to-right grow)

### Component: `components/charts/TopAuthorsChart.tsx`
- Uses Recharts `<BarChart layout="vertical">`
- Author name on Y-axis, count on X-axis
- Truncate long names with ellipsis

---

## Panel 4: Citation Network (Force-Directed Graph)

### Visualization
Interactive force-directed graph showing citation relationships.

```
        ○ Paper A
       / \
      /   \
     ○     ○ Paper B
    / \     \
   ○   ○    ○ Paper C
```

### Features
- Nodes sized by citation count (larger = more cited)
- Node color by category
- Edges show citation direction (arrow)
- Hover node: show paper title, citation count
- Click node: center graph + expand connections (lazy load depth+1)
- Zoom + pan (mouse wheel, drag)
- "In library" papers have solid fill, external papers have outline only
- Search/filter within the graph
- Toggle: show labels on/off

### Component: `components/charts/CitationNetwork.tsx`
- Uses D3 force simulation (`d3-force`) rendered to SVG
- React manages state + D3 handles physics simulation
- Lazy loading: starts with a seed paper or top-cited papers, expands on interaction
- Performance: limit to 200 visible nodes, cluster distant nodes

### Starting Views
1. **Global view** — top 50 most-cited papers as nodes
2. **Paper-centric** — select a paper, show its citation neighborhood (depth 2)
3. **Category view** — one cluster per category, inter-category edges

---

## Panel 5: Pattern Trends (Stacked Area)

### Visualization
Shows how research pattern categories evolve over time.

```
Pattern Distribution Over Time
    ▲
    │    ░░░░░░░░░░░░░░░░░░░░░░░
    │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
    │ ████████████████████████████
    └──────────────────────────────►

    ■ Agent Planning  ■ Agent Memory  ■ Tool Use  ■ Other
```

### Features
- Week or month granularity
- Hover: date, total classified papers, per-category count
- Agentic ratio overlay (dashed line showing % agentic over time)
- Click category in legend to isolate it

### Component: `components/charts/PatternTrendsChart.tsx`
- Recharts `<AreaChart>` similar to papers-over-time
- Secondary Y-axis for agentic ratio percentage

---

## Panel 6: Agentic Research Gauge

### Visualization
Large gauge showing current agentic paper ratio + trend.

```
        ╭─────────╮
       ╱           ╲
      ╱    38.2%    ╲
     ╱   Agentic     ╲
     ╲               ╱
      ╲  ↑ 4.1% MoM ╱
       ╲           ╱
        ╰─────────╯
```

### Features
- Semi-circular gauge (0-100%)
- Color gradient: blue (low) → indigo (mid) → violet (high)
- Monthly trend indicator below
- Animate fill on load

### Component: `components/charts/AgenticGauge.tsx`
- Custom SVG arc with Framer Motion animation
- Percentage text centered

---

## Panel 7: Library Growth (Line Chart)

### Visualization
Cumulative papers bookmarked over time on the bookmarks page.

```
Your Library
    ▲
120 │                    ╱──
    │                ╱──╱
 80 │            ╱──╱
    │        ╱──╱
 40 │    ╱──╱
    │╱──╱
  0 └──────────────────────────►
    Jan    Feb    Mar    Apr
```

### Features
- Cumulative line (solid) + daily additions (bar below, subtle)
- Annotations: notable add dates (e.g., "Added 15 papers")
- Also appears as a small sparkline on the bookmarks page header

### Component: `components/charts/LibraryGrowthChart.tsx`
- Recharts `<ComposedChart>` with `<Line>` + `<Bar>`
- Placed both on analytics page and as mini version on bookmarks page

---

## Panel 8: Hot Categories Heatmap

### Visualization
Grid heatmap showing which categories are growing fastest week-over-week.

```
          W1    W2    W3    W4    W5
cs.AI    [ 🟩 ] [ 🟩 ] [ 🟨 ] [ 🟩 ] [ 🟥 ]
cs.LG    [ 🟨 ] [ 🟩 ] [ 🟩 ] [ 🟩 ] [ 🟩 ]
cs.CL    [ 🟥 ] [ 🟨 ] [ 🟩 ] [ 🟩 ] [ 🟩 ]
cs.CV    [ 🟩 ] [ 🟥 ] [ 🟥 ] [ 🟨 ] [ 🟩 ]
```

Colors represent week-over-week growth rate:
- Dark green: >50% growth
- Light green: 10-50% growth
- Yellow: ±10%
- Red: >10% decline

### Features
- Hover cell: exact count + growth percentage
- Click cell: filter papers to that category+week
- Row labels show current week count + trend arrow

### Component: `components/charts/CategoryHeatmap.tsx`
- Custom grid using Tailwind CSS grid
- Color computed client-side from papers-over-time data
- No additional backend endpoint needed (derived from papers-over-time response)

---

## Existing Analysis Page Migration

The current `/analysis` page shows citation rankings only. This content moves into Panel 4 (citation network) and a new "Top Citations" tab within the analytics dashboard. The `/analysis` route redirects to `/analytics`.

### Files
- Remove: `app/analysis/page.tsx` (replace with redirect)
- New: `app/analytics/page.tsx` — full analytics dashboard
- New: `app/analytics/layout.tsx` — analytics-specific layout (optional)

---

## Chart Component Architecture

All chart components follow a consistent pattern:

```tsx
interface ChartProps {
  data: DataType[];
  loading?: boolean;
  height?: number;
  onFilterChange?: (filter: FilterType) => void;
}

function Chart({ data, loading, height = 300, onFilterChange }: ChartProps) {
  if (loading) return <ChartSkeleton height={height} />;
  if (!data.length) return <EmptyState icon={BarChart3} message="..." />;
  return <ResponsiveContainer height={height}>...</ResponsiveContainer>;
}
```

### Shared Utilities
- `lib/categoryColors.ts` — consistent color mapping across all charts
- `lib/chartUtils.ts` — date formatting, number formatting (1,234 / 1.2K), granularity helpers
- `components/charts/ChartSkeleton.tsx` — loading skeleton for chart areas

---

## File Summary

### New Backend Files
- `backend/routers/analytics.py` — all aggregation endpoints
- Modified: `backend/main.py` — register analytics router

### New Frontend Files
- `app/analytics/page.tsx` — analytics dashboard page
- `components/charts/PapersOverTimeChart.tsx`
- `components/charts/CategoryTreemap.tsx`
- `components/charts/TopAuthorsChart.tsx`
- `components/charts/CitationNetwork.tsx`
- `components/charts/PatternTrendsChart.tsx`
- `components/charts/AgenticGauge.tsx`
- `components/charts/LibraryGrowthChart.tsx`
- `components/charts/CategoryHeatmap.tsx`
- `components/charts/ChartSkeleton.tsx`
- `lib/categoryColors.ts`
- `lib/chartUtils.ts`

### Modified Frontend Files
- `app/analysis/page.tsx` — redirect to `/analytics`
- `app/bookmarks/page.tsx` — mini library growth sparkline
- `components/Sidebar.tsx` — update "Analysis" nav to "Analytics" pointing to `/analytics`
- `components/DashboardContent.tsx` — mini sparkline in header
