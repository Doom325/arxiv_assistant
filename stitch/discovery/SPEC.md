# SPEC: Discovery / Search Page
Date: 2026-03-28
Stitch output: (designed inline by ui-architect — no external Stitch render)

## Design Summary

The Discovery/Search page is a scholarly search interface — a beautifully designed library catalog search. The page centers on a search hero with a large search input on a deep forest-green featured surface (the single featured surface), followed by a filter bar and a 3-column results grid of paper cards. The overall feel is calm, editorial, and focused on content discovery.

---

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | Pass | Page uses `#F5F0E8` (`bg-background`), cards `#EDE9E1` (`bg-surface-card`), insets `#E5E0D5` (`bg-surface-inset`). No pure white or cool grey. |
| One accent color on interactive elements only | Pass | Terracotta `#C4614A` on search button, links, active filters, bookmark icons. No decorative use. |
| One featured/deep surface per page | Pass | Forest green `#2A4A1A` search hero is the single featured surface. |
| Mixed-weight serif headline | Pass | Hero: "Search your" in Newsreader font-extralight, "research library" in Newsreader font-bold italic. |
| No structural borders on cards/panels | Pass | Cards use tonal shift + shadow-warm-sm. Filter bar uses bg-surface-card without borders. |
| Generous whitespace | Pass | `px-12`, `pt-8`, `pb-24`, card padding `p-5`, grid `gap-6`. |
| Metadata labels uppercase with tracking | Pass | Category chips, "SEARCH OPERATORS" hint label, filter labels all uppercase tracking. |

---

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|---------|
| REQ-S01 | Semantic search | Covered | Large search input on featured hero surface, search button |
| REQ-S02 | Responsive results grid | Covered | 3-column grid using grid-cols-1 md:grid-cols-2 lg:grid-cols-3 |
| REQ-S03 | Card content | Covered | Category chip, title, abstract, date, reading time, PDF link, details link |
| REQ-S04 | Sort by relevance/date | Covered | Sort dropdown in filter bar |
| REQ-S05 | URL sync | Covered | useSearchParams preserves ?q= parameter |
| REQ-S06 | Category filter | Covered | Category dropdown in filter bar |
| REQ-S07 | Date range filter | Covered | Start date and end date inputs in filter bar |
| REQ-S08 | Operator hints | Covered | Small operator hint chips below search input on hero |
| REQ-S09 | Navigate to detail | Covered | "Full Details" accent link on each card |
| REQ-S10 | Bookmark toggle | Covered | BookmarkButton on each card |
| REQ-S11 | Add to queue | Covered | Queue icon button on each card |
| REQ-S12 | Open PDF | Covered | "Read PDF" accent link on each card |
| REQ-S13 | Loading skeleton | Covered | Warm SkeletonGrid with skeleton utility class |
| REQ-S14 | Empty/hero state | Covered | Hero search surface shown before first search |
| REQ-S15 | No-results state | Covered | Editorial serif empty state with operator hints |
| REQ-S16 | Error state | Covered | Error message with retry button |
| REQ-S17 | Keyboard focus | Covered | autoFocus on search input |
| REQ-S18 | Responsive layout | Covered | grid-cols-1 / md:grid-cols-2 / lg:grid-cols-3 |

**Summary: 18 Covered, 0 Partial, 0 Missing**

---

## Component Inventory

1. **Search Hero** (featured surface) — Deep forest green panel (`bg-surface-featured`). Contains: "DISCOVER" uppercase tracked label, mixed-weight Newsreader headline ("Search your / research library"), italic Newsreader subtitle, large search input (white bg, warm shadow, accent focus ring), search button (accent bg), and operator hint chips below the input.

2. **Search Filter Bar** — Horizontal bar on `bg-surface-card` surface. Contains: category dropdown, date range inputs (start/end), sort dropdown (Relevance/Date), and a clear-filters button. All inputs use `bg-surface-inset` backgrounds with warm focus rings.

3. **Search Result Card** — `bg-surface-card rounded-2xl p-5 shadow-warm-sm`. Category chip (pill-shaped, uppercase tracking), paper title (Inter semibold, hover accent), abstract line-clamp-3, published date + reading time metadata, "Read PDF" and "Full Details" accent links, BookmarkButton, queue add button. Left accent bar using category color.

4. **Search Skeleton Grid** — Warm skeleton cards (3-column grid) using existing `.skeleton` CSS utility class with warm surface tokens.

5. **No-Results State** — Editorial serif "No results" in Newsreader font-light, "found." in Newsreader font-bold italic. Subtitle with search tips in italic. Operator hint list. Warm surface, dashed border.

6. **Error State** — Warm card surface with AlertCircle icon, error message, "Try Again" accent button.

---

## Escalations

### E-S01 — Category Filter Options
**Issue:** Categories must come from somewhere — hardcoded list vs API call.
**Resolution:** Option A — use hardcoded list from categoryColorMap keys in lib/categoryColors.ts. Simplest and most robust. The category list is stable and already defined.

### E-S02 — Sort Direction Toggle
**Issue:** Sort by date could be ascending or descending.
**Resolution:** Option A — single dropdown with combined options ("Date: Newest", "Date: Oldest", "Relevance"). Simplest UI, no separate direction toggle needed.

### E-S03 — Search Input Placement
**Issue:** Hero search input vs persistent top-bar search.
**Resolution:** Option A — hero-only search input. The research page is the search destination; CommandPalette handles quick nav search. No duplicate search bar needed.

---

## Gaps — Resolution Log

**REQ-S11 — Add to queue button** Resolved: Small icon button (ListPlus) adjacent to bookmark, same pattern as LibraryPaperCard (E-019 from library spec).

**REQ-S16 — Error state** Resolved: Warm card surface with error message and retry button. No Stitch needed; follows warm token pattern.
