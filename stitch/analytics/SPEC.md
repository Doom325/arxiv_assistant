# SPEC: Analytics Page
Date: 2026-03-28
Status: Approved

## Design Summary

The analytics page is a single-screen observatory layout with four major sections stacked vertically: a featured hero strip displaying key summary statistics on a deep forest-green surface (the ONE featured surface), a charts row with papers-over-time area chart and category distribution bar chart side-by-side, a filter bar for citation controls, and a ranked top-citations feed. The visual language is warm editorial: Newsreader serif for display headings, Inter sans-serif for body/UI, on the warm parchment (#F5F0E8) surface with tonal card steps.

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | PASS | Page surface is #F5F0E8. Cards use #EDE9E1. Inset areas use #E5E0D5. No cool greys. |
| One accent color on interactive elements only | PASS | Terracotta (#C4614A) used for active filter states, CTA buttons, chart accent fills. Not decorative. |
| One featured/deep surface per page | PASS | Hero stats strip uses #2A4A1A (deep forest green). No other dark/featured surfaces. |
| Mixed-weight serif headline | PASS | Page title uses Newsreader font-light "Research" + font-bold "Analytics". |
| No structural borders on cards/panels | PASS | Cards rely on tonal surface shift and shadow-warm. No border classes. |
| Generous whitespace | PASS | space-y-12 between major sections. p-8 card padding. Relaxed line heights. |
| Metadata labels uppercase with tracking | PASS | "TOTAL PAPERS", "TODAY", "YESTERDAY", "IN LIBRARY", category chips all use text-[10px] font-bold uppercase tracking-[0.08em]. |

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|----------|
| REQ-A01 | Total papers stat | Covered | Hero featured strip, first stat block. |
| REQ-A02 | Today/yesterday counts | Covered | Hero strip, second and third stat blocks with delta indicator. |
| REQ-A03 | Library count | Covered | Hero strip, fourth stat block. |
| REQ-A04 | Category count | Covered | Hero strip, fifth stat block. |
| REQ-A05 | Papers-over-time chart | Covered | Left chart card with AreaChart, granularity toggle (day/week/month). |
| REQ-A06 | Category distribution chart | Covered | Right chart card with horizontal BarChart, top categories sorted by count. |
| REQ-A07 | Warm palette charts | Covered | Chart fills use terracotta accent; grid uses surfaceInset; tooltip uses surfaceCard. |
| REQ-A08 | Top citations list | Covered | Ranked list below charts section with citation count, rank badge. |
| REQ-A09 | Citation entry details | Covered | Each row: rank number, citation count circle, title, arXiv ID chip, category chip, author line. |
| REQ-A10 | In-database distinction | Covered | "In Library" badge + accent CTA linking to /paper/[id]. |
| REQ-A11 | External arXiv link | Covered | "View on arXiv" secondary link for non-library papers. |
| REQ-A12 | Citation filters | Covered | Filter bar with category select + date range inputs above citation list. |
| REQ-A13 | Loading skeletons | Covered | Warm skeleton pulse animation using surface-card/surface-inset gradient. |
| REQ-A14 | Empty state | Covered | Centered illustration with warm tokens, guidance text. |

## Component Inventory

1. **AnalyticsHero** -- Full-width featured (forest-green) strip with 4-5 stat blocks: Total Papers, Today, Yesterday, Library, Categories. Each shows a large number + uppercase label. White text on featured surface.
2. **PapersOverTimeChart** -- Card containing a recharts AreaChart with day/week/month granularity toggle. Warm tooltip, terracotta fill, parchment grid.
3. **CategoryDistributionChart** -- Card containing a recharts horizontal BarChart of top categories. Same warm styling.
4. **CitationFilterBar** -- Horizontal bar with category dropdown and date range (From/To) inputs. Warm surface-inset background, no borders.
5. **CitationCard** -- Row card for each top-cited paper. Shows rank number, citation count in accent circle, title (Newsreader), arXiv ID chip, category chip, author line, and CTA button.
6. **AnalyticsEmptyState** -- Centered empty state with warm tokens and guidance message.
7. **AnalyticsPage** -- Orchestrator component that fetches all data and composes the above components.

## Open Questions

None -- all API endpoints exist and are verified in api.ts (getAnalyticsSummaryStats, getAnalyticsPapersOverTime, getAnalyticsCategoryDist, getTopCitations).
