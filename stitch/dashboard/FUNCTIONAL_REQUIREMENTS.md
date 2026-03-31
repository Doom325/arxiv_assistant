# Functional Requirements: Dashboard Page

The dashboard is the researcher's "morning briefing" -- the first screen they see.
It answers: what happened while I was away, what should I pay attention to, and how do I dive in?

---

## Domain: Discovery Feed

- REQ-D01: User can browse a continuously-loading feed of recently indexed AI research papers with title, categories, publication date, and abstract visible per item.
- REQ-D02: User can see papers organized chronologically by publication date, with clear date groupings that can be expanded or collapsed.
- REQ-D03: User can see a prominently featured "lead story" paper -- the most recent or most relevant paper -- with an extended preview including rendered abstract (with math support) and estimated reading time.
- REQ-D04: User can navigate from any paper in the feed to its full detail page.
- REQ-D05: User can trigger a manual refresh of the feed to surface newly indexed papers without a full page reload.
- REQ-D06: User can switch between a spatial (grid) layout and a compact (list) layout for the paper feed.
- REQ-D07: Feed loads additional papers automatically as the user scrolls (infinite scroll), with a visible loading indicator.
- REQ-D08: User's scroll position and loaded papers persist across in-session navigation so returning to the dashboard does not reset their place.

## Domain: Search and Filtering

- REQ-D09: User can perform a free-text search across all indexed papers directly from the dashboard.
- REQ-D10: User can filter the feed by arXiv category (cs.AI, cs.LG, cs.CL, cs.CV, cs.RO, cs.NE, cs.MA, cs.IR, cs.SI, cs.HC, cs.CY).
- REQ-D11: User can filter the feed by a publication date range (start and/or end date).
- REQ-D12: User can sort the feed by relevance, newest date, or title alphabetically.
- REQ-D13: User can reset all active filters and search terms to return to the default unfiltered view.
- REQ-D14: Active filters are reflected in the URL so filtered views can be shared or bookmarked.

## Domain: Activity Snapshot

- REQ-D15: User can see at a glance the total number of papers in the index for their primary category (cs.AI).
- REQ-D16: User can see how many papers were published yesterday in their primary category, with a directional trend indicator (up/flat/down).
- REQ-D17: User can see a sparkline or mini time-series chart showing the volume of papers per day over the past 14 days for their primary category.
- REQ-D18: User can see a proportional breakdown of papers by sub-category over the past 30 days, giving a sense of where research activity is concentrated.

## Domain: Quick Actions

- REQ-D19: User can bookmark any paper from the feed without leaving the dashboard.
- REQ-D20: User can open a quick-peek preview of any paper (title, abstract, AI summary, reading time) in a slide-over sheet without navigating away.
- REQ-D21: User can navigate between papers within the quick-peek sheet (previous/next) without closing it.
- REQ-D22: User can trigger an AI summary generation for a paper from within the quick-peek sheet and see the result inline when it completes.

## Domain: Keyboard Navigation

- REQ-D23: User can navigate the paper list with keyboard shortcuts (j/k to move focus between papers).
- REQ-D24: User can open the quick-peek preview of the focused paper using a keyboard shortcut (Space).
- REQ-D25: User can view a reference overlay listing all available keyboard shortcuts.

## Domain: Empty and Error States

- REQ-D26: When no papers exist in the index, the user sees a welcoming empty state that communicates readiness rather than failure, with guidance on how to populate the feed.
- REQ-D27: When a search returns no results, the user sees a specific "no results" state with an option to clear filters.
