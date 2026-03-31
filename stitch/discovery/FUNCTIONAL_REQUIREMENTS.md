# Functional Requirements: Discovery / Search Page

## Core Search
- **REQ-S01** Semantic search across all indexed papers via search query input
- **REQ-S02** Display search results in a responsive grid (1/2/3 columns)
- **REQ-S03** Each result card shows: category, title, abstract snippet, published date, reading time, PDF link, detail link
- **REQ-S04** Sort results by: relevance (default), publication date
- **REQ-S05** URL sync: persist search query in URL query parameter (?q=) for shareability and browser back

## Filters
- **REQ-S06** Filter by category (dropdown or pill selection from known categories)
- **REQ-S07** Filter by date range (start date, end date)
- **REQ-S08** Structured search operators (category:cs.AI, after:2024, author:Name) shown as hints

## Paper Actions
- **REQ-S09** Navigate to paper detail page from result card
- **REQ-S10** Toggle bookmark from result card via BookmarkButton
- **REQ-S11** Add paper to reading queue from result card
- **REQ-S12** Open paper PDF in new tab

## States
- **REQ-S13** Loading state with warm skeleton grid
- **REQ-S14** Empty state (no search yet): hero search surface with prompt suggestions
- **REQ-S15** No-results state with helpful messaging and operator hints
- **REQ-S16** Error state with retry affordance

## Cross-cutting
- **REQ-S17** Keyboard shortcut: focus search input on page load or via shortcut
- **REQ-S18** Responsive layout: single column on mobile, 2-col on tablet, 3-col on desktop
