# Timeline Page — Design Specification

## Design Tokens

| Token | Value | Usage |
|---|---|---|
| Page background | `#F5F0E8` | Body / page base |
| Card surface | `#EDE9E1` | Node backgrounds, detail panel |
| Inset surface | `#E5E0D5` | Category badges, nested elements |
| Featured surface | `#2A4A1A` | Hero header section |
| Accent | `#C4614A` | Search button, interactive highlights |
| Accent hover | `#B05540` | Hover state for accent elements |
| Foreground | `#1C1915` | Primary text |
| Foreground secondary | `#6B6258` | Subtitles, meta text |
| Foreground muted | `#9B9086` | Timestamps, labels, graph chrome |
| On-featured | `#FFFFFF` | Text on featured surface |
| Display font | `Newsreader` | Headings, hero title, seminal node titles |
| Body font | `Inter` | Body text, labels, metadata |
| Label tracking | `0.08em` | Uppercase metadata labels |

## Layout Structure

```
+-----------------------------------------------------------+
| SEARCH BAR (sticky top, bg card surface, warm border)     |
|  [search icon] [input field          ] [lib toggle] [btn] |
+-----------------------------------------------------------+
|                                                           |
| STATE-DEPENDENT CONTENT:                                  |
|                                                           |
| A) EMPTY STATE / HERO                                     |
|    Featured surface header with icon + headline           |
|    Subtitle + 3 suggestion cards on card surface          |
|    Footer note                                            |
|                                                           |
| B) LOADING STATE                                          |
|    Centered spinner + "Building timeline..."              |
|                                                           |
| C) ERROR / NO-RESULTS                                     |
|    Centered message with icon                             |
|                                                           |
| D) GRAPH + DETAIL                                         |
|    +-----------------------------------------------+      |
|    | TIMELINE GRAPH (ReactFlow canvas)             |      |
|    | - Year markers along top                      |      |
|    | - Paper nodes placed by date (x) + stacked (y)|      |
|    | - Citation edges between nodes                |      |
|    | - MiniMap (bottom-right)                       |      |
|    | - Controls (bottom-left)                       |      |
|    | - Stats pill (top-right)                       |      |
|    +-----------------------------------------------+      |
|    +-----------------------------------------------+      |
|    | DETAIL PANEL (shown on node click)             |      |
|    | [badges] Title                                 |      |
|    | Summary text          | Authors + Actions      |      |
|    +-----------------------------------------------+      |
+-----------------------------------------------------------+
```

## Component Specifications

### Component #1: Search Bar (Sticky)
- **Position**: Sticky top, z-30
- **Background**: `bg-[var(--color-surface-card)]` with warm border-bottom `border-[#D5CFC4]`
- **Input**: Rounded-full, `bg-[var(--color-surface-inset)]`, border `border-[#D5CFC4]`, text `var(--color-foreground)`, placeholder `var(--color-foreground-muted)`
- **Library toggle pill**: Inside input, right side. Active: `bg-[var(--color-accent)]/15 text-[var(--color-accent)]`. Inactive: `bg-[var(--color-surface-card)] text-[var(--color-foreground-muted)]`
- **Search button**: `bg-[var(--color-accent)] text-white` rounded-full. Hover: `bg-[var(--color-accent-hover)]`. Disabled: opacity-40

### Component #2: Hero / Empty State
- **Header block**: `bg-[var(--color-surface-featured)]` with generous padding
- **Icon**: GitBranch in white/on-featured color, set in a bordered circle on featured surface
- **Headline**: `font-[var(--font-display)]` font-bold text-4xl/5xl, `text-[var(--color-on-featured)]`
- **Gradient span**: accent-colored text for emphasis word
- **Subtitle**: `text-[var(--color-on-featured)]/80` text-lg
- **Suggestion cards**: `bg-[var(--color-surface-card)]` rounded-2xl, border `border-[#D5CFC4]`, shadow-warm-sm. Hover: shadow-warm
- **Card icon**: accent color
- **Card title**: `font-[var(--font-display)]` font-bold text-sm, foreground color
- **Card description**: text-xs, foreground-secondary
- **Footer note**: foreground-muted, uppercase tracking-widest

### Component #3: Timeline Graph Canvas
- **Container**: `bg-[var(--color-surface-card)]` rounded-2xl, shadow-warm, overflow-hidden, height 650px
- **ReactFlow background**: Dot grid using `var(--color-surface-inset)` dots on card surface
- **Year marker nodes**: font-display, 8rem, font-weight 800, opacity 0.12, color `var(--color-foreground-muted)`
- **Edge colors**: Use warm-mapped category colors (see Category Color Map below)
- **MiniMap**: `bg-[var(--color-surface-inset)]`, border `border-[#D5CFC4]`, rounded-xl
- **Controls toolbar**: `bg-[var(--color-surface-card)]/90` backdrop-blur, border `border-[#D5CFC4]`, rounded-xl. Button text: foreground-secondary, hover: bg-surface-inset
- **Stats pill**: `bg-[var(--color-background)]/80` backdrop-blur, border `border-[#D5CFC4]`, rounded-full. Text: foreground-muted, uppercase tracking

### Component #4: Paper Node (Regular)
- **Background**: `bg-[var(--color-surface-card)]` backdrop-blur
- **Border**: `border-[#D5CFC4]`, hover: `border-[var(--color-accent)]/40`
- **Title**: foreground color, text-xs font-medium (regular) or text-base font-bold font-display (high-citation)
- **Meta text**: foreground-muted, 11px
- **Category badge**: `bg-[var(--color-surface-inset)]` text foreground-secondary
- **High-citation label**: accent color icon + uppercase text
- **Selected state**: ring-2 ring-accent/50 border-accent/40
- **Library badge**: accent-colored bookmark icon
- **Handles**: bg-foreground-muted, 2px diameter

### Component #5: Paper Node (Seminal)
- **Scale**: 1.1x, width 320px, extra padding
- **Background**: `bg-[var(--color-surface-card)]` backdrop-blur
- **Border**: 2px `border-[#C4614A]/40` (accent)
- **Ring**: ring-4 `ring-[#C4614A]/10`
- **Glow**: warm box-shadow using accent color `rgba(196, 97, 74, 0.15)`
- **Seminal badge**: accent-colored pulsing dot + star icon + "Seminal Paper" uppercase label
- **Title**: font-display text-xl font-extrabold foreground
- **Handles**: bg-accent

### Component #6: Paper Node (Ghost)
- **Background**: transparent
- **Border**: dashed `border-[var(--color-foreground-muted)]/30`, hover: `/50`
- **Title**: foreground-secondary, italic
- **ArXiv ID**: font-mono foreground-muted

### Component #7: Detail Panel
- **Background**: `bg-[var(--color-surface-card)]` rounded-2xl, border-t `border-[#D5CFC4]`
- **Seminal badge**: `bg-[#C4614A]/10 text-[#C4614A]` border-accent/20
- **Category badge**: `bg-[var(--color-surface-inset)] text-[var(--color-foreground-secondary)]`
- **Title**: font-display text-3xl font-extrabold foreground
- **Summary**: text-sm foreground-secondary
- **Authors label**: uppercase tracking-widest foreground-muted
- **Authors text**: foreground, text-xs font-medium
- **Primary CTA**: `bg-[var(--color-accent)] text-white` rounded-xl, font-display font-bold
- **Secondary buttons**: `bg-[var(--color-surface-inset)] text-[var(--color-foreground)]` border-[#D5CFC4]
- **Bookmark button wrapper**: `bg-[var(--color-surface-inset)]` border accent/10

## Category Color Map (Warm-Compatible)

For edges and node accents, map categories to warm-compatible muted tones:

| Category | Accent (edges/icons) |
|---|---|
| cs.AI | `#8B7355` (warm brown) |
| cs.LG | `#7B6B8A` (dusty mauve) |
| cs.CL | `#5B7B8A` (muted teal) |
| cs.CV | `#5B7A5B` (sage green) |
| cs.RO | `#B5944A` (warm gold) |
| cs.NE | `#A06B5B` (clay) |
| cs.IR | `#5B8A8A` (ocean teal) |
| stat.ML | `#8A6B8A` (plum) |
| Default | `#9B9086` (foreground-muted) |

## Interaction Patterns

1. **Search**: Type query + Enter or click Search button. Loading state replaces content. Results render graph.
2. **Library toggle**: Click pill to toggle library-only filtering. Triggers re-search if query exists.
3. **Suggestion click**: Populates query + triggers search.
4. **Node click**: Selects node, shows detail panel below graph. Clicking another node replaces detail.
5. **Graph navigation**: Pan (drag canvas), zoom (scroll/buttons), minimap drag.
6. **Detail CTA**: "Full Details" navigates to paper page. "arXiv" opens external link. "Import" fetches paper.

## Responsive Notes

- Search bar and graph are full-width
- Suggestion cards stack to 1-column on mobile (md:grid-cols-3 -> grid-cols-1)
- Detail panel stacks vertically on smaller screens (flex-col on mobile)
- Graph height remains 650px with scroll/zoom for navigation
