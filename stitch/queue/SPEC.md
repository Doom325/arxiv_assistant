# SPEC: Reading Queue Page
Date: 2026-03-25
Stitch output: stitch/queue/screen.png

## Design Summary

Stitch produced a three-zone layout: a fixed left sidebar (navigation + "Trigger Scan" CTA), a wide main canvas (hero header, stat block, filter/sort bar, and a linear card list), and a fixed right quick-preview panel. The most distinctive visual choice is a deep forest-green hero stat block ("Recommended Next") that doubles as the featured surface, displaying a top-priority paper alongside four summary stat tiles. Queue items are rendered as large horizontal cards with inline read-status controls; a "Quick Preview" glass panel appears docked to the right for abstract and AI-summary inspection without leaving the page.

---

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | ✅ | `bg-background` (#fef9ef) and `surface-container-*` tokens are all warm cream tones; no pure white or cool grey on the page surface |
| One accent color on interactive elements only | ⚠ | Primary accent is terracotta/warm-red (`primary` #9b3f25) used correctly on interactive elements. However emerald green (`text-emerald-900`) appears on the "Scholar's Atelier" wordmark in the top bar — this is a second distinct accent-family color appearing on a non-interactive element, which conflicts with the one-accent principle |
| One featured/deep surface per page | ✅ | The forest-green hero stat block (`bg-secondary` #4d6453) is the single featured surface; no other deep/rich color surfaces appear |
| Mixed-weight serif headline | ✅ | Page headline uses Newsreader at `font-extralight` for "Your Reading" and `font-black italic` for "Queue" — correct mixed-weight technique |
| No structural borders on cards/panels | ⚠ | Queue cards use tonal shift correctly (no borders). However, the sidebar has an explicit `border-r border-stone-200/50` structural border, and the quick-preview panel uses `border border-white/40`. Sidebar border is minor but technically violates the no-structural-borders principle |
| Generous whitespace | ✅ | Main canvas uses `px-12`, `pt-32`, `pb-24`, `mb-16`, card internal `p-8`, and section gaps of `mb-10` / `mb-12` — consistently generous throughout |
| Metadata labels uppercase with tracking | ✅ | Group header "This Week" uses `uppercase tracking-[0.2em]`; priority badges use `uppercase tracking-wider`; stat tile labels use `uppercase tracking-widest`; sidebar footer links use `uppercase tracking-widest` — well applied throughout |

---

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|---------|
| REQ-031 | View reading queue aggregating discovered and bookmarked papers | Covered | Main list shows three cards; hero stat block tiles show "AI Discovered: 12" and "Manual Adds: 30" counts |
| REQ-032 | Filter by source (discovered vs. bookmarked) and read status | Partial | Source filter pill group shows "All Sources / JSTOR / ArXiv / Personal" — covers source filtering. Read-status filter is only present as a top-bar nav (Unread / Reading / Read / Skipped tabs) with no combined or multi-select filter UI; the `filter_list` icon button is present but its panel is not shown. Source options shown (JSTOR, ArXiv, Personal) do not map to the API values (discovered vs. bookmarked) |
| REQ-033 | Sort by priority score, publication date, or date added (asc/desc) | Partial | "Sort by: Priority" dropdown is present, accent-colored, indicating it is the active sort. Only one sort key is shown as active; the dropdown panel is not rendered so it is ambiguous whether date-added and publication-date options exist, and direction toggle is not shown |
| REQ-034 | Group by publication day, week, or month | Partial | A single group header "This Week" is shown, indicating grouping by week is active. There is no visible control for changing the grouping interval (day / week / month picker absent) |
| REQ-035 | Mark item as unread, reading, read, or skipped | Covered | Each card shows inline status buttons: "Unread", "Read", "Skipped" as pill buttons, plus a "Currently Reading" toggle (filled primary circle) on the active card and "Mark as Reading" affordance on others. All four statuses are reachable |
| REQ-036 | Manually override priority (high, medium, low, or auto) | Missing | Priority score is displayed as a badge (e.g. "Priority: 9.4") but there is no UI to override it. The `more_vert` overflow menu is present but its contents are not shown; cannot confirm priority override is accessible |
| REQ-037 | Remove a paper from the queue entirely | Missing | No delete / remove action is visible on any card. The `more_vert` overflow menu could house this, but it is not shown — no design evidence this capability is surfaced |
| REQ-038 | Rescore all queue items | Covered | "Recalculate Scores" button is present in the hero header, clearly labeled, with a refresh icon |
| REQ-039 | View queue statistics (counts, estimated reading time) | Partial | The hero stat block shows "AI Discovered: 12", "Manual Adds: 30", "Completion: 84%", and "Current Velocity: High". Missing: explicit high-priority count and estimated total reading time — two of the five statistics called for by the REQ |
| REQ-040 | Preview abstract and AI summary without leaving queue; navigate to adjacent items | Partial | Quick-preview panel shows abstract and "AI Key Takeaways" section. No navigation controls (prev/next arrows) for moving between adjacent queue items within the preview session are visible |
| REQ-012 | Trigger AI-powered paper discovery | Covered | "AI Scan" button in hero header and "Trigger Scan" button in sidebar both present |
| REQ-056 | Persistent navigation between all major sections | Covered | Fixed sidebar with Library, Queue (active), Collections, Archive links |
| REQ-057 | Global command palette via Cmd/Ctrl+K | Covered | Search bar in top bar shows `⌘K` keyboard hint; input field is present |
| REQ-058 | Keyboard navigation (j/k focus, Space to peek, b to bookmark) | Missing | No visible affordance or indicator for keyboard nav on the list. Shortcuts link exists in sidebar but the list itself shows no focus indicators or keyboard hints |
| REQ-059 | Two-key chord shortcuts (g then d/r/c/b/a/p/s) | Missing | No visible affordance. Shortcuts link exists but chord navigation is not indicated anywhere in the design |
| REQ-060 | View keyboard shortcut reference overlay | Covered | "Shortcuts" link in sidebar footer with keyboard icon is present |
| REQ-061 | Navigate to paper full detail view from listing | Covered | "Open Details" button on every card |
| REQ-064 | Open paper PDF in new tab | Missing | No "Open PDF" or external link affordance visible on cards or in the quick-preview panel |

**Summary: 7 Covered, 6 Partial, 5 Missing**

---

## Component Inventory

1. **Left Sidebar** — Fixed navigation rail with app title "The Atelier", nav links (Library, Queue active, Collections, Archive), "Trigger Scan" CTA button at bottom, and footer links for Shortcuts and Settings.

2. **Top App Bar** — Fixed header with "Scholar's Atelier" wordmark, inline read-status tab nav (Unread / Reading / Read / Skipped), search input with ⌘K hint, notifications bell, and user avatar.

3. **Hero Header** — Page title using mixed-weight serif headline ("Your Reading / Queue"), subtitle in italic serif, and two CTA buttons ("Recalculate Scores", "AI Scan").

4. **Featured Stat Block** — Deep forest-green panel (the single featured surface). Contains: "Focus Mode: Recommended Next" label, featured paper title, relevance score callout with estimated reading time, author/date metadata, "Start Reading" CTA, and a 2×2 grid of stat tiles (AI Discovered, Manual Adds, Completion, Current Velocity).

5. **Source Filter Pill Group** — Horizontal segmented control with "All Sources / JSTOR / ArXiv / Personal" tabs, pill-style with one active state.

6. **Sort + Filter Controls** — "Sort by: Priority" inline dropdown (accent-colored active state) and a filter icon button for an advanced filter panel (panel not shown).

7. **Group Header** — Small uppercase tracked label ("This Week") acting as a temporal section divider for the card list.

8. **Queue Item Card** — Horizontal card (tonal surface, no border) with: source type icon, paper title (hover → primary color), author/journal/date metadata in italic serif, priority score badge, overflow menu (`more_vert`), read-status inline toggle (play button for active, radio button for inactive), status pill buttons (Unread / Read / Skipped), "Open Details" pill button, and "Preview" pill button.

9. **Quick Preview Panel** — Fixed right glass panel (frosted, `backdrop-filter: blur`). Contains: "Quick Preview" badge, close button, paper title, author/year, Abstract section (body text), AI Key Takeaways section (numbered bullet list in italic, accent-colored numbering), and a "Begin Reading Session" full-width CTA button.

10. **Floating Action Button (FAB)** — Center-bottom fixed button, forest-green, labeled "Add New Research Item" with a bold plus icon.

11. **Load More / Pagination** — Italic serif text link at page bottom: "Discover more insights in the archive →".

---

## Open Questions

1. **More-vert overflow menu contents** — Three cards each have a `more_vert` icon, but the menu is never shown. It may be the intended home for priority override (REQ-036) and remove from queue (REQ-037). If so, the design needs at least one open-state mockup.

2. **Filter panel contents** — The `filter_list` icon button is present but its expanded state is not shown. Whether it handles the read-status multi-select or source "discovered vs. bookmarked" distinction is unresolved.

3. **Grouping control** — "This Week" implies week grouping is active, but there is no visible control to switch between day / week / month groupings. Where does this control live?

4. **Sort dropdown expanded state** — Only "Priority" is shown as active. The dropdown panel with other sort keys and direction (asc/desc) is not mocked.

5. **Adjacent item navigation in preview** — The quick-preview panel has no prev/next controls. How does the user move to the next item in the queue without closing the panel?

6. **PDF access** — No "Open PDF" affordance on cards or in the preview panel. Is it assumed to be in the full detail view only?

7. **Empty state** — No design for when the queue is empty (e.g., after all items are skipped or read).

8. **FAB vs. sidebar "Trigger Scan"** — The FAB says "Add New Research Item" while the sidebar button says "Trigger Scan". These appear to be different capabilities — is the FAB for manual bookmarking? If so, it should be mapped to a specific REQ.

9. **Source filter values mismatch** — The API uses `source=discovered|bookmarked` but the filter pills show JSTOR / ArXiv / Personal — these are content sources, not the API source categories. The design may be using a different taxonomy than the backend expects.

10. **Keyboard focus indicators** — No visual focus ring or list-item focus state is shown. j/k navigation requires a visible focused-item highlight design.

---

## Gaps — Resolution Log

**REQ-036 — Manual priority override** ✅ RESOLVED
- Design source: `priority_override_interaction/` — extract the popup pattern only (AI score badge + High/Medium/Low/Auto options + Revert to Automatic). Discard the page layout from that file.
- Trigger: clicking the priority badge on a queue card.

**REQ-037 — Remove from queue** ✅ RESOLVED
- "Remove from Queue" added to overflow (⋮) menu on each card. No Stitch needed.

**REQ-058 — Keyboard navigation (j/k / Space / b)** ✅ RESOLVED
- Resolve in implementation. Focused card state = visible ring, handled by ui-architect in design system.

**REQ-059 — Chord shortcuts** ✅ RESOLVED
- No visual change needed. Covered by Shortcuts link in sidebar (REQ-060).

**REQ-064 — PDF link** ✅ RESOLVED
- PDF access via full detail view only (Open Details → REQ-061). No affordance on queue cards.

**REQ-032 — Source filter** ✅ RESOLVED
- Keep provider-level filter (JSTOR / ArXiv / Personal / etc). Backend to support provider filtering.

**REQ-034 — Grouping control** ✅ RESOLVED
- Design source: `reading_queue_grouped_by_date/` — extract grouping concept (temporal section headers, Group by control). Discard the navigation from that file.
- Control placement: top-right of card list, adjacent to Sort.

**REQ-039 — Missing stats** ✅ RESOLVED
- Add high-priority count and estimated total reading time to the green stat block (6 stats total).

**REQ-040 — Preview navigation** ✅ RESOLVED
- Resolve in implementation. Add prev/next controls to quick-preview panel.
