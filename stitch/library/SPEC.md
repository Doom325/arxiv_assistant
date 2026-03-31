# SPEC: Library / Bookmarks Page
Date: 2026-03-28
Stitch output: stitch/library/library/code.html

## Design Summary

Stitch produced a clean collection-management layout: a deep forest-green hero header with library stats, horizontal list pills as a tab-style filter, a 3-column paper card grid, and warm editorial empty/auth states. The page feels like a personal research shelf — organized, warm, uncluttered.

---

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | ✅ | Page uses `#F5F0E8`, cards `#EDE9E1`, insets `#E5E0D5`. No pure white or cool grey. |
| One accent color on interactive elements only | ✅ | Terracotta `#C4614A` on active list pill, bookmark icons, CTAs, links. No decorative use. |
| One featured/deep surface per page | ✅ | Forest green `#2A4A1A` hero header is the single featured surface. |
| Mixed-weight serif headline | ✅ | Hero: "Your personal" in light italic, "research library." in bold. Newsreader. |
| No structural borders on cards/panels | ✅ | Cards use tonal shift + shadow-warm-sm. No border-* classes. |
| Generous whitespace | ✅ | `px-12`, `py-8`, card padding `p-5`, grid `gap-6`. |
| Metadata labels uppercase with tracking | ✅ | "YOUR LIBRARY" label, category chips, list badges all uppercase tracking. |

---

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|---------|
| REQ-L01 | Paper grid | Covered | 3-column responsive grid with 6 sample cards |
| REQ-L02 | Filter by list | Covered | Horizontal pill tabs: "All", "AI Research", "Transformers" |
| REQ-L03 | Sort papers | Covered | "Sort by: Date Added" dropdown present |
| REQ-L04 | Card content | Covered | Category chip, title, abstract, reading time, list badges on each card |
| REQ-L05 | Create list | Covered | "+ New List" pill button present |
| REQ-L06 | Delete list | Partial | Trash icon visible when list selected; confirmation is runtime |
| REQ-L07 | List pill tabs | Covered | Horizontal scrollable pills with active/inactive states |
| REQ-L08 | List badges | Covered | Accent-tinted pills on cards showing list membership |
| REQ-L09 | Navigate to detail | Covered | "Full Details →" link on each card |
| REQ-L10 | Bookmark toggle | Covered | Filled bookmark icon on each card |
| REQ-L11 | Add to queue | Missing | No queue button visible on cards |
| REQ-L12 | Export to Drive | Covered | "Sync to Drive" button when list selected |
| REQ-L13 | OAuth flow | Covered | Auth panel with steps, code input, "Complete Auth" button |
| REQ-L14 | Export status | Partial | Alert banner present; animation states runtime |
| REQ-L15 | Loading state | Missing | Not shown in static mock |
| REQ-L16 | Empty state | Covered | Editorial serif "Your library / awaits." with CTA |
| REQ-L17 | Empty list state | Partial | Generic empty state; list-specific message runtime |

**Summary: 12 Covered, 3 Partial, 2 Missing**

---

## Component Inventory

1. **Library Hero Header** (featured surface) — Deep forest green panel with "YOUR LIBRARY" label, mixed-weight Newsreader headline, subtitle with paper/list counts, stats row.

2. **List Pill Tabs** — Horizontal scrollable row. Active pill: `bg-accent text-on-accent rounded-full`. Inactive: `bg-surface-inset text-foreground-muted rounded-full`. "+ New List" pill with accent dashed border.

3. **Control Bar** — Sort dropdown in same row as list pills. "Sync to Drive" and trash button appear when specific list selected.

4. **Library Paper Card** — `bg-surface-card rounded-2xl p-5 shadow-warm-sm`. Category chip, list membership badges (accent/10 tint), title link, abstract line-clamp-3, reading time, "Full Details →" accent link, bookmark icon.

5. **Empty State** — Editorial serif "Your library / awaits." with italic subtitle and "Browse Papers" accent CTA.

6. **Google Drive Auth Panel** — Card surface with Cloud icon, numbered steps, auth code input (`bg-surface-inset rounded-xl`), "Complete Auth" accent button.

7. **Export Status Banner** — Success (green tint) / error (red tint) alert with dismiss button.

---

## Escalations

### E-001 — List Pill Overflow
**Issue:** When many lists exist, the pill row could overflow horizontally.
**Options:**
- A) Horizontal scroll with overflow-x-auto and scroll-snap
- B) Wrap to multiple rows
- C) Dropdown instead of pills when > 5 lists
**Recommendation:** A — scroll with fade edges, keeps UI compact

### E-002 — Add-to-Queue on Library Cards
**Issue:** REQ-L11 (add to queue) has no visible button in the Stitch design.
**Options:**
- A) Add a small "+" icon button on each card for queue addition
- B) Include it in a card overflow menu (three-dot)
- C) Skip — users can add to queue from paper detail page
**Recommendation:** A — small icon button next to bookmark

### E-003 — PaperCard Reuse vs New Component
**Issue:** The existing PaperCard component is heavily dark-themed. The library page needs warm cards.
**Options:**
- A) Create a new LibraryPaperCard component (clean warm implementation)
- B) Restyle existing PaperCard with warm tokens
- C) Reuse DashboardPaperCard from Phase 9
**Recommendation:** A — LibraryPaperCard is cleanest since it needs list badges and bookmark management
