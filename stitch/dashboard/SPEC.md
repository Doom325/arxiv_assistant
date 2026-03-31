# SPEC: Dashboard Page
Date: 2026-03-26
Stitch outputs: stitch/dashboard/dashboard/screen.png, stitch/dashboard/quick_peek_view/screen.png

## Design Summary

The dashboard is a two-screen design: a main feed view with sidebar navigation, hero lead story, activity stats, filter bar, and chronological paper cards; and a slide-over quick-peek panel showing a paper's abstract, AI synthesis findings, metadata, and prev/next navigation. The visual language is editorial and warm, using Newsreader serif for headlines and Inter sans-serif for body/UI, on a cream (#FEF9EF) surface with a deep forest-green hero section as the single featured surface.

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | :white_check_mark: | Page surface is #FEF9EF (warm cream). Card surfaces use tonal steps (#F8F3E9, #F2EDE3). No cool greys. |
| One accent color on interactive elements only | :white_check_mark: | Secondary (#A03F30, terracotta/warm red) is used consistently for CTAs, hover states, active indicators, and the "Reset" filter link. Not used decoratively. |
| One featured/deep surface per page | :white_check_mark: | Main screen: hero section uses primary-container (#1B3022, deep forest green). Quick-peek: the AI Synthesis Findings block uses the same deep green. Since these are two states of the same page, this is one featured surface at a time. |
| Mixed-weight serif headline | :white_check_mark: | Hero headline uses "Analysis of" in font-light and "Emergent Reasoning in Large Language Models" in font-bold, both in Newsreader. Quick-peek repeats this pattern with extralight italic + bold. |
| No structural borders on cards/panels | :warning: | Mostly clean -- cards rely on tonal shift and editorial-shadow. However, the filter bar buttons use `border border-outline-variant/15` and the category chips in the hero use `border border-on-primary-container/10`. These are very faint and stylistic, but technically structural borders. The quick-peek metadata grid uses a `gap-px bg-outline-variant/10` technique that simulates thin borders between cells. |
| Generous whitespace | :white_check_mark: | Section spacing is 48px (space-y-12). Card padding is 32px (p-8). Grid gaps are 32px (gap-8). Line heights are relaxed. The layout breathes well. |
| Metadata labels uppercase with tracking | :white_check_mark: | Consistently applied: "LEAD STORY", "TOTAL IN LIBRARY", "PULSE SCORE", category tags, "FILTER BY", "24 NEW PAPERS", date labels, reading time -- all use text-[10px] font-bold uppercase tracking-widest. |

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|----------|
| REQ-D01 | Browse feed with title, categories, date, abstract | Covered | Paper cards show title, category chip, abstract snippet, reading time. Date visible in section headers. |
| REQ-D02 | Chronological grouping, expandable/collapsible | Partial | "Today" and "Yesterday" date groups are present. No expand/collapse affordance visible. |
| REQ-D03 | Featured lead story with abstract + reading time | Covered | Hero section shows lead story with rendered abstract snippet, "12 min read", category tags, and "Read Full Analysis" CTA. |
| REQ-D04 | Navigate from feed to detail page | Covered | Paper cards are clickable (cursor-pointer, hover states). "Read Full Analysis" link on hero. Quick-peek has "Generate Full Deep Analysis" button. |
| REQ-D05 | Manual refresh without full reload | Covered | Refresh icon button in top app bar header. |
| REQ-D06 | Grid/list layout toggle | Covered | Grid/list toggle buttons visible in filter bar (grid_view / view_list icons). |
| REQ-D07 | Infinite scroll with loading indicator | Covered | "Fetching deeper archives..." loading indicator with progress bar at bottom of feed. |
| REQ-D08 | Scroll position persists across navigation | Missing | No visible UI element; this is a runtime behavior. Cannot verify from static design. Will need implementation-level handling. |
| REQ-D09 | Free-text search | Covered | Search input with icon in top app bar: "Search the archives..." |
| REQ-D10 | Filter by arXiv category | Partial | "All Categories" filter button exists. The sidebar shows cs.AI, cs.LG, cs.CL, cs.CV. The full list of 11 categories (cs.RO, cs.NE, cs.MA, cs.IR, cs.SI, cs.HC, cs.CY) is not shown -- presumably behind the dropdown. |
| REQ-D11 | Filter by date range | Partial | "Last 7 Days" button is visible but this is a preset, not a start/end date range picker. No calendar or date input is shown. |
| REQ-D12 | Sort by relevance, newest, title | Partial | "Most Relevant" sort button exists. No visible way to switch between relevance/newest/title options. |
| REQ-D13 | Reset all filters | Covered | "Reset" text button in filter bar with secondary color. |
| REQ-D14 | Filters reflected in URL | Missing | No visible UI element; this is a runtime behavior. Cannot verify from static design. |
| REQ-D15 | Total papers in index for primary category | Covered | "Total in Library: 12,842" stat card with trend indicator. |
| REQ-D16 | Yesterday's paper count with trend | Covered | "+412 vs last week" with trending_up icon on the total library card. |
| REQ-D17 | Sparkline / mini time-series (14 days) | Missing | The "Category Distribution" chart is a bar chart showing 30-day category breakdown, not a per-day time-series for the primary category. No sparkline is present. |
| REQ-D18 | Proportional breakdown by sub-category (30 days) | Covered | "Category Distribution" bar chart with 5 category bars (AI, LG, CL, CV, GR) labeled "Last 30 days of research activity." |
| REQ-D19 | Bookmark from feed | Covered | Bookmark icon on every paper card. Second card shows filled bookmark state. |
| REQ-D20 | Quick-peek slide-over preview | Covered | Quick-peek panel shows title, abstract, AI synthesis, reading time, category tags, metadata grid. Slide-over with backdrop blur dimming the main feed. |
| REQ-D21 | Navigate prev/next within quick-peek | Covered | Footer with "Previous Paper: Latent Space Mapping" and "Next Paper: Graph Neural Origins" with arrow icons. |
| REQ-D22 | Trigger AI summary from quick-peek | Covered | "Generate Full Deep Analysis" button in AI synthesis section. Pre-populated synthesis findings are also shown inline. |
| REQ-D23 | Keyboard nav (j/k) between papers | Partial | Keyboard shortcuts overlay lists "Next Paper: J" but no "K" for previous paper is shown. No visible focus ring state on paper cards. |
| REQ-D24 | Space to open quick-peek | Missing | The shortcuts overlay lists Search(/), Bookmark(B), Analyze(A), Next Paper(J) -- Space for quick-peek is not listed. |
| REQ-D25 | Keyboard shortcuts reference overlay | Covered | Floating button (keyboard_command_key icon) at bottom-right reveals shortcuts overlay on hover. |
| REQ-D26 | Empty state (no papers) | Missing | No empty state screen is designed. |
| REQ-D27 | No-results search state | Missing | No "no results" state is designed. |

## Component Inventory

1. **SideNavBar** -- Fixed left sidebar with app branding, "New Analysis" CTA, category navigation links (cs.AI, cs.LG, cs.CL, cs.CV, Bookmarks, Archive), and footer shortcuts/support links.
2. **TopAppBar** -- Fixed top header with search input, refresh button, notifications button, settings button, and user profile avatar.
3. **HeroLeadStory** -- Full-width dark-surface card featuring the top paper with mixed-weight headline, abstract excerpt, "Read Full Analysis" CTA, and category chips.
4. **CategoryDistributionChart** -- Bar chart showing paper volume by arXiv sub-category over 30 days, with hover interaction.
5. **TotalLibraryStat** -- Warm tertiary-toned stat card showing total indexed papers with weekly trend delta.
6. **PulseScoreStat** -- Circular gauge-style stat card displaying a research activity pulse score.
7. **FilterBar** -- Horizontal bar with category dropdown, date preset, sort selector, reset button, and grid/list layout toggle.
8. **DateGroupHeader** -- Section divider with date label (e.g., "Today March 25") and new paper count badge.
9. **PaperCardLarge** -- Two-column card with category chip, bookmark toggle, title, abstract snippet, author avatars, and reading time.
10. **PaperCardCompact** -- Smaller card used in 3-column yesterday grid, showing category+topic label, title, and status badge.
11. **InfiniteScrollIndicator** -- Progress bar and italic message at bottom of feed indicating more content loading.
12. **KeyboardShortcutsOverlay** -- Floating action button that reveals a hover tooltip listing keyboard shortcuts.
13. **QuickPeekPanel** -- Slide-over sheet with header (Deep Work Peek label + close button), category chips, mixed-weight headline, date/reading-time metadata, hero image, abstract with drop cap, AI synthesis findings section, metadata detail grid, and prev/next paper footer navigation.
14. **AISynthesisCard** -- Dark featured surface within quick-peek showing bullet-point synthesis findings and "Generate Full Deep Analysis" CTA.
15. **MetadataDetailGrid** -- 2x2 grid in quick-peek showing Author, Institution, Citations, and Peer Review status with uppercase labels.
16. **PaperNavigationFooter** -- Sticky footer in quick-peek with previous/next paper buttons showing paper titles.

## Open Questions

1. **Date group expand/collapse (REQ-D02):** The design shows "Today" and "Yesterday" groups but no toggle affordance. Should groups be collapsible, or is the chronological layout sufficient?
2. **Category filter interaction:** Does "All Categories" open a dropdown, a popover with checkboxes, or a full filter panel? The design shows a button but not the opened state.
3. **Date range picker (REQ-D11):** The design only shows a "Last 7 Days" preset. How does the user select an arbitrary date range?
4. **Sort options (REQ-D12):** Only "Most Relevant" is visible. Is this a dropdown? Where are "Newest" and "Title A-Z" options?
5. **Pulse Score meaning:** What does the 8.4 pulse score represent? Is there a tooltip or explanation?
6. **Quick-peek trigger:** How is the quick-peek opened from the main feed? Click? Keyboard? Hover? No explicit trigger is shown on paper cards.
7. **Scroll position persistence (REQ-D08):** This is an implementation concern with no visual representation -- needs an implementation plan.
8. **URL-synced filters (REQ-D14):** Also an implementation concern with no visual representation.
9. **Math rendering in abstracts (REQ-D03):** The lead story mentions "rendered abstract with math support" but the sample text has no math. KaTeX/MathJax integration needed?
10. **Quick-peek on hero vs. feed cards:** Does the hero's "Read Full Analysis" go to a detail page, or does it open a quick-peek? The interaction model between hero CTA and quick-peek is unclear.

## Gaps Requiring Resolution

1. **REQ-D17 (sparkline/time-series):** No per-day time-series chart exists. The category distribution chart covers sub-category breakdown (REQ-D18) but not daily volume. Decision needed: add a sparkline to the stats area, fold into the existing chart, or descope.
2. **REQ-D24 (Space to open quick-peek):** The keyboard shortcut for opening quick-peek is not listed in the shortcuts overlay. Needs to be added.
3. **REQ-D26 (empty state):** No empty state screen was designed. Needs either a Stitch pass or implementation-time design.
4. **REQ-D27 (no-results state):** No search-no-results state was designed. Needs either a Stitch pass or implementation-time design.
5. **REQ-D11 (date range):** Only a preset button is shown. A date picker or range input needs to be designed or the requirement needs to be narrowed to presets only.
