# Frontend Major Upgrade — High-Level Plan

## Vision

Transform arxiv_assistant from a functional research tool into an engaging, fast, visually rich experience that minimizes friction for every interaction and surfaces meaningful insights through analytics.

## Three Pillars

### 1. Engaging Visual Experience
**Goal:** Make the UI feel alive, polished, and delightful to use.

| Area | Current State | Target State |
|------|--------------|--------------|
| Page transitions | None — hard cuts between routes | Smooth cross-fade/slide transitions between pages |
| Card interactions | Basic hover border color change | Staggered entrance animations, hover lift with shadow, skeleton loading |
| Loading states | Spinner or pulse placeholders | Shimmer skeletons matching content shape, progress indicators |
| Data visualization | Plain text lists for citations/patterns | Charts, sparklines, heatmaps, network graphs |
| Paper cards | Dense text blocks | Visual hierarchy with category color coding, reading-time estimate, relevance score indicator |
| Chat interface | Basic message bubbles | Typing indicator, streaming text reveal, source cards with thumbnails |
| Empty states | Plain text messages | Illustrated empty states with suggested actions |
| Micro-interactions | Minimal | Bookmark burst animation, toast slide-in, button ripple effects |

**Detailed plan:** [claude_fe_engagement.md](claude_fe_engagement.md)

---

### 2. Action-Oriented UX — Reduce Friction
**Goal:** Every common action should be reachable in ≤2 clicks or one keyboard shortcut.

| Area | Current State | Target State |
|------|--------------|--------------|
| Search | Navigate to Research page, type, submit | Global command palette (⌘K) from any page, instant results |
| Bookmarking | Click bookmark icon → dropdown → select list | One-click default bookmark, drag-to-list, batch select |
| Filtering | Separate dropdowns, manual date entry | Inline filter chips, quick presets (Today, This Week, This Month), faceted sidebar |
| Paper actions | Scattered across UI | Contextual action bar on hover/select (bookmark, email, summarize, PDF) |
| Navigation | Sidebar links only | Keyboard shortcuts for all pages (g+d = dashboard, g+r = research, etc.) |
| Batch operations | Add to queue one-by-one | Multi-select with shift-click, batch summarize/bookmark/export |
| Paper detail | Full page navigation required | Quick-peek modal from any paper list (spacebar to preview) |
| Add paper | Sidebar mini-form | Paste arXiv URL anywhere, auto-detect and prompt to add |

**Detailed plan:** [claude_fe_actions.md](claude_fe_actions.md)

---

### 3. Analytics Views
**Goal:** Surface trends and insights from the paper library to guide research decisions.

| View | Data Source | Visualization |
|------|------------|---------------|
| Papers over time | `papers.published_date` grouped by day/week/month | Area chart with category color stacking |
| Category distribution | `papers.category` counts | Treemap or sunburst chart |
| Top authors | `papers.authors` JSON flattened | Ranked bar chart, clickable to filter |
| Citation network | `citation_links` table | Force-directed graph (D3) with node sizing by citation count |
| Pattern trends | `pattern_experiment_results` over time | Stacked area chart by pattern category |
| Agentic vs non-agentic | `pattern_experiment_results.is_agentic` | Ratio gauge + trend line |
| Embedding quality | `paper_embeddings` metadata | Scatter plot of paper clusters (UMAP/t-SNE projection) |
| Research velocity | Papers ingested per day | Sparkline in dashboard header |
| Your library growth | `user_library.added_at` | Cumulative line chart on bookmarks page |
| Hot categories | Category growth rate (week-over-week) | Heatmap grid with trend arrows |

**Detailed plan:** [claude_fe_analytics.md](claude_fe_analytics.md)

---

## Technical Approach

### New Dependencies
```
framer-motion          # Animations, page transitions, layout animations
recharts               # Charts (area, bar, line, treemap) — React-native, lightweight
d3 + @types/d3         # Force-directed citation graph only
cmdk                   # Command palette (⌘K)
sonner                 # Toast notifications (replaces custom alerts)
```

### No New Dependencies Needed
- Tailwind CSS v4 already supports transitions/transforms
- lucide-react already provides all needed icons
- react-intersection-observer already present for scroll detection

### Architecture Decisions
- **Animations:** Framer Motion for declarative animation — works with React 19 and App Router
- **Charts:** Recharts for standard charts (lightweight, React-based), D3 only for the citation force graph
- **Command palette:** cmdk is 3KB, accessible, keyboard-first
- **State:** Continue using React context + URL params — no Redux needed
- **API:** All analytics data can be derived from existing endpoints or simple new aggregation endpoints

### New Backend Endpoints Needed
```
GET /analytics/papers-over-time?granularity=day|week|month&category=...&start=...&end=...
GET /analytics/category-distribution?start=...&end=...
GET /analytics/top-authors?limit=20&category=...
GET /analytics/pattern-trends?granularity=week&start=...&end=...
GET /citations/network?paper_id=...&depth=2
```

### Implementation Order

**Phase 1 — Foundation (animations + command palette)**
1. Install framer-motion, cmdk, sonner
2. Add page transition wrapper in layout.tsx
3. Build command palette (⌘K) with search integration
4. Replace alert toasts with sonner
5. Add card entrance animations + hover effects

**Phase 2 — Action-Oriented UX**
6. Quick-peek paper modal (spacebar preview)
7. Inline filter chips + presets on dashboard
8. Keyboard shortcuts system (g+d, g+r, etc.)
9. Batch selection + bulk actions
10. One-click bookmark default behavior

**Phase 3 — Analytics**
11. Add backend aggregation endpoints
12. Build analytics dashboard page with recharts
13. Papers-over-time area chart
14. Category distribution treemap
15. Citation network force graph (D3)
16. Pattern trends + agentic ratio views

**Phase 4 — Polish**
17. Skeleton loading for all pages
18. Empty state illustrations
19. Chat streaming text reveal
20. Mobile gesture support
21. Performance audit (bundle size, lazy loading)

---

## Files Affected

### New Files
- `components/CommandPalette.tsx` — Global ⌘K search
- `components/QuickPeek.tsx` — Paper preview modal
- `components/FilterChips.tsx` — Inline filter system
- `components/charts/` — Chart components (PapersOverTime, CategoryTree, CitationGraph, PatternTrends, etc.)
- `components/animations/` — Reusable animation wrappers (FadeIn, StaggerList, PageTransition)
- `components/SkeletonCard.tsx` — Loading skeleton for paper cards
- `app/analytics/page.tsx` — New analytics dashboard (replaces basic analysis page)
- `lib/keyboard.ts` — Keyboard shortcut manager
- `lib/animations.ts` — Shared animation variants

### Modified Files
- `app/layout.tsx` — Add AnimatePresence, CommandPalette, Toaster
- `components/DashboardContent.tsx` — Filter chips, batch select, animations
- `components/PaperCard.tsx` — Hover effects, action bar, selection state
- `components/Sidebar.tsx` — Keyboard shortcut hints
- `components/BookmarkButton.tsx` — One-click default + animation
- `app/chat/page.tsx` — Streaming text, improved source cards
- `app/bookmarks/page.tsx` — Batch operations, drag-to-list
- `app/research/page.tsx` — Unified with command palette search
- All page.tsx files — Page transition wrappers
