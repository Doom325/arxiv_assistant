# Detailed Plan: Action-Oriented UX — Reduce Friction

## 1. Global Command Palette (⌘K)

### Design
A spotlight-style overlay accessible from any page via `⌘K` (Mac) / `Ctrl+K` (Windows).

```
┌──────────────────────────────────────────┐
│  🔍  Search papers, commands, pages...   │
│─────────────────────────────────────────-│
│  Recent                                  │
│    ○ Attention Is All You Need           │
│    ○ GPT-4 Technical Report              │
│                                          │
│  Pages                                   │
│    → Dashboard                     g d   │
│    → Research                      g r   │
│    → Bookmarks                     g b   │
│    → Analytics                     g a   │
│    → Chat                          g c   │
│                                          │
│  Actions                                 │
│    ⊕ Add paper by arXiv ID        g n   │
│    ⚡ Quick search                 /     │
│─────────────────────────────────────────-│
│  ↑↓ Navigate  ⏎ Select  esc Close       │
└──────────────────────────────────────────┘
```

### Behavior
- **Typing text** → live search against `/papers/search` with debounce (300ms)
- **Arrow keys** → navigate results
- **Enter** → open paper detail or execute action
- **Escape** → close
- **Results grouped:** Recent papers, search results, pages, actions
- **Paper results show:** title, category badge, date

### Implementation
Use `cmdk` library (3KB, accessible, works with React 19):
```tsx
<CommandDialog open={open} onOpenChange={setOpen}>
  <CommandInput placeholder="Search papers, commands..." />
  <CommandList>
    <CommandGroup heading="Recent">...</CommandGroup>
    <CommandGroup heading="Results">...</CommandGroup>
    <CommandGroup heading="Pages">...</CommandGroup>
    <CommandGroup heading="Actions">...</CommandGroup>
  </CommandList>
</CommandDialog>
```

### Files
- New: `components/CommandPalette.tsx`
- Modified: `app/layout.tsx` — mount CommandPalette + keyboard listener
- Modified: `lib/api.ts` — add lightweight search method (limit=8, minimal fields)

---

## 2. Keyboard Shortcuts System

### Global Shortcuts
| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open command palette |
| `g` then `d` | Go to Dashboard |
| `g` then `r` | Go to Research |
| `g` then `b` | Go to Bookmarks |
| `g` then `a` | Go to Analytics |
| `g` then `c` | Go to Chat |
| `g` then `s` | Go to Settings |
| `g` then `n` | Add new paper (focus input) |
| `/` | Focus search input (on pages with search) |
| `?` | Show keyboard shortcuts help modal |

### Paper List Shortcuts (when on dashboard/research/bookmarks)
| Shortcut | Action |
|----------|--------|
| `j` / `k` | Move selection down/up through papers |
| `Enter` | Open selected paper |
| `Space` | Quick-peek selected paper (modal) |
| `b` | Toggle bookmark on selected paper |
| `e` | Email summary of selected paper |
| `x` | Toggle multi-select on current paper |
| `Escape` | Clear selection / close modal |

### Paper Detail Shortcuts
| Shortcut | Action |
|----------|--------|
| `b` | Toggle bookmark |
| `p` | Open PDF |
| `s` | Scroll to similar papers |
| `Escape` / `Backspace` | Go back |

### Implementation
Custom hook `useKeyboardShortcuts` that:
- Registers global key listeners
- Supports chord sequences (g+d = two sequential keys within 500ms)
- Ignores shortcuts when typing in inputs/textareas
- Provides visual feedback (brief flash on triggered action)

### Visual Hints
- Sidebar nav items show shortcut hints on hover: `Dashboard  gd`
- Command palette shows all shortcuts
- `?` opens a shortcuts cheat sheet modal

### Files
- New: `lib/keyboard.ts` — shortcut manager, chord detection
- New: `hooks/useKeyboardShortcuts.ts` — React hook
- New: `components/KeyboardShortcutsHelp.tsx` — cheat sheet modal
- Modified: `components/Sidebar.tsx` — shortcut hints
- Modified: `app/layout.tsx` — mount global shortcut listener

---

## 3. Quick-Peek Paper Modal

### Design
Press `Space` on any paper in a list to preview it without navigating away.

```
┌─────────────────────────────────────────────────────┐
│  ✕                                                   │
│                                                      │
│  Attention Is All You Need                           │
│  Vaswani et al. · 2017-06-12 · cs.CL                │
│                                                      │
│  ┌─ Abstract ──────────────────────────────────────┐ │
│  │ The dominant sequence transduction models are   │ │
│  │ based on complex recurrent or convolutional...  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ AI Summary ────────────────────────────────────┐ │
│  │ This paper introduces the Transformer...        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  [☆ Bookmark]  [📧 Email]  [📄 PDF]  [→ Full View]  │
│                                                      │
│  ← → Previous / Next paper                           │
└─────────────────────────────────────────────────────┘
```

### Behavior
- Opens as a modal overlay (Framer Motion slide-up + fade backdrop)
- `←` / `→` arrow keys cycle through papers in the current list
- `Escape` closes
- `Enter` navigates to full paper detail page
- All quick actions (bookmark, email, PDF) available inline
- Loads paper detail from `/papers/{id}` (cached if already fetched)

### Files
- New: `components/QuickPeek.tsx`
- Modified: `components/DashboardContent.tsx` — track selected index, Space handler
- Modified: `app/research/page.tsx` — same integration
- Modified: `app/bookmarks/page.tsx` — same integration

---

## 4. Inline Filter Chips + Quick Presets

### Current Problem
Filters are separate dropdown menus. Changing date requires clicking a dropdown and typing. No quick presets.

### New Design
Replace filter dropdowns with a horizontal chip bar:

```
┌──────────────────────────────────────────────────────────┐
│ [Today] [This Week] [This Month] │ cs.AI ✕ │ ▼ Category │ ▼ Date Range │ ▼ Sort │
└──────────────────────────────────────────────────────────┘
```

### Quick Presets
- **Today** — `start_date = today`
- **This Week** — `start_date = 7 days ago`
- **This Month** — `start_date = 30 days ago`
- **All Time** — no date filter
- Active preset highlighted with indigo background
- Clicking an active preset toggles it off

### Active Filter Chips
When a filter is active, it appears as a removable chip:
```
[cs.AI ✕]  [After: Mar 10 ✕]  [Sort: Date ↓]
```

### Category Quick-Select
Instead of dropdown, show a popover grid of categories with counts:
```
┌────────────────────────────────┐
│  cs.AI (234)    cs.LG (189)   │
│  cs.CL (156)    cs.CV (98)    │
│  cs.RO (45)     stat.ML (67)  │
│  ...more                       │
└────────────────────────────────┘
```
Each category shows paper count and is color-coded.

### Files
- New: `components/FilterChips.tsx` — chip bar with presets
- New: `components/CategoryPicker.tsx` — grid category selector
- Modified: `components/DashboardContent.tsx` — replace dropdown filters
- Modified: `app/research/page.tsx` — add filter chips to research

---

## 5. One-Click Bookmark

### Current Problem
Bookmarking requires: click icon → dropdown opens → select list → done. 3 interactions minimum.

### New Design
- **Single click** on bookmark icon → adds to default "Bookmarks" list instantly
- **Long press** (500ms) or **right-click** → opens list selector dropdown
- **Visual feedback:** Icon fills + scale pop animation (see engagement plan)
- **Undo toast:** "Bookmarked 'Paper Title'" with [Undo] button (5s timeout)

### Bookmark States
```
○  Not bookmarked (outline icon, zinc-500)
●  In default list (filled icon, indigo-400)
●● In multiple lists (filled icon + small badge count)
```

### Files
- Modified: `components/BookmarkButton.tsx` — single-click default, long-press for lists
- Modified: `components/PaperCard.tsx` — updated bookmark state display

---

## 6. Batch Operations

### Multi-Select Mode
- Click paper card checkbox (appears on hover at top-left corner) or press `x`
- Shift+click selects a range
- Selection bar appears at bottom of screen:

```
┌────────────────────────────────────────────────────────┐
│  3 papers selected  │ [☆ Bookmark All] [📧 Email] [🗑 Remove] [✕ Clear] │
└────────────────────────────────────────────────────────┘
```

### Available Batch Actions
- **Bookmark All** → add all to a selected list
- **Email Summary** → send combined summary email
- **Add to Batch Queue** → queue all for embedding generation
- **Export** → download as BibTeX or CSV
- **Remove from List** → (on bookmarks page only)

### Implementation
- Selection state managed in DashboardContent / parent page component
- Floating action bar at bottom with `position: sticky`
- Animated entrance (slide up from below viewport)
- Clear selection on page navigation

### Files
- New: `components/BatchActionBar.tsx` — floating action bar
- New: `components/SelectableCard.tsx` — wrapper adding checkbox to PaperCard
- Modified: `components/DashboardContent.tsx` — selection state, shift-click logic
- Modified: `app/bookmarks/page.tsx` — batch remove, batch export

---

## 7. Contextual Action Bar on Paper Cards

### Current State
Actions are scattered: bookmark button top-right, PDF link at bottom, no quick email/summarize.

### New Design
On hover, a compact action bar slides in at the bottom of the card:

```
┌──────────────────────────────────────┐
│  Paper Title...                      │
│  Summary text...                     │
│                                      │
│  ─────────────────────────────────── │
│  [☆ Save] [📧 Email] [📄 PDF] [⚡ Summarize] [→ Open] │
└──────────────────────────────────────┘
```

### Behavior
- Slides up from below card content (Framer Motion, 150ms)
- Icons with labels on wide screens, icons-only on narrow
- Each action fires immediately (no intermediate UI except bookmark list)
- Summarize shows inline progress spinner, then checkmark
- Disabled state for already-summarized papers (checkmark instead)

### Files
- New: `components/CardActionBar.tsx`
- Modified: `components/PaperCard.tsx` — integrate action bar on hover

---

## 8. Smart Paper Input

### Current State
Add paper form is a small text input in the sidebar. Easy to miss.

### New Design
Improve detection and reduce friction:

1. **Auto-detect arXiv URLs** — if user pastes an arXiv URL anywhere on the page, show a floating prompt:
   ```
   ┌──────────────────────────────────────┐
   │  📋 arXiv paper detected!            │
   │  "2402.12345 — Title Here"           │
   │  [Add to Library]  [Dismiss]         │
   └──────────────────────────────────────┘
   ```

2. **Command palette integration** — typing an arXiv ID pattern in ⌘K shows "Add paper: 2402.12345" as first result

3. **Drag-and-drop** — drag a URL from browser tab bar onto the app to trigger add

### Files
- New: `components/PasteDetector.tsx` — clipboard listener for arXiv patterns
- Modified: `components/CommandPalette.tsx` — arXiv ID detection in search
- Modified: `app/layout.tsx` — mount PasteDetector

---

## 9. Improved Navigation Patterns

### Breadcrumbs
On paper detail and nested pattern views, show breadcrumb trail:
```
Dashboard > cs.AI > Paper Title
Patterns > Agent Planning > Tree Search
```

### Back Navigation
- Paper detail page: "← Back to [previous page name]" with keyboard shortcut
- Preserve scroll position when returning to lists (already partially implemented via session storage — extend to all pages)

### Active Page Indicator
Sidebar active item gets:
- Indigo left border (3px)
- Brighter icon + text
- Subtle background glow

### Files
- New: `components/Breadcrumbs.tsx`
- Modified: `app/paper/[id]/page.tsx` — breadcrumb + back button
- Modified: `app/patterns/page.tsx` — breadcrumbs for drill-down
- Modified: `components/Sidebar.tsx` — enhanced active state
