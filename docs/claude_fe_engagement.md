# Detailed Plan: Engaging Visual Experience

## 1. Page Transitions

### Implementation
Wrap the App Router's `children` in `layout.tsx` with Framer Motion's `AnimatePresence` and a `PageTransition` component.

```
layout.tsx
  └── AnimatePresence mode="wait"
        └── <PageTransition key={pathname}>
              └── {children}
```

### Animation Specs
- **Enter:** Fade in (opacity 0→1) + slide up (y: 8px→0), 200ms ease-out
- **Exit:** Fade out (opacity 1→0), 150ms ease-in
- **No transition for:** Same-page state changes (filters, search results)

### Files
- New: `components/animations/PageTransition.tsx`
- Modified: `app/layout.tsx`

---

## 2. Card Animations

### Staggered Entrance
When papers load (initial or filter change), cards animate in with staggered delays.

```
container: { staggerChildren: 0.04 }
item: { opacity: [0, 1], y: [12, 0], duration: 0.3 }
```

### Hover Effects
Replace current `hover:border-indigo-500/50` with layered effect:
- Border brightens to indigo-500/60
- Card lifts: `translateY(-2px)`
- Subtle shadow appears: `shadow-lg shadow-indigo-500/5`
- Transition: 200ms ease-out

### Click Feedback
- `active:scale-[0.98]` (already partially exists, make consistent)

### Files
- New: `components/animations/StaggerList.tsx` — reusable wrapper
- Modified: `components/PaperCard.tsx` — hover + entrance animations
- Modified: `components/DashboardContent.tsx` — wrap grid in StaggerList

---

## 3. Skeleton Loading

### Approach
Replace `animate-pulse` placeholders with shimmer skeletons that match the shape of real content.

### Paper Card Skeleton
```
┌──────────────────────────────┐
│ ░░░░░░░░ ░░░░   ░░░         │  ← date + category badges (shimmer)
│                              │
│ ░░░░░░░░░░░░░░░░░░░░░       │  ← title line 1
│ ░░░░░░░░░░░░░░░              │  ← title line 2
│                              │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░  │  ← summary line 1
│ ░░░░░░░░░░░░░░░░░░░░░░░     │  ← summary line 2
│ ░░░░░░░░░░░░░░░░             │  ← summary line 3
│                              │
│ ░░░░░░░░   ░░░░░░░          │  ← action buttons
└──────────────────────────────┘
```

### Shimmer Effect (CSS)
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, #27272a 25%, #3f3f46 50%, #27272a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### Files
- New: `components/SkeletonCard.tsx`
- New: `components/SkeletonList.tsx` (for list view)
- Modified: `components/DashboardContent.tsx` — show skeletons during load
- Modified: `app/globals.css` — shimmer keyframes

---

## 4. Micro-Interactions

### Bookmark Animation
When user bookmarks a paper:
1. Heart/bookmark icon fills with color (indigo→filled)
2. Brief scale pop: 1→1.3→1 over 300ms with spring physics
3. Small particle burst effect (3-4 dots radiating outward, fade out)

### Toast Notifications
Replace custom `successMessage`/`errorMessage` state with `sonner` toasts:
- Slide in from bottom-right
- Auto-dismiss after 4s
- Success: green left border, checkmark icon
- Error: red left border, X icon
- Action toasts: include undo button

### Button Ripple
Primary action buttons get subtle ripple on click:
- Radial gradient expanding from click point
- Semi-transparent white (10% opacity)
- 400ms duration, ease-out

### Copy-to-Clipboard
ArXiv ID and paper titles get a click-to-copy with:
- Brief checkmark flash replacing the text/icon
- Toast confirmation

### Files
- Modified: `components/BookmarkButton.tsx` — pop + burst animation
- New: `components/animations/BookmarkBurst.tsx` — particle effect
- Modified: `app/layout.tsx` — add `<Toaster />` from sonner
- Modified: All pages — replace setState alerts with toast()

---

## 5. Visual Hierarchy on Paper Cards

### Category Color Coding
Assign consistent colors to top categories:
```
cs.AI  → indigo
cs.LG  → violet
cs.CL  → sky
cs.CV  → emerald
cs.RO  → amber
stat.ML → pink
other  → zinc
```

Apply as:
- Left border accent (3px colored bar)
- Category badge background tint
- Subtle card background gradient (2% opacity at top)

### Relevance/Similarity Score
When displaying search results or similar papers, show a visual relevance indicator:
- Small circular progress ring (0-100%) next to the result
- Color: green (>80%), yellow (50-80%), gray (<50%)

### Reading Time Estimate
Calculate from abstract length: `~${Math.ceil(wordCount / 200)} min read`
Display as small text next to the date.

### Files
- New: `lib/categoryColors.ts` — color mapping
- Modified: `components/PaperCard.tsx` — colored border, reading time, relevance ring
- Modified: `app/research/page.tsx` — pass relevance scores to cards

---

## 6. Chat Interface Enhancements

### Streaming Text Reveal
When assistant responds, reveal text character-by-character (or token-by-token if backend supports streaming):
- Characters appear with slight fade: opacity 0→1 per character group
- Cursor blinks at end of growing text
- Fallback for non-streaming: sentence-by-sentence reveal with 100ms delays

### Source Cards
Replace plain text source list with rich cards:
```
┌──────────────────────────────┐
│ 📄 Paper Title               │
│ arxiv:2402.12345 · cs.AI     │
│ "...relevant excerpt..."     │
│                    [View →]  │
└──────────────────────────────┘
```

### Typing Indicator
Replace 3-dot bounce with animated ellipsis in a chat bubble:
- Three dots with sequential opacity pulse
- Appears in assistant message area
- Smooth height transition when real response replaces it

### Files
- Modified: `app/chat/page.tsx` — streaming reveal, source cards, typing indicator
- New: `components/SourceCard.tsx` — rich source display
- New: `components/animations/StreamingText.tsx` — text reveal effect

---

## 7. Empty States

### Approach
Each empty state gets:
- A relevant lucide-react icon (64px, zinc-600)
- A brief message explaining what goes here
- A primary action button to get started

### Examples
| Page | Icon | Message | Action |
|------|------|---------|--------|
| Dashboard (no papers) | `Newspaper` | "No papers yet. Add your first arXiv paper to get started." | "Add Paper" button |
| Research (no results) | `SearchX` | "No papers match your search. Try different keywords or broaden your filters." | "Clear filters" |
| Bookmarks (empty list) | `BookmarkPlus` | "This list is empty. Browse papers and bookmark ones you want to revisit." | "Browse Dashboard" |
| Chat (no messages) | `MessageCircle` | "Ask anything about your paper library." | Suggested prompts |
| Analytics (no data) | `BarChart3` | "Not enough data yet. Analytics appear after 50+ papers are indexed." | — |

### Files
- New: `components/EmptyState.tsx` — reusable component
- Modified: All pages with empty states

---

## 8. Dashboard Header Sparkline

### Design
Top of dashboard shows a small summary row:
```
┌─────────────────────────────────────────────────┐
│  📊 1,247 papers  ·  📈 +23 today  ·  ▁▃▅▇█▅▃  │
└─────────────────────────────────────────────────┘
```

The sparkline shows papers ingested over the last 14 days as a tiny inline area chart (recharts `<Sparkline>`).

### Files
- New: `components/DashboardHeader.tsx`
- Modified: `components/DashboardContent.tsx` — include header above filters
