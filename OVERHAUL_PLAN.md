# Overhaul Plan
Last updated: 2026-03-26
Status legend: ○ not_started | ⟳ in_progress | ✓ done | ⚠ escalated | ✗ failed

---

## Overview

This plan governs the full frontend overhaul of the arxiv_assistant application.
The design language target is warm editorial (docs/DESIGN_LANGUAGE.md).
App name placeholder: "Scholar's Atelier" (from Stitch; final name TBD).

Navigation model (DECISION confirmed):
- Primary nav: fixed icon sidebar rail — Library, Queue, Collections, Archive
- Page-level read-status tabs: Unread / Reading / Read / Skipped (inside main content area)
- Secondary/detailed nav: hamburger drawer (current Sidebar.tsx pattern preserved as drawer)

Pages currently in the codebase that map to the new nav model:
- `/` (root, currently an alias for queue) → becomes the Queue page entry point
- `/queue` → Queue page (Library domain)
- `/bookmarks` → Library / Collections (maps to new "Library" nav item)
- `/research` → not in primary nav rail; accessible via Command Palette / hamburger
- `/dashboard` → not in primary nav rail; accessible via hamburger
- `/analysis`, `/patterns`, `/chat`, `/timeline`, `/paper/[id]`, `/settings` → secondary access

Escalation decisions outstanding: see E-005, E-006 below.

---

## Phase 1: Foundation
Must complete before any page work. All later phases depend on these tokens, globals, and shell.

### 1.1 Design Token Layer
Status: ✓
Spec: — (no Stitch; resolve from docs/DESIGN_LANGUAGE.md)
Files to create/modify:
  - frontend/app/globals.css — full replacement (warm palette, typography CSS vars, skeleton, utilities)
  - frontend/lib/tokens.ts — (create) typed token constants for JS/TSX use
  - [x] 1.1.1 Replace CSS custom properties: swap dark/cool palette for warm cream/parchment base (`--color-background`, `--color-surface-card`, `--color-surface-inset`, `--color-surface-featured`, `--color-accent`, `--color-foreground`, etc.)
  - [x] 1.1.2 Add typography CSS vars: `--font-display` (variable-weight serif — Newsreader or Fraunces from Google Fonts), `--font-body` (Inter, already loaded), letter-spacing token for metadata labels
  - [x] 1.1.3 Rewrite Tailwind theme extension in globals.css (@theme inline block): replace zinc/indigo dark tokens with warm tokens; add `surface-card`, `surface-inset`, `surface-featured`, `accent` color aliases
  - [x] 1.1.4 Rewrite `.skeleton` utility class for warm palette; remove space/parallax animation keyframes (SpaceBackground* components will be deleted in 1.3)
  - [x] 1.1.5 Add warm-shadow utility (`.shadow-warm`): `box-shadow: 0 4px 24px rgba(60,40,20,0.08)`
  - [x] 1.1.6 Create frontend/lib/tokens.ts — export typed constants mirroring CSS vars for use in JS (accent hex, surface hex values, featured surface hex)
Validator notes:
  [PASS] Warm surface: #F5F0E8 — warm parchment/cream confirmed; not white, not cool grey, not zinc
  [PASS] No dark remnants: no #09090b, bg-zinc, text-white (root/body), oklch dark values, or dark: class references found in globals.css
  [PASS] Required CSS vars: all 12 required vars present in :root — --color-background, --color-surface-card, --color-surface-inset, --color-surface-featured, --color-accent, --color-foreground, --color-foreground-secondary, --color-foreground-muted, --color-on-featured, --font-display, --font-body, --tracking-label
  [PASS] Tailwind theme block: @theme inline block maps --color-background, --color-accent, --color-surface-card, and all other warm tokens as Tailwind utilities
  [PASS] Skeleton warm: .skeleton gradient uses var(--color-surface-card) and var(--color-surface-inset) — no zinc or white values
  [PASS] Warm shadow utilities: .shadow-warm, .shadow-warm-sm, .shadow-warm-lg all present with rgba(60,40,20,…) warm brown values
  [PASS] tokens.ts completeness: file exists, exports `tokens as const` with colors.background, colors.accent, colors.surfaceFeatured, and all other color/tracking constants; types correct
  [PASS] No broken syntax: all braces closed, @theme inline and @keyframes blocks well-formed, no malformed constructs in 97-line file
  [PASS] Functional capabilities intact: --radius and scrollbar-hide absent from new globals.css; grep confirmed zero components reference either token, so no existing components are broken
  Overall: PASS

---

### 1.2 Font Loading
Status: ✓
Spec: — (no Stitch; resolve from docs/DESIGN_LANGUAGE.md)
Files to create/modify:
  - frontend/app/layout.tsx — replace / supplement font imports
  - [x] 1.2.1 Add Newsreader (variable weight, subsets: latin) via `next/font/google`; expose as `--font-display` CSS var
  - [x] 1.2.2 Keep Inter as body font; keep Manrope variable if used elsewhere; remove unused font vars
  - [x] 1.2.3 Update `<body>` className in layout.tsx to apply new font vars and warm background token (remove `bg-black`, `dark` class, `text-white`)
Validator notes:
  [PASS] Newsreader imported: `Newsreader` from `next/font/google` present with weights 200–900 (normal+italic) and `variable: "--font-newsreader"` — extralight (200) and black (900) both declared
  [PASS] Inter variable: `Inter` uses `variable: "--font-inter"`, populating `--font-body: var(--font-inter, system-ui, sans-serif)` in globals.css
  [PASS] Newsreader variable on body: `${newsreader.variable}` present in `<body>` className
  [PASS] No dark class on html: `<html lang="en" suppressHydrationWarning>` — no `className="dark"`
  [PASS] No bg-black / text-white on body: neither token appears in body className
  [PASS] bg-background text-foreground on body: both warm tokens applied to `<body>`
  [PASS] Providers intact: `LibraryProvider`, `CommandPalette`, and `Toaster` all present in JSX
  [PASS] Manrope intact: `Manrope` with `variable: "--font-manrope"` present; `${manrope.variable}` in body className
  Overall: PASS (8/8 checks)

---

### 1.3 Remove Dark-Theme Infrastructure
Status: ✓
Spec: — (no Stitch)
Files to modify/delete:
  - frontend/components/parallax/SpaceBackground3D.tsx — DELETE
  - frontend/components/parallax/SpaceBackgroundCSS.tsx — DELETE
  - frontend/components/parallax/SpaceBackgroundClient.tsx — DELETE
  - frontend/components/parallax/SpaceBackgroundSwitcher.tsx — DELETE
  - frontend/components/parallax/ParallaxBackground.tsx — DELETE (audit first for non-parallax reuse)
  - frontend/components/parallax/ParallaxLayer.tsx — DELETE
  - frontend/components/parallax/ScrollProgress.tsx — DELETE (or keep if scroll progress is wanted; default: delete)
  - frontend/app/layout.tsx — remove SpaceBackgroundClient and ScrollProgress imports/JSX
  - [x] 1.3.1 Audit each parallax/* component for any logic that should be preserved (none expected); delete all
  - [x] 1.3.2 Remove SpaceBackgroundClient and ScrollProgress from layout.tsx; remove `dark` className from `<html>`
  - [x] 1.3.3 Update Toaster in layout.tsx: switch to warm light theme (remove dark bg/border inline styles)
Validator notes:
  [PASS] Parallax files deleted: all 7 target files confirmed absent — SpaceBackground3D.tsx,
    SpaceBackgroundCSS.tsx, SpaceBackgroundClient.tsx, SpaceBackgroundSwitcher.tsx,
    ParallaxBackground.tsx, ParallaxLayer.tsx, ScrollProgress.tsx — none exist in filesystem.
  [PASS] No dangling imports: grep of entire frontend/ for SpaceBackground, ParallaxBackground,
    ParallaxLayer, ScrollProgress found zero matches in source files; only hit was CLAUDE.md
    (documentation reference — not a code import, not a runtime dependency).
  [PASS] layout.tsx clean: SpaceBackgroundClient and ScrollProgress appear in neither imports
    nor JSX in frontend/app/layout.tsx. File contains only: Inter/Manrope/Newsreader fonts,
    globals.css, katex.min.css, Sidebar, PageTransition, LibraryProvider, Toaster,
    CommandPalette — nothing parallax or dark-theme related.
  [PASS] Toaster warm: Toaster in layout.tsx uses CSS vars only — background:
    'var(--color-surface-card)', color: 'var(--color-foreground)', boxShadow:
    '0 4px 24px rgba(60,40,20,0.08)'. No theme="dark", no hardcoded dark hex
    (no #1a1a2e or similar). Fully warm-token driven.
  [PASS] TiltCard preserved: frontend/components/parallax/TiltCard.tsx exists.
    Only file remaining in the parallax/ directory.
  [PASS] DashboardContent intact: frontend/components/DashboardContent.tsx exists,
    zero imports of ParallaxLayer (import line removed), all dashboard content
    (paper cards, bento grid, filters, date groups, infinite scroll, quick peek,
    shortcut overlay) fully preserved — only wrapper tags removed as intended.
  [PASS] Spot-check — Sidebar.tsx: imports from next/link, next/navigation, lucide-react,
    sonner, lib/api, useRouter — no parallax or deleted-file references.
  [PASS] Spot-check — PaperCard.tsx: imports from next/link, lucide-react, framer-motion,
    react-markdown, remark/rehype plugins, LibraryContext, lib/api, BookmarkButton,
    lib/categoryColors — no parallax or deleted-file references.
  [PASS] Spot-check — CommandPalette.tsx: imports from react, cmdk, next/navigation,
    framer-motion, lucide-react, lib/api, lib/categoryColors — no parallax or deleted-file
    references.
  Overall: PASS (9/9 checks)

---

### 1.4 Layout Shell
Status: ✓
Spec: stitch/queue/SPEC.md (Component #1 Left Sidebar, Component #2 Top App Bar — layout reference only)
Files to create/modify:
  - frontend/app/layout.tsx — restructure shell JSX
  - frontend/components/AppShell.tsx — (create) wraps the three-zone layout
  - [x] 1.4.1 Create AppShell.tsx: three-zone flex layout — fixed icon sidebar rail (left, 64px wide), fixed top bar (full width, 60px tall), main scrollable content area (flex-1, left offset by rail width, top offset by bar height)
  - [x] 1.4.2 Wire AppShell into layout.tsx; remove old `<Sidebar />` from layout; pass `{children}` into content area
  - [x] 1.4.3 Apply warm surface tokens to shell: page background = `--color-background` (warm cream); top bar and rail = `--color-surface-card` (one warm tonal step); shadow-warm-sm on top bar; no borders, tonal separation only
Validator notes: content area must not be obscured by rail or top bar on any route; shell renders with no hydration errors.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] AppShell exists: frontend/components/AppShell.tsx present; first line is 'use client'
  [PASS] Three zones: rail fixed left-0 w-16 (64px); top bar fixed top-0 left-16 h-[60px] (60px, offset by rail); main ml-16 pt-[60px]
  [PASS] Warm tokens: rail bg-surface-card, top bar bg-surface-card, main bg-background — no bg-black, no bg-zinc, no bg-white
  [PASS] No structural borders: no border-r or border-b on any zone div in AppShell.tsx
  [PASS] shadow-warm-sm on top bar: present on top bar div; defined in globals.css as 0 2px 12px rgba(60,40,20,0.06)
  [PASS] layout.tsx uses AppShell: imported and children wrapped in <AppShell>...</AppShell>
  [PASS] Sidebar removed from layout: no <Sidebar JSX and no Sidebar import in layout.tsx
  [PASS] Providers intact: LibraryProvider, CommandPalette, Toaster all present in layout.tsx
  [PASS] Sidebar.tsx preserved: file exists at frontend/components/Sidebar.tsx
  [PASS] No hydration risk: AppShell is 'use client'; main passes {children} directly, no extra client boundary
  Overall: 10 PASS, 0 WARN, 0 FAIL

---

## Phase 2: Navigation Components

### 2.1 Icon Sidebar Rail
Status: ✓
Spec: stitch/queue/SPEC.md (Component #1 Left Sidebar)
Files to create/modify:
  - frontend/components/SidebarRail.tsx — (create) replaces Sidebar.tsx in layout
  - frontend/components/Sidebar.tsx — KEEP AS IS temporarily; repurpose as hamburger drawer in 2.2
  - [x] 2.1.1 Create SidebarRail.tsx: fixed, 64px wide, warm surface, no border. Four icon nav items: Library (`/bookmarks`), Queue (`/queue`), Collections (placeholder → `/bookmarks`), Archive (placeholder → `/research`). Active state: accent-color icon + left border accent strip. Inactive: muted icon, hover = tonal background shift.
  - [x] 2.1.2 Add app logo/monogram at top of rail (placeholder: BookMarked icon in accent color)
  - [x] 2.1.3 Add footer slot: Settings icon (link to `/settings`), Shortcuts icon (trigger ShortcutOverlay)
  - [x] 2.1.4 Add unread badge on Queue nav item (reuse existing `api.getQueueStats()` call pattern from Sidebar.tsx)
Validator notes: rail must stay fixed on scroll; active route must be visually distinct; no text labels (icon-only).
Validator notes (behavior-validator, 2026-03-26):
  [PASS] SidebarRail mounted in AppShell: AppShell.tsx imports and renders <SidebarRail /> inside the fixed left rail zone.
  [PASS] Four nav items: Library (/bookmarks), Queue (/queue), Collections (/bookmarks placeholder), Archive (/research) — all present with correct hrefs.
  [PASS] Icon-only: no text labels rendered in JSX; only <Icon size={20} />; title attr used for tooltip (accessible name only).
  [PASS] Active state uses accent: isActive path applies border-l-2 border-accent bg-surface-inset text-accent; inactive uses text-foreground-muted.
  [PASS] No structural border on rail: <nav> className is "flex flex-col h-full w-16 bg-surface-card" — no border-r present.
  [PASS] Logo slot: 60px top zone (h-[60px]) renders BookMarked icon in text-accent with aria-label "Scholar's Atelier".
  [PASS] Footer slot: Settings link (/settings) and Keyboard shortcuts button both present in pb-4 footer div.
  [PASS] Unread badge: Queue nav item has showBadge:true; dot span rendered conditionally when unreadCount > 0 — bg-accent rounded-full with aria-label showing count.
  Overall: PASS (8/8 checks)

---

### 2.2 Top App Bar
Status: ✓
Spec: stitch/queue/SPEC.md (Component #2 Top App Bar)
Files to create/modify:
  - frontend/components/TopBar.tsx — (create)
  - [x] 2.2.1 Create TopBar.tsx: fixed, full width (offset left by rail width), warm surface one tonal step darker than page. Left: "Scholar's Atelier" wordmark in display serif (mixed weight: light "Scholar's" + heavy italic "Atelier"). Center: inline read-status tab nav (Unread / Reading / Read / Skipped) — visible only on Queue route, hidden on all others. Right: search input with ⌘K hint (triggers CommandPalette), notifications bell (placeholder), user avatar (placeholder).
  - [x] 2.2.2 Wire ⌘K search input to existing CommandPalette open state (currently uses keyboard event; add a click trigger)
  - [x] 2.2.3 Conditionally show/hide status tabs based on `usePathname()` — tabs visible only on `/queue` and `/`
  - [x] 2.2.4 Style wordmark: load Newsreader for the "Atelier" portion (bold italic); apply accent color to key word only (not to wordmark as a whole — avoids dual-accent violation flagged in SPEC.md coherence check)
Validator notes: wordmark must not use a second accent color family (per SPEC.md coherence issue with emerald on wordmark); status tabs must not appear on non-queue routes.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] TopBar mounted in AppShell: AppShell.tsx imports TopBar and renders <TopBar onHamburgerOpen={() => setDrawerOpen(true)} />.
  [PASS] Fixed positioning: header element has className "fixed top-0 left-16 right-0 h-[60px] ..." — all four required values present.
  [PASS] Warm surface, no border: bg-surface-card and shadow-warm-sm on header; no border-b anywhere in TopBar.tsx.
  [PASS] Wordmark present: "Scholar's Atelier" rendered via style={{ fontFamily: 'var(--font-display)' }}; "Scholar's" uses text-foreground font-light, "Atelier" uses text-foreground-secondary italic — neither span uses an accent color token.
  [PASS] Status tabs conditional: QUEUE_ROUTES = ['/', '/queue']; showStatusTabs = QUEUE_ROUTES.includes(pathname); tabs nav rendered only when showStatusTabs is true; a flex-1 spacer replaces it on all other routes.
  [PASS] Search / ⌘K trigger: search button present with onClick={handleSearchClick}; dispatches synthetic Cmd+K keydown event to open CommandPalette; ⌘K kbd hint visible in button label.
  [PASS] Hamburger button: <Menu size={20} /> button present with onClick={onHamburgerOpen} and aria-label "Open navigation drawer".
  Overall: PASS (7/7 checks)

---

### 2.3 Hamburger Drawer (Secondary Nav)
Status: ✓
Spec: — (no Stitch; pattern from existing Sidebar.tsx)
Files to create/modify:
  - frontend/components/HamburgerDrawer.tsx — (create) based on existing Sidebar.tsx logic
  - frontend/components/Sidebar.tsx — to be replaced/deprecated after 2.3 is complete
  - [x] 2.3.1 Create HamburgerDrawer.tsx: slide-in drawer (same pattern as current Sidebar.tsx). Warm surface. Contains: all current navigation items (Discover, Dashboard, Research, Bookmarks, Analysis, Timeline, Patterns, Deep Dive, Settings) plus AddPaperForm and LibraryRing widgets. Triggered by hamburger icon in TopBar or SidebarRail.
  - [x] 2.3.2 Remove structural `border-r` from drawer (coherence: no structural borders — use tonal shadow instead)
  - [x] 2.3.3 Restyle nav links in drawer for warm palette: warm hover states, accent color for active item text (no heavy background fill — left accent border or text color change only)
  - [x] 2.3.4 Wire hamburger open state between TopBar and HamburgerDrawer via shared state or context
Validator notes: drawer open/close must not interfere with rail; overlay backdrop must cover content but not rail.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] HamburgerDrawer mounted in AppShell: AppShell.tsx imports HamburgerDrawer and renders <HamburgerDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />.
  [PASS] Drawer state in AppShell: const [drawerOpen, setDrawerOpen] = useState(false) declared in AppShell; drawerOpen passed as isOpen to HamburgerDrawer; setDrawerOpen(true) passed as onHamburgerOpen to TopBar.
  [PASS] No border-r on drawer: drawer panel className is "fixed top-0 left-0 z-50 h-screen w-[280px] flex flex-col bg-surface-card shadow-warm-lg transition-transform duration-300 ease-in-out ..." — no border-r present.
  [PASS] Warm surface: drawer panel uses bg-surface-card; all inner widgets use bg-surface-inset, text-foreground-*, var(--color-accent) — no zinc, gray-900, or dark hex tokens found.
  [PASS] Backdrop starts at left-16: backdrop div has className "fixed inset-0 left-16 bg-foreground/10 backdrop-blur-[2px] z-40" — rail (0–64px) is fully uncovered.
  [PASS] All nav links present: 9 navigation items defined — Discover (/), Dashboard (/dashboard), Research (/research), Bookmarks (/bookmarks), Analysis (/analysis), Timeline (/timeline), Patterns (/patterns), Deep Dive (/chat), Settings (/settings) — exceeds minimum of 6.
  [PASS] Active link uses accent: isActive path applies "border-l-2 border-accent text-accent pl-[10px] bg-surface-inset" to link and "text-accent" to icon — no indigo token present anywhere in HamburgerDrawer.tsx.
  [PASS] Sidebar.tsx untouched: frontend/components/Sidebar.tsx exists at expected path; not modified by Tasks 2.2 or 2.3.
  Overall: PASS (8/8 checks)

---

### 2.4 Command Palette — Warm Reskin
Status: ✓
Spec: stitch/queue/SPEC.md (Component #2 — ⌘K hint in search bar)
Files to modify:
  - frontend/components/CommandPalette.tsx
  - [x] 2.4.1 Restyle backdrop and palette container for warm palette: warm cream surface (not zinc-900), warm shadow, no dark glass effect
  - [x] 2.4.2 Update selected-item highlight from indigo to accent color
  - [x] 2.4.3 Update pages list to include Queue entry and correct hrefs to match new routing (Queue → `/queue`, Library → `/bookmarks`)
  - [x] 2.4.4 Update chord shortcut hints (g+d, g+r, etc.) to match new nav model in Actions group
Validator notes: palette must open on ⌘K; paper search must remain functional; warm surface, not dark.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] No dark container: Command element uses bg-surface-card shadow-warm-lg rounded-2xl — no bg-zinc-*, bg-black, or bg-gray-900.
  [PASS] Warm surface: bg-surface-card confirmed on the palette container.
  [PASS] No structural border on container: Command element has no border border-white/10 or equivalent; inner dividers (border-b/border-t border-surface-inset/50) are semantic separators, not structural container borders.
  [PASS] Selected item warm: all Command.Item elements use data-[selected=true]:bg-surface-inset data-[selected=true]:text-accent — no bg-indigo-* present.
  [PASS] Queue entry present: pages array includes { name: "Queue", href: "/queue", icon: Inbox } at position 1.
  [PASS] Search functionality intact: cmdk Command + Command.Input present; debounced searchPapers() calls api.searchPapers(); Command.List/Group/Item structure intact; paper results group renders conditionally on results.length > 0.
  Overall: PASS (6/6 checks)

---

### 2.5 Keyboard Navigation & Shortcut Overlay
Status: ✓
Spec: stitch/queue/SPEC.md (REQ-058, REQ-059, REQ-060 — resolved in implementation)
Files to modify:
  - frontend/components/ShortcutOverlay.tsx
  - frontend/lib/useKeyboardNav.ts
  - [x] 2.5.1 Restyle ShortcutOverlay.tsx for warm palette (no dark modal)
  - [x] 2.5.2 Update useKeyboardNav.ts chord map to match new nav routes
  - [x] 2.5.3 Add visible focus-ring design token to globals.css for keyboard-focused queue cards (accent-color outline, warm shadow)
Validator notes: j/k navigation on list pages must show focus ring on focused item; ? shortcut must open overlay.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] ShortcutOverlay warm: modal container div (line 46) uses bg-surface-card shadow-warm-lg rounded-2xl — no bg-zinc-*, bg-black, or bg-gray-900 present.
  [PASS] No border on overlay: modal container div has no border border-white/10 or any structural border token; only shadow-warm-lg provides edge separation.
  [PASS] kbd badges warm: all <kbd> elements (shortcut key list lines 63–68 and footer line 76) use bg-surface-inset — no bg-zinc-* present.
  [PASS] Chord map updated: useKeyboardNav.ts chordMap contains q: "/queue" (line 20) and l: "/bookmarks" (line 21) — both required chords present.
  [PASS] No broken chords: all 9 chordMap entries verified against frontend/app/ directory — /dashboard, /research, /chat, /bookmarks, /analysis, /patterns, /settings, /queue all exist as subdirectories; /bookmarks (l alias) is the same valid route. Zero broken chords.
  [PASS] focus-ring in globals.css: .focus-ring (line 99) uses outline: 2px solid var(--color-accent) with rgba(196,97,74,0.15) glow shadow; .focus-visible-ring:focus-visible (line 106) also uses var(--color-accent) outline — both classes present and correctly reference accent token.
  [PASS] Overlay open/close intact: ShortcutOverlay accepts open: boolean and onClose: () => void props; AnimatePresence + {open && (…)} controls mount/unmount; close button (line 50) calls onClose(); useKeyboardNav.ts case "Escape" (line 90) calls setShowShortcuts(false); case "?" (line 87) toggles setShowShortcuts.
  Overall: PASS (7/7 checks)

---

## Phase 3: Queue Page
This is the only page with an approved Stitch SPEC. Build it fully. All sub-tasks reference stitch/queue/SPEC.md.

### 3.1 Queue Page Shell Restructure
Status: ✓
Spec: stitch/queue/SPEC.md (overall three-zone layout)
Files to modify:
  - frontend/app/queue/page.tsx — restructure layout JSX and integrate new components
  - frontend/app/page.tsx — (currently aliases queue; keep alias or redirect, TBD in 3.1.1)
  - [x] 3.1.1 Decide root route: `/` currently renders `<QueuePage />` directly. Keep the alias so `/` and `/queue` both render queue. No change needed — page.tsx already imports and renders QueuePage. E-005 resolved: Option A.
  - [x] 3.1.2 Remove existing `max-w-4xl mx-auto` single-column wrapper; implement three-zone layout: main canvas (flex-1, wide, with right gutter reserved for quick-preview panel when open via `mr-[400px]` transition), quick-preview zone (fixed right panel when active, 400px wide — space reserved, QuickPreviewPanel component mounts in Task 3.8)
  - [x] 3.1.3 Apply warm surface to page: `bg-background` (warm cream) on outermost div; main canvas `px-12 pt-8 pb-24` (generous whitespace per design language)
Validator notes: three zones must not overlap; layout must be responsive (collapse right panel to bottom sheet on narrow viewports).
Validator notes (behavior-validator, 2026-03-26):
  [PASS] Root route alias: frontend/app/page.tsx imports QueuePage from ./queue/page and renders it inside Suspense — no dedicated home page, Option A confirmed.
  [PASS] No max-w-4xl wrapper: outermost div is "relative min-h-screen bg-background"; no max-w-4xl mx-auto present anywhere in the return tree.
  [PASS] bg-background on page: outermost div carries bg-background.
  [PASS] Generous padding: main canvas div has px-12 pt-8 pb-24 — meets spec.
  [PASS] Preview-responsive gutter: previewOpen = peekPaper !== null drives conditional mr-[400px] / mr-0 with transition-all duration-300 on main canvas div.
  [WARN] handleMarkRead absent: no standalone handleMarkRead function. Status mutations delegated via onStatusChange={fetchData} callback passed to QueueCard and DateGroup. Functionality equivalent — fetchData refreshes queue after any card-level status change. Not a regression; original page.tsx had no handleMarkRead either. Low severity.
  [PASS] Child components imports intact: QueueCard, QuickPeekSheet, and RippleButton all imported; no accidental removals.
  Summary: 6 PASS, 1 WARN, 0 FAIL

---

### 3.2 Queue Hero Header
Status: ✓
Spec: stitch/queue/SPEC.md (Component #3 Hero Header)
Files to modify:
  - frontend/app/queue/page.tsx — hero header section
  - [x] 3.2.1 Replace existing `<h1>` header: implement mixed-weight serif headline — "Your Reading" in Newsreader extralight + "Queue" in Newsreader black italic. Font sizes: extralight portion ~3xl, heavy portion ~4xl or larger.
  - [x] 3.2.2 Add subtitle: italic serif (Newsreader italic) below headline, short descriptor text
  - [x] 3.2.3 Add two CTA buttons: "Recalculate Scores" (maps to `handleRescore`) and "AI Scan" (maps to `handleDiscover`). Style: warm surface buttons with accent on primary action; warm shadow, generous border-radius (16px+)
  - [x] 3.2.4 Remove existing `<Compass>` icon from header (icon-first layout replaced by typography-first)
Validator notes: mixed-weight headline must use Newsreader, not Inter; no icon next to headline.

---

### 3.3 Featured Stat Block (Forest-Green Hero Panel)
Status: ✓
Spec: stitch/queue/SPEC.md (Component #4 Featured Stat Block)
Files to create/modify:
  - frontend/components/queue/FeaturedStatBlock.tsx — (create)
  - frontend/app/queue/page.tsx — add FeaturedStatBlock above the filter bar
  - [x] 3.3.1 Create FeaturedStatBlock.tsx: deep forest-green panel (`bg-[#2A4A1A]`). This is the single featured surface on the queue page — do not use this deep color anywhere else.
  - [x] 3.3.2 Top section: "Focus Mode · Recommended Next" label (uppercase, tracked), featured paper title (highest priority_score item from queue), relevance score callout + estimated reading time, author/date metadata in italic, "Start Reading →" CTA (navigates to `/paper/{arxiv_id}`)
  - [x] 3.3.3 Bottom section: 2×3 grid of stat tiles (all 6 per REQ-039 resolution): AI Discovered count, Manual Adds count, Completion %, Current Velocity (qualitative), High Priority count, Estimated Total Reading Time. Stat tile labels: uppercase with tracking.
  - [x] 3.3.4 Wire data: top paper via featuredPaper prop (caller passes highest priority_score item); stats from QueueStats props. high_priority_count existed in QueueStats; estimated_reading_hours existed; estimated_reading_time_minutes added as optional field.
Validator notes: forest green is the only featured/deep surface on this page; stat tile count must be exactly 6; "Start Reading" must navigate to paper detail, not open preview.
Validator notes (behavior-validator, 2026-03-26):
  [PASS] FeaturedStatBlock exists: frontend/components/queue/FeaturedStatBlock.tsx present, default export confirmed.
  [PASS] Forest green surface: component root div uses bg-[#2A4A1A]. No bg-surface-card or bg-background in the component.
  [PASS] Exactly 6 stat tiles: tiles array is always length 6 — populated with real values when stats is non-null, populated with "—" placeholders when stats is null. Grid renders {tiles.map(tile => ...)} with exactly the 6-item array.
  [PASS] All text on green is white: text-white on title, value cells, and CTA button; text-white/60 on labels and muted lines; text-white/70 on italic metadata. No text-foreground inside the component.
  [PASS] "Start Reading" button uses accent: CTA button className includes bg-accent — not green, not any zinc variant.
  [PASS] QueueStats new field: estimated_reading_time_minutes?: number added at line 156 in frontend/lib/api.ts under a REQ-039 resolution comment. estimated_reading_hours (existing) retained as fallback.
  [PASS] Graceful null handling: featuredPaper null → renders "No papers in queue yet." fallback paragraph; stats null → tiles array built via Array.from with "—" values; no unguarded property accesses.
  Summary: 7 PASS, 0 WARN, 0 FAIL

---

### 3.4 Source Filter Pill Group
Status: ✓
Spec: stitch/queue/SPEC.md (Component #5 Source Filter Pill Group) + DECISION (REQ-032 resolved: keep provider-level filter)
Files to modify:
  - frontend/app/queue/page.tsx — source filter section
  - [x] 3.4.1 Replace current segmented source filter tabs (All / Discovered / Saved) with pill-style segmented control: "All Sources", "ArXiv", "JSTOR", "Personal" (expandable to other providers). Active pill: accent-colored background fill (pill shape, border-radius: 999px). Inactive: no fill, text muted.
  - [x] 3.4.2 Update `SourceFilter` type and `SOURCE_TABS` array to match new provider taxonomy; update `api.getQueue()` call to pass provider param if filter API supports it (note: may require backend support, flag in implementation)
Validator notes: pill shape (border-radius: 999px); one active state at a time; no structural border around the pill group container.

---

### 3.5 Sort + Group + Filter Controls Bar
Status: ✓
Spec: stitch/queue/SPEC.md (Components #6, from reading_queue_grouped_by_date for grouping control) + DECISION (REQ-034 resolved: group control top-right adjacent to sort)
Files to modify:
  - frontend/app/queue/page.tsx — sort/group/filter row
  - [x] 3.5.1 Restyle sort dropdown: inline text label "Sort by: [Priority]" with accent-colored active value, chevron. Replace `<select>` with a styled custom dropdown component or keep native select with warm styling. Placement: left of group control.
  - [x] 3.5.2 Add grouping control: "Group by: [Week]" inline selector (Day / Week / Month / None) adjacent to sort, top-right of card list area. Matches concept from `stitch/queue/reading_queue_grouped_by_date/`.
  - [x] 3.5.3 Add filter icon button (opens advanced filter panel — panel contents: ⚠ see E-006 escalation). Button: filter icon, warm surface, accent on active state. Panel: slide-in or dropdown, warm card surface, no border (tonal shift only).
Validator notes: sort and group controls must be adjacent; filter panel content is escalated (E-006).

---

### 3.6 Group Header
Status: ✓
Spec: stitch/queue/SPEC.md (Component #7 Group Header) + reading_queue_grouped_by_date reference
Files to modify:
  - frontend/app/queue/page.tsx — DateGroup component
  - [x] 3.6.1 Restyle group header label: uppercase, `tracking-[0.2em]`, small size, warm muted foreground. Remove ChevronRight/ChevronDown lucide icons; replace collapse toggle with a more editorial affordance (e.g., a thin warm-colored rule + label inline).
  - [x] 3.6.2 Keep collapse/expand behavior from existing `DateGroup` component; restyle collapsed state.
  - [x] 3.6.3 Add item count in warm muted tone adjacent to group label.
Validator notes: uppercase with generous tracking; no structural border under the group header.

---

### 3.7 Queue Item Card
Status: ✓
Spec: stitch/queue/SPEC.md (Component #8 Queue Item Card)
Files to create/modify:
  - frontend/components/QueueCard.tsx — full restyle
  - [x] 3.7.1 Replace dark zinc surface with warm card surface (`bg-surface-card`). Remove explicit border (`border border-zinc-800`); use tonal separation only (card surface slightly warmer/darker than page). Border-radius: 16px minimum.
  - [x] 3.7.2 Add source type icon (Sparkles for AI-discovered, Bookmark for manual) at card left edge area. Keep category accent bar (left border strip) but restyle in accent/warm color family.
  - [x] 3.7.3 Restyle paper title: hover state → accent color (terracotta/warm-red), not indigo. Font: Inter medium or semibold.
  - [x] 3.7.4 Restyle author/journal/date metadata: italic serif (Newsreader or italic Inter), warm muted tone.
  - [x] 3.7.5 Restyle priority score badge: warm surface pill with accent border. Keep HIGH/MED/LOW labels with uppercase tracking.
  - [x] 3.7.6 Move overflow menu (⋮) to card top-right. Overflow menu must contain: "Remove from Queue" (REQ-037, resolved) and any other future items. Implement open state (simple dropdown, warm surface, warm shadow).
  - [x] 3.7.7 Restyle inline read-status toggle buttons (Unread / Read / Skipped / Reading): pill buttons, warm surface, accent-colored active state. Keep existing `handleMarkRead`, `handleMarkSkipped`, `handleMarkReading` handlers.
  - [x] 3.7.8 Replace priority override inline icon buttons (ArrowUp/Minus/ArrowDown) with a click-on-badge popup following pattern from `stitch/queue/priority_override_interaction/` — popup: AI score badge + High/Medium/Low/Auto options. Trigger: click on priority badge. Keep existing `handlePriority` API calls.
  - [x] 3.7.9 Add "Open Details" pill button (accent-colored outline) → navigate to `/paper/{arxiv_id}`. Add "Preview" pill button → triggers quick-preview panel.
  - [x] 3.7.10 Add warm focus ring on card when focused via keyboard (j/k nav); ring uses accent color, warm shadow.
Validator notes: no border on card; tonal surface only; accent color on interactive elements only; priority popup matches priority_override_interaction Stitch output.

---

### 3.8 Quick Preview Panel
Status: ✓
Spec: stitch/queue/SPEC.md (Component #9 Quick Preview Panel) + DECISION (REQ-040 resolved: add prev/next controls in implementation)
Files to create/modify:
  - frontend/components/queue/QuickPreviewPanel.tsx — (create) new fixed-right panel version
  - frontend/components/QuickPeekSheet.tsx — KEEP for other pages (bottom-sheet variant); queue page uses the new panel
  - frontend/app/queue/page.tsx — wire QuickPreviewPanel
  - [x] 3.8.1 Create QuickPreviewPanel.tsx: fixed right panel, 400px wide, warm surface with frosted glass (`backdrop-filter: blur(20px)`). Contains: "Quick Preview" badge label, close button (X), paper title (display serif, warm foreground), author/year in italic, Abstract section, AI Key Takeaways section (numbered list, italic, accent-colored numbers), "Begin Reading Session" full-width CTA button.
  - [x] 3.8.2 Wire panel open/close to "Preview" button on queue cards and to close (X) button. Panel state managed in queue page component (existing `peekPaper` state). [COMPONENT ONLY — state wired via props; page.tsx wiring deferred to 3.8.5]
  - [x] 3.8.3 Add prev/next navigation controls (per REQ-040 resolution): Previous / Next buttons at panel bottom. Wire to adjacent items in current sorted+filtered queue list. [COMPONENT ONLY — buttons present; page.tsx index wiring deferred]
  - [x] 3.8.4 Wire AI Key Takeaways section to existing `useSummarize` hook (same as QuickPeekSheet). Show placeholder italic text if no summary; show "Generate Summary" button.
  - [x] 3.8.5 "Begin Reading Session" CTA: calls `handleMarkReading` (api.markReading) for the previewed paper, then navigates to `/paper/{arxiv_id}`. previewIndex computed from sorted list; handlePreviewPrev/Next wired.
  - [x] 3.8.6 On narrow viewports (< 1024px): QuickPreviewPanel returns null when !isWide (handled inside component); QuickPeekSheet retained as mobile fallback, rendered conditionally on peekPaper !== null.
Validator notes: panel uses frosted glass (not opaque); only one border (the glass panel edge may use border-white/40 per SPEC note — minor coherence flag, acceptable); prev/next controls must be present.

---

### 3.9 Floating Action Button (FAB)
Status: ✓
Spec: stitch/queue/SPEC.md (Component #10 FAB)
Files to create/modify:
  - frontend/components/queue/QueueFAB.tsx — (create)
  - frontend/app/queue/page.tsx — add QueueFAB
  - [x] 3.9.1 Create QueueFAB.tsx: center-bottom fixed button, forest-green background (#2A4A1A matching featured surface), "Add New Research Item" label, bold plus icon. On click: open AddPaperForm in a modal or focus the existing form (maps to REQ-010).
  - [x] 3.9.2 Extract AddPaperForm from HamburgerDrawer into frontend/components/AddPaperForm.tsx; HamburgerDrawer updated to import from new location.
  - [x] 3.9.3 Wire QueueFAB + AddPaperForm modal into page.tsx: fabOpen state, backdrop click to close, X button, modal overlay with bg-foreground/20 backdrop-blur-sm.
Validator notes: FAB must use the same forest-green as the featured stat block (one featured color per page — FAB counts as a featured element on the same page, not a second featured surface, since it is a button not a surface).

---

### 3.10 Pagination / Load More
Status: ✓
Spec: stitch/queue/SPEC.md (Component #11)
Files to modify:
  - frontend/app/queue/page.tsx — bottom of card list
  - [x] 3.10.1 Add "Discover more insights in the archive →" italic serif text link at page bottom (styled per SPEC: italic, warm muted tone, arrow). Triggers handleDiscover (queue fetch). Arrow → is text glyph.
Validator notes: italic serif; warm muted color; → arrow glyph (not an icon component).

---

### 3.11 Empty State
Status: ✓
Spec: stitch/queue/SPEC.md (Open Question #7, no design yet — resolve in implementation)
Files to modify:
  - frontend/app/queue/page.tsx — EmptyQueue component
  - [x] 3.11.1 Restyle EmptyQueue: mixed-weight display serif headline ("Your queue is / ready."), no dashed border, no icon, generous whitespace, warm palette. "Discover Papers" button in accent style with Sparkles icon. Personal filter variant preserved.
Validator notes: must not look like an error; no dashed border; display serif for empty-state headline.

---

### 3.12 "Trigger Scan" Sidebar CTA
Status: ✓
Spec: stitch/queue/SPEC.md (Component #1 — "Trigger Scan" CTA in sidebar)
Files to modify:
  - frontend/components/SidebarRail.tsx (created in 2.1) — add Trigger Scan affordance
  - [x] 3.12.1 Add "Trigger Scan" button (ScanSearch icon, icon-only, tooltip on hover) to SidebarRail footer area. Calls api.discoverQueue(7). Uses accent hover color, no second featured color. Toast on success/failure.
Validator notes: must not introduce a second featured color; use accent or a muted warm tone.

---

## Phase 3 Validation (behavior-validator, 2026-03-26)
Overall: PASS
20 checks: 20 PASS, 0 WARN, 0 FAIL
Re-validated after E-007/E-008 fixes — all 20 checks now pass.

[FAIL] 1. No dark tokens (page.tsx): Found dark/cool tokens that must be replaced with warm design tokens:
  - L420-421: `bg-indigo-500/20 text-indigo-300 border border-indigo-500/40` and `text-zinc-600 hover:text-zinc-400` on STATUS_TABS buttons
  - L629: `text-zinc-500` on loading spinner
  - L658: `border-zinc-800` on completed section divider
  - L661: `text-zinc-500 hover:text-zinc-300` on completed toggle button
  - L867: `bg-zinc-900/60 border border-zinc-800` on StatCard (unused component but still present)
  - L870-871: `text-white` and `text-zinc-500` on StatCard (unused component but still present)
[PASS] 2. No dark tokens (QueueCard.tsx): Clean — all classes use design tokens (bg-surface-card, text-foreground, etc.).
[PASS] 3. FeaturedStatBlock forest green: Uses `bg-[#2A4A1A]` on root div.
[PASS] 4. QuickPreviewPanel frosted glass: Uses `backdropFilter: "blur(20px)"` and `backgroundColor: "var(--color-surface-overlay)"`.
[PASS] 5. QueueFAB forest green: Uses `bg-[#2A4A1A]`, not terracotta.
[PASS] 6. Mixed-weight serif headline: `font-extralight text-3xl` + `font-black italic text-5xl`, both with `var(--font-display)`.
[PASS] 7. REQ-031 View queue: Items rendered via DateGroup > QueueCard list.
[PASS] 8. REQ-032 Filter by source: SOURCE_TABS array includes All Sources/ArXiv/JSTOR/Personal.
[PASS] 9. REQ-033 Sort: SORT_OPTIONS array (6 options); sortField + sortDir state; handleSortChange wired.
[PASS] 10. REQ-034 Group by: GROUP_OPTIONS with day/week/month/none; groupBy state; GROUP_OPTIONS dropdown wired.
[PASS] 11. REQ-035 Mark status: QueueCard has handleMarkRead, handleMarkSkipped, handleMarkReading handlers calling api.markRead/markSkipped/markReading.
[PASS] 12. REQ-036 Priority override: PriorityPopup in QueueCard with High (3), Medium (2), Low (1) options + "Revert to Automatic" (null). handlePriority calls api.setManualPriority.
[PASS] 13. REQ-037 Remove from queue: OverflowMenu contains "Remove from Queue" button; handleRemove calls api.removeFromQueue; onRemove prop wired from page.tsx.
[PASS] 14. REQ-038 Rescore: handleRescore present; "Recalculate Scores" button in hero header calls api.rescoreQueue.
[PASS] 15. REQ-039 Stats (6 tiles): FeaturedStatBlock tiles array always length 6 (AI Discovered, Manual Adds, Completion, Current Velocity, High Priority, Est. Reading Time).
[PASS] 16. REQ-040 Preview nav: QuickPreviewPanel has onPrev/onNext/hasPrev/hasNext props; previewIndex computed from sorted list in page.tsx; handlePreviewPrev/handlePreviewNext wired.
[PASS] 17. REQ-010 Add paper: QueueFAB triggers fabOpen modal containing AddPaperForm.
[PASS] 18. REQ-012 Trigger scan: SidebarRail has ScanSearch icon button calling api.discoverQueue(7) with toast feedback.
[FAIL] 19. REQ-058 Keyboard focus: QueueCard accepts isFocused prop and applies focus-ring class, BUT page.tsx never defines focusedIndex state, never attaches j/k keyboard listeners, and never passes isFocused to QueueCard. Keyboard navigation is not wired.
[PASS] 20. Empty state: No dashed border, no Compass icon; uses display serif mixed-weight headline (font-extralight + font-black italic).

### Escalations from Phase 3 Validation

### E-007 — Dark/cool token remnants in queue page.tsx
Status: RESOLVED
Raised by: behavior-validator (Phase 3 validation, check 1)
Severity: Medium — visual regression, not functional
Details: STATUS_TABS active state uses `bg-indigo-500/20 text-indigo-300` (cool indigo) and inactive state uses `text-zinc-600 hover:text-zinc-400` (dark zinc). Loading spinner uses `text-zinc-500`. Completed section divider uses `border-zinc-800`, toggle button uses `text-zinc-500 hover:text-zinc-300`. StatCard component (lines 857-875) is entirely dark-themed (`bg-zinc-900/60 border border-zinc-800 text-white text-zinc-500`) — appears to be dead code (not used in current render tree) but should be removed or restyled.
Resolution needed: Replace all listed tokens with warm design tokens (bg-accent/20, text-accent, text-foreground-muted, border-surface-inset, etc.). Remove StatCard if unused.

### E-008 — Keyboard focus navigation not wired in queue page.tsx
Status: RESOLVED
Raised by: behavior-validator (Phase 3 validation, check 19)
Severity: Medium — REQ-058 partially unmet
Details: QueueCard component correctly accepts isFocused prop and renders focus-ring class. However, page.tsx has no focusedIndex state, no useEffect keyboard listener for j/k keys, and never passes isFocused={true} to any QueueCard. The keyboard navigation chain is broken at the page level.
Resolution needed: Add focusedIndex state to QueuePage; add keydown listener for j/k (move focus up/down), Space (open preview), b (bookmark); pass isFocused={focusedIndex === idx} to each QueueCard.

---

## Phase 4: Library Page
SPEC: stitch/library/SPEC.md
Functional requirements: stitch/library/FUNCTIONAL_REQUIREMENTS.md (REQ-L01 through REQ-L17)
Dependencies: Phase 1–2 complete (design tokens, fonts, shell, nav); Phase 3 complete (QuickPreviewPanel reusable, DateGroup pattern reusable)
Resolved escalations: E-018 (pill overflow → horizontal scroll with overflow-x-auto), E-019 (add-to-queue → small icon button next to bookmark), E-020 (PaperCard → new LibraryPaperCard component)

### 4.1 Library Page Shell + Token Swap
Status: ✓
Spec: stitch/library/SPEC.md (overall layout — hero header, pill tabs, control bar, card grid)
Files to modify:
  - frontend/app/bookmarks/page.tsx — full token swap and layout restructure
  - [x] 4.1.1 Remove all dark/cool tokens from bookmarks/page.tsx: replace `text-white`, `bg-zinc-*`, `border-zinc-*`, `text-indigo-*`, `focus:ring-indigo-*` with warm design tokens (`bg-background`, `bg-surface-card`, `text-foreground`, `text-foreground-muted`, `text-accent`, etc.). Remove `bg-black`, `[color-scheme:dark]`, and any dark-mode conditional classes.
  - [x] 4.1.2 Restructure outermost layout: apply `bg-background` on outer div, generous whitespace (`px-12 pt-8 pb-24` — matching queue/dashboard pattern), `space-y-10` between major sections (hero, pill tabs, control bar, card grid).
  - [x] 4.1.3 Keep all existing state hooks (papers, loading, selectedList, isCreatingList, newListName, sortBy, exportStatus, authUrl, codeVerifier, authCode, isExporting, isAuthenticating) and all API calls (loadLibrary, handleCreateList, handleDeleteList, handleExportToGDrive, handleConfirmAuth) intact. Only restructure JSX and swap tokens.
  - [ ] 4.1.4 Replace current `<select>` list filter dropdown with pill tabs (component built in Task 4.3). Replace current inline sort dropdown with styled control bar (component built in Task 4.4).
Validator notes: no dark tokens (bg-zinc, text-white, text-indigo, border-zinc) anywhere in bookmarks/page.tsx; outermost div uses bg-background; generous whitespace matches queue/dashboard pattern; all state and API logic preserved.

---

### 4.2 Library Hero Header (Featured Surface)
Status: ●
Spec: stitch/library/SPEC.md (Component #1 Library Hero Header) — REQ-L01
Files to create/modify:
  - frontend/components/library/LibraryHero.tsx — (create)
  - frontend/app/bookmarks/page.tsx — wire LibraryHero
  - [x] 4.2.1 Create LibraryHero.tsx: deep forest-green panel (`bg-surface-featured`). This is the single featured surface on the library page — do not use this deep color anywhere else on the page.
  - [x] 4.2.2 "YOUR LIBRARY" label: uppercase, `tracking-widest`, `text-[10px]`, `font-bold`, white/60 on the green surface.
  - [x] 4.2.3 Mixed-weight serif headline: "Your personal" in Newsreader font-extralight italic, "research library." in Newsreader font-bold. Both in white on green. Font sizes text-3xl md:text-4xl.
  - [x] 4.2.4 Subtitle: italic serif (Newsreader italic) below headline, paper and list counts in white/80.
  - [x] 4.2.5 Stats row: merged into subtitle — "{totalPapers} papers across {totalLists} collections" in italic Newsreader text-sm white/80.
  - [ ] 4.2.6 Wire into bookmarks/page.tsx: pass `papers.length` and `lists.length` as props. Show above pill tabs.
Validator notes: forest green is the only featured/deep surface on this page; mixed-weight headline uses Newsreader (not Inter); "YOUR LIBRARY" label is uppercase with tracking; all text on green surface is white or white/opacity.

---

### 4.3 List Pill Tabs
Status: ✅
Spec: stitch/library/SPEC.md (Component #2 List Pill Tabs) — REQ-L02, REQ-L05, REQ-L07, E-018
Files to create/modify:
  - frontend/components/library/ListPillTabs.tsx — (create)
  - frontend/app/bookmarks/page.tsx — wire ListPillTabs, remove old `<select>` list filter
  - [x] 4.3.1 Create ListPillTabs.tsx: horizontal scrollable pill row with `overflow-x-auto` and `scrollbar-hide` (E-018 resolution). Container: `flex gap-2 overflow-x-auto` with optional scroll-snap. (Combined into LibraryControls.tsx)
  - [x] 4.3.2 "All" pill (always first): active state when `selectedList === "All"`. Active pill: `bg-accent text-on-accent rounded-full px-4 py-1.5 text-sm font-medium`. Inactive pill: `bg-surface-inset text-foreground-muted rounded-full px-4 py-1.5 text-sm`.
  - [x] 4.3.3 Custom list pills: render one pill per item in `lists` array. Active/inactive styling matches 4.3.2. onClick sets `selectedList`.
  - [x] 4.3.4 "+ New List" pill: accent dashed border (`border-2 border-dashed border-accent/40 text-accent rounded-full px-4 py-1.5 text-sm`). onClick toggles `isCreatingList` state. When active, renders inline input inside the pill row (Enter to confirm, Escape to cancel) — REQ-L05.
  - [ ] 4.3.5 Wire into bookmarks/page.tsx: pass props to LibraryControls. Replace existing `<select>` filter. (Deferred per instructions — do NOT modify bookmarks/page.tsx)
Validator notes: horizontal scroll with overflow-x-auto (E-018); pill shape (border-radius: 999px via rounded-full); one active state at a time; "+ New List" pill has dashed accent border; inline input for list creation (REQ-L05).

---

### 4.4 Control Bar (Sort + Actions)
Status: ✅
Spec: stitch/library/SPEC.md (Component #3 Control Bar) — REQ-L03, REQ-L06, REQ-L12
Files to create/modify:
  - frontend/components/library/LibraryControlBar.tsx — (create)
  - frontend/app/bookmarks/page.tsx — wire LibraryControlBar, remove old inline sort/action buttons
  - [x] 4.4.1 Create LibraryControlBar.tsx: horizontal bar in same row as pill tabs. Flex layout with items centered. (Combined into LibraryControls.tsx)
  - [x] 4.4.2 Sort dropdown: inline text label "Sort by:" with styled select. Options: Date Added, Published (Newest/Oldest), Title (A-Z/Z-A) — REQ-L03.
  - [x] 4.4.3 "Sync to Drive" button: visible only when `selectedList !== "All"`. `bg-surface-card text-foreground-secondary rounded-full` with Cloud icon. onClick triggers onExport — REQ-L12.
  - [x] 4.4.4 Delete list button: visible only when `selectedList !== "All"`. Trash2 icon, `text-foreground-muted hover:text-red-600`. onClick triggers onDeleteList — REQ-L06.
  - [ ] 4.4.5 Wire into bookmarks/page.tsx: pass props to LibraryControls. (Deferred per instructions — do NOT modify bookmarks/page.tsx)
Validator notes: sort and action controls in one row; warm surface, no borders; "Sync to Drive" and delete only visible for specific lists; sort options match REQ-L03.

---

### 4.5 LibraryPaperCard
Status: ✓
Spec: stitch/library/SPEC.md (Component #4 Library Paper Card) — REQ-L04, REQ-L08, REQ-L09, REQ-L10, REQ-L11, E-019, E-020
Files to create/modify:
  - frontend/components/library/LibraryPaperCard.tsx — (create, per E-020 resolution)
  - frontend/app/bookmarks/page.tsx — replace PaperCard with LibraryPaperCard
  - [x] 4.5.1 Create LibraryPaperCard.tsx: new warm component (E-020 — do not restyle existing PaperCard). Surface: `bg-surface-card rounded-2xl p-5 shadow-warm-sm`. No structural borders.
  - [x] 4.5.2 Category chip: pill-shaped (`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest`), accent background for primary category, warm muted for others — REQ-L04.
  - [x] 4.5.3 List membership badges: small pills showing which lists the paper belongs to. Style: `bg-accent/10 text-accent rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide` — REQ-L08.
  - [x] 4.5.4 Paper title: Inter semibold, hover → accent color. Clickable, navigates to `/paper/{arxiv_id}` — REQ-L09.
  - [x] 4.5.5 Abstract snippet: 3-line clamp (`line-clamp-3`), body font (Inter), `text-foreground-secondary`, relaxed line-height — REQ-L04.
  - [x] 4.5.6 Reading time label: uppercase tracking, `text-[10px]`, `text-foreground-muted`. Author metadata in italic — REQ-L04.
  - [x] 4.5.7 "Full Details" link: accent-colored text link with arrow (`→`), navigates to `/paper/{arxiv_id}` — REQ-L09.
  - [x] 4.5.8 Bookmark icon: filled bookmark icon (BookmarkButton reuse or standalone). Warm accent color when bookmarked. Toggle removes bookmark via `removeBookmark` — REQ-L10.
  - [x] 4.5.9 Queue icon button: small icon button (ListPlus or similar) adjacent to bookmark icon (E-019 resolution). Adds paper to reading queue. Accent color on hover. — REQ-L11.
  - [ ] 4.5.10 Wire into bookmarks/page.tsx: replace `<PaperCard>` with `<LibraryPaperCard>` in the grid. Pass paper data, list info, and action handlers. Grid layout: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`.
Validator notes: new component (not restyled PaperCard, per E-020); warm surface, no borders; category chip + list badges both present; bookmark + queue icons side by side (E-019); title links to detail (REQ-L09); 3-column responsive grid (REQ-L01).

---

### 4.6 Empty States
Status: ✓
Spec: stitch/library/SPEC.md (Components #5 Empty State, #7 Export Status Banner) — REQ-L16, REQ-L17
Files to create/modify:
  - frontend/components/library/LibraryEmptyStates.tsx — (created)
  - frontend/app/bookmarks/page.tsx — wire empty states, replace current dark empty state
  - [x] 4.6.1 Create LibraryEmptyStates.tsx with two exported components: LibraryEmptyState and LibraryEmptyList.
  - [x] 4.6.2 "no-bookmarks" variant (REQ-L16): editorial serif layout — "Your library" in Newsreader font-light, "awaits." in Newsreader font-bold italic. Subtitle in italic body font, foreground-muted. "Browse Papers" CTA button: accent-colored, pill-shaped (`rounded-full`), navigates to `/dashboard`.
  - [x] 4.6.3 "empty-list" variant (REQ-L17): editorial serif layout — list-specific empty message. No CTA button (user adds from card context).
  - [x] 4.6.4 Both variants: generous vertical padding (`py-24`/`py-16`), centered text, warm tokens only.
  - [x] 4.6.5 Wire into bookmarks/page.tsx: show LibraryEmptyState when `papers.length === 0 && selectedList === "All"`. Show LibraryEmptyList when `papers.length === 0 && selectedList !== "All"`. Old dark empty state div removed.
Validator notes: editorial serif pattern (Newsreader mixed-weight); warm surface, dashed border; two distinct variants for global empty vs list-specific empty; "Browse Papers" CTA navigates to dashboard.

---

### 4.7 Google Drive Auth Panel
Status: ✓
Spec: stitch/library/SPEC.md (Component #6 Google Drive Auth Panel) — REQ-L12, REQ-L13, REQ-L14
Files to create/modify:
  - frontend/components/library/GDriveAuthPanel.tsx — (created)
  - frontend/app/bookmarks/page.tsx — wire GDriveAuthPanel, replace current dark auth panel
  - [x] 4.7.1 Create GDriveAuthPanel.tsx: warm card surface (`bg-surface-card rounded-2xl p-6 shadow-warm-sm`). Cloud icon in `bg-accent/15 rounded-xl p-2`. No structural borders.
  - [x] 4.7.2 Title: "Google Drive Authentication" in bold, `text-foreground`. Subtitle: description text in `text-foreground-secondary`.
  - [x] 4.7.3 Step 1: numbered step indicator (`w-6 h-6 bg-surface-inset rounded-full`). Auth link in accent color with ExternalLink icon — REQ-L13.
  - [x] 4.7.4 Step 2: same numbered step indicator. Auth code input: `bg-surface-inset rounded-xl px-4 py-2 text-foreground focus:ring-2 focus:ring-accent/30`. No dark backgrounds — REQ-L13.
  - [x] 4.7.5 "Complete Auth" button: accent-colored (`bg-accent text-on-accent rounded-full px-6 py-2 font-medium`). Disabled state: `opacity-50 cursor-not-allowed`.
  - [x] 4.7.6 Dismiss button: X icon, `text-foreground-muted hover:text-foreground`.
  - [x] 4.7.7 Export status banner (REQ-L14): ExportStatusBanner component — success (`bg-green-50 text-green-700`), error (`bg-red-50 text-red-700`). Dismiss button.
  - [x] 4.7.8 Wire into bookmarks/page.tsx: show GDriveAuthPanel when `authUrl` is non-null. Show ExportStatusBanner when `exportStatus` is non-null and `authUrl` is null. Old dark auth panel and status banner removed.
Validator notes: warm card surface, no dark tokens; numbered steps with surface-inset circles; auth input uses surface-inset background; CTA uses accent; status banner uses green-50/red-50 (warm-compatible) not green-500/10 dark pattern.

---

### 4.8 Integration + Wiring
Status: ✓
Spec: stitch/library/SPEC.md (all components)
Files to modify:
  - frontend/app/bookmarks/page.tsx — final assembly
  - [x] 4.8.1 Assemble all components in bookmarks/page.tsx in correct order: LibraryHero → LibraryControls → (GDriveAuthPanel if authUrl) → (ExportStatusBanner if exportStatus) → (LibraryEmptyState or card grid). Loading state uses warm spinner (`border-accent`, `text-foreground-muted`) — REQ-L15.
  - [x] 4.8.2 Remove old PaperCard import, old lucide icons, RippleButton. Add imports for all new library components: LibraryHero, LibraryControls, LibraryPaperCard, LibraryEmptyStates, GDriveAuthPanel + ExportStatusBanner.
  - [x] 4.8.3 Verify no dark tokens remain: grep for `zinc`, `indigo`, `text-white`, `bg-black`, `prose-invert` — zero matches.
  - [x] 4.8.4 Verify build: `tsc --noEmit` and `next build` both pass with zero errors.
  - [x] 4.8.5 Added handleAddToQueue function + useRouter for navigation. All props correctly typed.
Validator notes: all 7 sub-components wired; no dark tokens in final file; build passes; visual coherence with queue and dashboard pages.

---

## Phase 5: Discovery / Search Page
SPEC: stitch/discovery/SPEC.md
Functional requirements: stitch/discovery/FUNCTIONAL_REQUIREMENTS.md (REQ-S01 through REQ-S18)
Dependencies: Phase 1–2 complete (design tokens, fonts, shell, nav)
Resolved escalations: E-S01 (category list from hardcoded categoryColorMap), E-S02 (combined sort dropdown), E-S03 (hero-only search input)

### 5.1 Page Shell + Token Swap
Status: ✓
Spec: stitch/discovery/SPEC.md (overall layout — hero, filter bar, results grid)
Files to modify:
  - frontend/app/research/page.tsx — full token swap and layout restructure
  - [x] 5.1.1 Remove all dark/cool tokens from research/page.tsx: replace `text-white`, `bg-zinc-*`, `border-zinc-*`, `text-indigo-*`, `focus:ring-indigo-*` with warm design tokens (`bg-background`, `bg-surface-card`, `text-foreground`, `text-foreground-muted`, `text-accent`, etc.).
  - [x] 5.1.2 Restructure outermost layout: apply `bg-background` on outer div, generous whitespace (`px-12 pt-8 pb-24` — matching queue/dashboard/library pattern), `space-y-10` between major sections (hero, filters, results grid).
  - [x] 5.1.3 Keep all existing state hooks (query, papers, loading, hasSearched) and all API calls (handleSearch, URL sync via searchParams) intact. Only restructure JSX and swap tokens.

---

### 5.2 Search Hero (Featured Surface)
Status: ✓
Spec: stitch/discovery/SPEC.md (Component #1 Search Hero) — REQ-S01, REQ-S05, REQ-S08, REQ-S14, REQ-S17
Files to create/modify:
  - frontend/components/discovery/SearchHero.tsx — (create)
  - frontend/app/research/page.tsx — wire SearchHero
  - [x] 5.2.1 Create SearchHero.tsx: deep forest-green panel (`bg-surface-featured`). This is the single featured surface on the search page.
  - [x] 5.2.2 "DISCOVER" label: uppercase, `tracking-widest`, `text-[10px]`, `font-bold`, white/60 on the green surface.
  - [x] 5.2.3 Mixed-weight serif headline: "Search your" in Newsreader font-extralight, "research library" in Newsreader font-bold italic. Both in white on green.
  - [x] 5.2.4 Subtitle: italic serif (Newsreader italic) below headline, in white/80.
  - [x] 5.2.5 Large search input: white bg, rounded-xl, warm shadow, accent focus ring. Search icon left, accent-colored search button right. autoFocus for REQ-S17.
  - [x] 5.2.6 Operator hint chips: small warm-muted chips below input showing `category:cs.AI`, `after:2024`, `author:Name`.
  - [x] 5.2.7 Wire into research/page.tsx: pass query, setQuery, onSearch, loading as props.

---

### 5.3 Search Filters
Status: ✓
Spec: stitch/discovery/SPEC.md (Component #2 Search Filter Bar) — REQ-S04, REQ-S06, REQ-S07
Files to create/modify:
  - frontend/components/discovery/SearchFilters.tsx — (create)
  - frontend/app/research/page.tsx — wire SearchFilters
  - [x] 5.3.1 Create SearchFilters.tsx: horizontal bar on `bg-surface-card rounded-2xl p-4 shadow-warm-sm`. No structural borders.
  - [x] 5.3.2 Category dropdown: select element with options from categoryColorMap keys (E-S01). `bg-surface-inset rounded-lg` styling.
  - [x] 5.3.3 Date range: start date and end date inputs. `bg-surface-inset rounded-lg` styling. type="date" native inputs.
  - [x] 5.3.4 Sort dropdown: "Relevance", "Date: Newest", "Date: Oldest" options. `bg-surface-inset rounded-lg`.
  - [x] 5.3.5 Clear filters button: `text-accent` text button, visible only when filters are active.
  - [x] 5.3.6 Wire into research/page.tsx: pass filter state and callbacks. Integrate with existing searchPapers API call (which accepts category, startDate, endDate, sortBy).

---

### 5.4 Search Results Cards
Status: ✓
Spec: stitch/discovery/SPEC.md (Component #3 Search Result Card) — REQ-S02, REQ-S03, REQ-S09, REQ-S10, REQ-S11, REQ-S12, REQ-S18
Files to create/modify:
  - frontend/components/discovery/SearchResultCard.tsx — (create)
  - frontend/app/research/page.tsx — replace PaperCard with SearchResultCard
  - [x] 5.4.1 Create SearchResultCard.tsx: warm card surface (`bg-surface-card rounded-2xl p-5 shadow-warm-sm`). No structural borders.
  - [x] 5.4.2 Left accent bar using category color from getCategoryColor.
  - [x] 5.4.3 Category chip: pill-shaped, uppercase tracking, category-colored background.
  - [x] 5.4.4 Paper title: Inter semibold, hover accent color. Clickable to paper detail page.
  - [x] 5.4.5 Abstract snippet: 3-line clamp, body font, `text-foreground-secondary`.
  - [x] 5.4.6 Metadata row: published date + reading time, uppercase tracking, `text-foreground-muted`.
  - [x] 5.4.7 Footer: "Read PDF" accent link, "Full Details" accent link, BookmarkButton, queue add button (ListPlus icon).
  - [x] 5.4.8 Wire into research/page.tsx: replace PaperCard with SearchResultCard in the grid. Grid: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`.

---

### 5.5 Empty + No-Results States
Status: ✓
Spec: stitch/discovery/SPEC.md (Components #5, #6) — REQ-S13, REQ-S14, REQ-S15, REQ-S16
Files to create/modify:
  - frontend/components/discovery/SearchEmptyStates.tsx — (create)
  - frontend/app/research/page.tsx — wire empty states
  - [x] 5.5.1 Create SearchEmptyStates.tsx with three exported components: SearchNoResults, SearchError, SearchSkeleton.
  - [x] 5.5.2 SearchNoResults (REQ-S15): editorial serif "No results" in Newsreader font-light, "found." in Newsreader font-bold italic. Subtitle with search tips. Operator hints list. Warm surface, dashed accent/20 border.
  - [x] 5.5.3 SearchError (REQ-S16): warm card with AlertCircle icon. Error message. "Try Again" accent button.
  - [x] 5.5.4 SearchSkeleton (REQ-S13): 3-column warm skeleton grid using existing `.skeleton` utility class. Cards with skeleton shapes matching SearchResultCard layout.
  - [x] 5.5.5 Wire into research/page.tsx: show SearchSkeleton during loading, SearchNoResults when hasSearched && papers.length === 0, SearchError on error.

---

### 5.6 Integration + Wiring
Status: ✓
Spec: stitch/discovery/SPEC.md (all components)
Files to modify:
  - frontend/app/research/page.tsx — final assembly
  - [x] 5.6.1 Assemble all components in research/page.tsx in correct order: SearchHero → SearchFilters (visible after first search or always) → (SearchSkeleton or results grid or SearchNoResults or SearchError). Loading state uses SearchSkeleton.
  - [x] 5.6.2 Add filter state: category, startDate, endDate, sortBy. Pass to searchPapers API call. Wire SearchFilters callbacks.
  - [x] 5.6.3 Remove old imports (PaperCard, SkeletonGrid, EmptyState, RippleButton). Add imports for all new discovery components: SearchHero, SearchFilters, SearchResultCard, SearchEmptyStates.
  - [x] 5.6.4 Verify no dark tokens remain: grep for `zinc`, `indigo`, `text-white`, `bg-black`, `prose-invert` — zero matches.
  - [x] 5.6.5 Verify build: `tsc --noEmit` and `next build` both pass with zero errors.

---

## Phase 7: Paper Detail Page — MOVED TO PHASE 10
Spec now approved. See Phase 10 below for the full plan.

---

## Phase 8: Analytics (Analysis) Page
SPEC: stitch/analytics/SPEC.md
Functional requirements: stitch/analytics/FUNCTIONAL_REQUIREMENTS.md (REQ-A01 through REQ-A14)
Dependencies: Phase 1-2 complete (design tokens, fonts, shell, nav)
Current file: frontend/app/analysis/page.tsx

### 8.1 Analytics Hero (Featured Stats Strip)
Status: ✓
Spec: stitch/analytics/SPEC.md (AnalyticsHero)
Files created:
  - frontend/components/analytics/AnalyticsHero.tsx
  - [x] 8.1.1 Create AnalyticsHero with forest-green featured surface (#2A4A1A), 4 stat blocks (Total Papers, Today, Yesterday, In Library, Categories), white text, uppercase tracking labels.

### 8.2 Charts Section (Papers Over Time + Category Distribution)
Status: ✓
Spec: stitch/analytics/SPEC.md (PapersOverTimeChart, CategoryDistributionChart)
Files created:
  - frontend/components/analytics/PapersOverTimeChart.tsx
  - frontend/components/analytics/CategoryDistChart.tsx
  - [x] 8.2.1 Create PapersOverTimeChart with recharts AreaChart, day/week/month granularity toggle, warm palette (terracotta fill, parchment grid, warm tooltip).
  - [x] 8.2.2 Create CategoryDistChart with recharts horizontal BarChart, warm palette, sorted by count.

### 8.3 Citation Filter Bar
Status: ✓
Spec: stitch/analytics/SPEC.md (CitationFilterBar)
Files created:
  - frontend/components/analytics/CitationFilterBar.tsx
  - [x] 8.3.1 Create CitationFilterBar with category select + date range inputs. Warm surface-inset background, no structural borders.

### 8.4 Citation Card
Status: ✓
Spec: stitch/analytics/SPEC.md (CitationCard)
Files created:
  - frontend/components/analytics/CitationCard.tsx
  - [x] 8.4.1 Create CitationCard with rank number, citation count in accent circle, title (Newsreader), arXiv ID chip, category chip, author line, and CTA button. Warm tokens throughout.

### 8.5 Analytics Page Wire-Up
Status: ✓
Spec: stitch/analytics/SPEC.md (AnalyticsPage orchestrator)
Files modified:
  - frontend/app/analysis/page.tsx — full rewrite
  - [x] 8.5.1 Rewrite analysis/page.tsx to compose AnalyticsHero, charts, CitationFilterBar, and CitationCard list. Remove all dark/cool tokens. Wire all API calls (getAnalyticsSummaryStats, getAnalyticsPapersOverTime, getAnalyticsCategoryDist, getTopCitations).
  - [x] 8.5.2 Dark token audit: zero instances of text-white (except on featured surface), bg-zinc, border-zinc, text-indigo, bg-indigo in analysis page or analytics components.

### 8.6 Patterns Page — PENDING DESIGN
Status: ⚠ blocked — no SPEC
Current file: frontend/app/patterns/page.tsx
Functional requirements: REQ-044 through REQ-048
Pages to design:
  - Pattern taxonomy overview (REQ-044, REQ-045)
  - Drill-down into category/sub-pattern (REQ-046, REQ-047)
  - Chain-of-thought reasoning view (REQ-048)
  - [ ] Placeholder — do not build until SPEC approved

---

## Phase 9: Dashboard Page
SPEC: stitch/dashboard/SPEC.md
Functional requirements: stitch/dashboard/FUNCTIONAL_REQUIREMENTS.md (REQ-D01 through REQ-D27)
Dependencies: Phase 1–2 complete (design tokens, fonts, shell, nav); Phase 3 complete (QuickPreviewPanel reusable, DateGroup pattern reusable, EmptyQueue pattern reusable)
Resolved escalations: E-009 (sparkline as chart tab), E-010 (empty + no-results at build time), E-011 (Space shortcut), E-012 (date picker warm theme), E-013 (quick-peek trigger, category filter, collapsible date groups)

### 9.1 Dashboard Page Shell Restructure
Status: ✓
Spec: stitch/dashboard/SPEC.md (overall layout — hero area, stats sidebar, filter bar, feed area)
Files to modify:
  - frontend/components/DashboardContent.tsx — full rewrite of outermost layout
  - frontend/app/dashboard/page.tsx — update Suspense fallback to warm tokens
  - [x] 9.1.1 Remove all dark/cool tokens from DashboardContent.tsx: replace `text-white`, `bg-zinc-*`, `border-zinc-*`, `text-indigo-*`, `focus:ring-indigo-*` with warm design tokens (`bg-background`, `bg-surface-card`, `text-foreground`, `text-foreground-muted`, `text-accent`, etc.). Remove dark `[color-scheme:dark]` from date inputs.
  - [x] 9.1.2 Remove the existing bento-grid layout (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4` wrapper around HeroCard/StatsTile/SparklineTile). Replace with the new Stitch layout: hero section (full-width), stats + chart row (sidebar layout), filter bar (horizontal), date-grouped feed area (main column).
  - [x] 9.1.3 Apply warm surface to page: `bg-background` on outermost div, generous whitespace (`space-y-12` between major sections, `px-12 pt-8 pb-24` on content area — matching queue page pattern).
  - [x] 9.1.4 Update dashboard/page.tsx Suspense fallback: replace `text-zinc-500` with `text-foreground-muted`.
  - [x] 9.1.5 Remove old dashboard sub-components that will be replaced: `dashboard/HeroCard.tsx`, `dashboard/StatsTile.tsx`, `dashboard/SparklineTile.tsx`, `dashboard/CategoryHeatmap.tsx`. Create new replacements in Tasks 9.2–9.4.
Validator notes: no dark tokens (bg-zinc, text-white, text-indigo, border-zinc) anywhere in DashboardContent.tsx; outermost div uses bg-background; section spacing is space-y-12 (48px); no bento grid wrapper remains.

---

### 9.2 Hero Lead Story Section
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #3 HeroLeadStory) — REQ-D03
Files to create/modify:
  - frontend/components/dashboard/HeroLeadStory.tsx — (create) replaces old HeroCard.tsx
  - frontend/components/DashboardContent.tsx — wire HeroLeadStory
  - [x] 9.2.1 Create HeroLeadStory.tsx: full-width deep forest-green panel (`bg-[#1B3022]` per SPEC primary-container). This is the single featured surface on the dashboard page — do not use this deep color anywhere else on the page.
  - [x] 9.2.2 "LEAD STORY" label: uppercase, `tracking-widest`, `text-[10px]`, `font-bold`, white/60 on the green surface.
  - [x] 9.2.3 Mixed-weight serif headline: context words (e.g., "Analysis of") in Newsreader font-light, key phrase (paper title) in Newsreader font-bold. Both in white on green. Font sizes generous (light ~2xl, bold ~3xl or larger).
  - [x] 9.2.4 Abstract excerpt: 2–3 line clamp of the paper abstract in white/80, body font (Inter), relaxed line-height.
  - [x] 9.2.5 Metadata row: estimated reading time ("12 min read"), category chips (pill-shaped, `border border-on-primary-container/10`, white text). Uppercase tracking on the reading-time label.
  - [x] 9.2.6 "Read Full Analysis" CTA button: accent-colored background (`bg-accent`), white text, pill shape (border-radius: 999px), navigates to `/paper/{arxiv_id}`.
  - [x] 9.2.7 Bookmark button on hero card: reuse BookmarkButton component, styled for white-on-green context.
  - [x] 9.2.8 Wire into DashboardContent: pass `papers[0]` (lead paper) as prop. Show only when papers.length > 0.
Validator notes: forest green is the only featured/deep surface on this page; mixed-weight serif headline uses Newsreader (not Inter); "LEAD STORY" label is uppercase with tracking; CTA uses accent color (terracotta), not green.

---

### 9.3 Activity Stats Section
Status: ✓
Spec: stitch/dashboard/SPEC.md (Components #5 TotalLibraryStat, #6 PulseScoreStat) — REQ-D15, REQ-D16
Files to create/modify:
  - frontend/components/dashboard/ActivityStats.tsx — (create) replaces old StatsTile.tsx
  - frontend/components/DashboardContent.tsx — wire ActivityStats
  - [x] 9.3.1 Create ActivityStats.tsx: two stat cards side by side. Both use warm surface tokens (`bg-surface-card`), generous padding (p-8), border-radius 16px, no structural borders, shadow-warm.
  - [x] 9.3.2 "Total in Library" card: large numeric value (display serif, bold), "TOTAL IN LIBRARY" label (uppercase, tracking-widest, text-[10px], font-bold). Trend indicator: "+412 vs last week" with trending_up/trending_down icon in accent color. Wired to `stats.total_papers`.
  - [x] 9.3.3 "Pulse Score" card: circular gauge visual (CSS-only or lightweight SVG arc), score value (e.g., "8.4") in display serif bold, "PULSE SCORE" label (same uppercase tracking pattern). Tooltip on hover explaining what pulse score represents. Wired to analytics API (new endpoint or computed from existing data).
  - [x] 9.3.4 Place adjacent to CategoryDistributionChart (right side of chart, or below hero in a stats row — follow Stitch layout).
Validator notes: exactly two stat cards; warm surface, no borders; labels uppercase with tracking; trend indicator present on Total card.

---

### 9.4 Category Distribution Chart (with Sparkline Tab)
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #4 CategoryDistributionChart) — REQ-D17 (E-009 resolution), REQ-D18
Files to create/modify:
  - frontend/components/dashboard/CategoryChart.tsx — (create) replaces old CategoryHeatmap.tsx and SparklineTile.tsx
  - frontend/components/DashboardContent.tsx — wire CategoryChart
  - [x] 9.4.1 Create CategoryChart.tsx: one component with two views, toggled by tab buttons ("By Category" and "By Day"). Tab buttons: pill-shaped, warm surface, accent on active tab.
  - [x] 9.4.2 "By Category" view (default): horizontal bar chart showing paper volume by arXiv sub-category over 30 days (cs.AI, cs.LG, cs.CL, cs.CV, etc.). Label "Last 30 days of research activity" in italic body font. Use recharts (already a dependency). Warm color palette for bars (accent for primary category, muted warm tones for others). No cool greys on axes.
  - [x] 9.4.3 "By Day" view: 14-day sparkline/time-series showing volume of papers per day for cs.AI. Line in accent color, area fill in accent/10 opacity. X-axis: date labels. Y-axis: count. Use recharts AreaChart.
  - [x] 9.4.4 Chart container: warm surface card (`bg-surface-card`), generous padding (p-8), border-radius 16px, no structural border, shadow-warm. "CATEGORY DISTRIBUTION" label (uppercase, tracking).
  - [x] 9.4.5 Wire into DashboardContent: pass `categoryData` for By Category view, `sparklineData` for By Day view. Both from existing analytics API calls (already fetched in DashboardContent).
Validator notes: two views accessible via tab toggle; "By Category" is bar chart (REQ-D18); "By Day" is sparkline/time-series (REQ-D17, E-009); recharts used; warm styling on all chart elements.

---

### 9.5 Filter Bar
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #7 FilterBar) — REQ-D09, REQ-D10, REQ-D11, REQ-D12, REQ-D13, REQ-D06
Files to modify:
  - frontend/components/DashboardContent.tsx — replace existing filter grid
  - [x] 9.5.1 Replace the current 4-column dark filter grid with a horizontal filter bar: single row, warm surface card (`bg-surface-card`), generous padding, border-radius 16px, no structural border. "FILTER BY" label (uppercase, tracking) at left edge.
  - [x] 9.5.2 Category dropdown: multi-select with checkboxes (E-013 resolution). Dropdown trigger shows "All Categories" or comma-separated active selections. Dropdown panel: warm surface, warm shadow, checkbox list of all 11 arXiv categories. Warm styling: no dark backgrounds, accent color on checked state.
  - [x] 9.5.3 Date range: replace native `<input type="date">` with DatePicker component (built in Task 9.6). Two inputs: start date, end date.
  - [x] 9.5.4 Sort selector: dropdown with three options — "Most Relevant", "Newest", "Title A–Z". Warm styled dropdown (same pattern as category).
  - [x] 9.5.5 Reset button: "Reset" text button in accent color (secondary, terracotta). Calls handleResetFilters.
  - [x] 9.5.6 Grid/list toggle: two icon buttons (grid_view / view_list) in a segmented control. Warm surface, accent on active mode. Wire to existing viewMode state.
  - [x] 9.5.7 Paper count badge: "24 NEW PAPERS" (or dynamic count) — uppercase, tracking, accent pill badge. Positioned in the filter bar or adjacent.
Validator notes: horizontal layout (not 4-column grid); multi-select category dropdown (E-013); warm surface, no dark tokens; reset button in accent color; grid/list toggle present (REQ-D06).

---

### 9.6 Date Picker Component
Status: ✓
Spec: — (E-012 resolution: warm-themed date picker, no Stitch pass)
Files to create:
  - frontend/components/DatePicker.tsx — (create) shared component
  - [x] 9.6.1 Create DatePicker.tsx: custom date picker with warm theme. Cream input surface (`bg-surface-inset`), accent borders on focus (`border-accent`), warm shadow on dropdown calendar panel (`shadow-warm`). Start/end date selection.
  - [x] 9.6.2 Calendar dropdown: warm cream surface, accent color on selected date, today indicator, month/year navigation arrows. No cool greys. Border-radius 16px on dropdown panel.
  - [x] 9.6.3 Input field styling: placeholder text in foreground-muted, selected date in foreground. Calendar icon (CalendarDays from lucide-react) as input adornment. Focus state: `ring-2 ring-accent/30 border-accent`.
  - [ ] 9.6.4 Wire into dashboard filter bar (Task 9.5.3): replace native date inputs with DatePicker for start and end dates. Update state handlers.
Validator notes: warm cream surface on input and dropdown; accent borders on focus; no native browser date picker chrome; shared component (reusable by other pages later).

---

### 9.7 Paper Feed Cards (Large + Compact)
Status: ✓
Spec: stitch/dashboard/SPEC.md (Components #9 PaperCardLarge, #10 PaperCardCompact) — REQ-D01, REQ-D04, REQ-D19, REQ-D20
Files to create/modify:
  - frontend/components/dashboard/DashboardPaperCard.tsx — (create) or restyle existing PaperCard for dashboard context
  - frontend/components/DashboardContent.tsx — wire new card variants
  - [x] 9.7.1 Large card variant (today's papers, 2-column grid): warm surface (`bg-surface-card`), no structural borders, border-radius 16px, generous padding (p-8). Category chip (pill-shaped, accent background for primary, warm muted for others). Paper title in Inter semibold, hover → accent color. Abstract snippet: 3-line clamp, body font, foreground-secondary.
  - [x] 9.7.2 Reading time label: uppercase tracking, text-[10px], foreground-muted. Author metadata in italic.
  - [x] 9.7.3 Bookmark button: reuse BookmarkButton component with warm styling. Position: top-right of card.
  - [x] 9.7.4 "Preview" button: dedicated button on each card (E-013 resolution — quick-peek trigger is a button, not hover). Pill-shaped, warm surface, accent border outline. onClick triggers quick-peek panel for that paper.
  - [x] 9.7.5 Compact card variant (yesterday's papers, 3-column grid): smaller card with category+topic label, title (Inter medium), status badge. Reduced padding. Same warm surface, no borders.
  - [x] 9.7.6 Card click navigates to detail page (`/paper/{arxiv_id}`) — REQ-D04. Cursor-pointer, hover state (tonal background shift + warm shadow appearance).
  - [x] 9.7.7 Wire into DashboardContent: render large cards for today's date group, compact cards for yesterday's date group and older.
Validator notes: two card variants (large and compact); no structural borders; warm surfaces; "Preview" button present on each card (E-013); bookmark button present (REQ-D19); click navigates to detail (REQ-D04).

---

### 9.8 Date Group Headers (Collapsible)
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #8 DateGroupHeader) — REQ-D02, E-013 resolution (collapsible)
Files to modify:
  - frontend/components/dashboard/DashboardDateGroup.tsx — NEW standalone component
  - [x] 9.8.1 Restyle date group headers: uppercase label with `tracking-[0.2em]`, small size, warm muted foreground — same editorial pattern as queue Phase 3 (Task 3.6). Date text: "TODAY MARCH 25", "YESTERDAY MARCH 24", etc.
  - [x] 9.8.2 Add collapse/expand toggle: same chevron pattern as queue DateGroup (E-013 resolution confirms collapsible). Existing `collapsedDates` state and `toggleDateCollapse` handler already in DashboardContent — keep and restyle.
  - [x] 9.8.3 Item count badge: "24 NEW PAPERS" or "{n} papers" — uppercase, tracking, warm muted text. Adjacent to date label on the right side.
  - [x] 9.8.4 Thin warm rule: horizontal divider line after the label row, using warm muted color (`border-surface-inset`). No heavy structural border.
Validator notes: uppercase with generous tracking; collapsible with existing state; item count present; thin warm rule (not heavy border); same pattern as queue page date groups.

---

### 9.9 Quick-Peek Panel (Dashboard Variant)
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #13 QuickPeekPanel, #14 AISynthesisCard, #15 MetadataDetailGrid, #16 PaperNavigationFooter) — REQ-D20, REQ-D21, REQ-D22
Files to create/modify:
  - frontend/components/dashboard/DashboardQuickPeek.tsx — NEW standalone component
  - [x] 9.9.1 Evaluate reuse of queue's QuickPreviewPanel (`frontend/components/queue/QuickPreviewPanel.tsx`). Dashboard variant is substantially different (slide-over sheet, "Deep Work Peek" label, drop cap abstract, AI Synthesis Findings section, metadata grid) — created new `frontend/components/dashboard/DashboardQuickPeek.tsx`.
  - [x] 9.9.2 "Deep Work Peek" label (uppercase, tracking) at panel top. Close button (X icon).
  - [x] 9.9.3 Category chips, mixed-weight serif headline (Newsreader extralight italic + bold for title), date/reading-time metadata.
  - [x] 9.9.4 Abstract section: drop cap styling on first letter (large serif initial cap, accent or foreground color). Body text in relaxed line-height.
  - [x] 9.9.5 AI Synthesis Findings section: deep green featured block (`bg-surface-featured`) inside the panel. Bullet-point synthesis findings. "Generate Full Deep Analysis" CTA button (accent color). Wired to `useSummarize` hook.
  - [x] 9.9.6 Metadata detail grid: 2x2 grid showing Author, Institution, Citations, Peer Review status. Uppercase labels with tracking. Gap-based cell separation (no explicit borders).
  - [x] 9.9.7 Paper navigation footer: sticky bottom of panel. "Previous Paper: {title}" and "Next Paper: {title}" with arrow icons. Props accept prevTitle/nextTitle.
  - [x] 9.9.8 Wire into DashboardContent: replace existing `<QuickPeekSheet>` usage with the new panel. Keep peekIndex, peekPaper, setPeekIndex state. "Preview" button on cards triggers setPeekIndex.
Validator notes: panel shows abstract, AI synthesis, metadata grid, prev/next nav; "Deep Work Peek" label present; drop cap on abstract; AI synthesis section uses same featured green as hero (one featured surface at a time — panel replaces hero view); prev/next wired (REQ-D21).

---

### 9.10 Empty State + No-Results State
Status: ✓
Spec: — (E-010 resolution: implement at build time, editorial serif pattern)
REQs: REQ-D26 (empty), REQ-D27 (no-results)
Files to modify:
  - frontend/components/dashboard/DashboardEmptyStates.tsx — NEW standalone component (exports DashboardEmptyState + DashboardNoResults)
  - [x] 9.10.1 Empty state (no papers in index): editorial serif headline with mixed weight — "Your research feed" in Newsreader font-extralight + "awaits." in Newsreader font-black italic. Warm palette. Generous whitespace. Inviting copy below (italic body, foreground-secondary). No dashed borders, no generic icons. "Discover Papers" CTA button in accent with Sparkles icon.
  - [x] 9.10.2 No-results state (search returned nothing): editorial serif headline — "No papers found" in font-bold. "Clear all filters" link in accent color. Warm palette, no error-like styling.
  - [x] 9.10.3 Replace existing `<EmptyState>` component usage (which uses Newspaper/SearchX icons) with the new editorial variants.
Validator notes: mixed-weight serif headlines (Newsreader); warm palette; no icons as focal point; no dashed borders; "clear filters" link on no-results state; same emotional tone as queue empty state (E-010).

---

### 9.11 Keyboard Navigation
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #12 KeyboardShortcutsOverlay) — REQ-D23, REQ-D24 (E-011 resolution), REQ-D25
Files to modify:
  - frontend/components/DashboardContent.tsx — wire keyboard nav
  - frontend/lib/useKeyboardNav.ts — add Space shortcut if not already present
  - frontend/components/ShortcutOverlay.tsx — add Space to shortcut list
  - [x] 9.11.1 Wire j/k keyboard navigation to paper feed: existing `useKeyboardNav` hook already provides `focusedIndex` state. Wired into DashboardContent with focusedPaperId derived from focusedIndex, passed to DashboardPaperCard isFocused prop. Cards apply `focus-ring` class.
  - [x] 9.11.2 Add Space key to open quick-peek (E-011 resolution): useKeyboardNav.ts already has `case " ":` (Space) that calls `onPeek(focusedIndex)`. Verified no conflict with page scroll (preventDefault called).
  - [x] 9.11.3 Update ShortcutOverlay.tsx: Space "Quick peek paper" entry already present in shortcuts list. j/k entries show "Next paper" / "Previous paper".
  - [x] 9.11.4 Keyboard shortcuts FAB: existing ShortcutOverlay trigger (? key) works. ShortcutOverlay wired in DashboardContent.
Validator notes: j/k moves focus between papers; Space opens quick-peek (E-011); focus ring visible on focused card; ? opens shortcuts overlay; Space listed in overlay.

---

### 9.12 Grid/List Layout Toggle
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #7 FilterBar — grid/list toggle) — REQ-D06
Files to modify:
  - frontend/components/DashboardContent.tsx — implement two view modes
  - [x] 9.12.1 Grid view (default): paper cards in responsive grid layout. Today's papers: 2-column (large cards via md:grid-cols-2). Yesterday and older: 3-column (compact cards via md:grid-cols-2 lg:grid-cols-3). Gap: gap-6 for today, gap-4 for older.
  - [x] 9.12.2 List view: compact single-column rows (space-y-3). All cards render as compact variant. Warm surface, spacing-based separation.
  - [x] 9.12.3 Toggle wired to viewMode state via DashboardFilterBar component. FilterBar provides warm-styled grid/list toggle buttons (accent on active, surface-inset on inactive).
  - [x] 9.12.4 Persist viewMode in localStorage so it survives page navigation. Read on mount, write on change.
Validator notes: two distinct layouts (grid with card variants, list with compact rows); toggle buttons warm-styled; viewMode persisted; grid uses responsive Tailwind grid.

---

### 9.13 Infinite Scroll + Loading Indicator
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #11 InfiniteScrollIndicator) — REQ-D07
Files to modify:
  - frontend/components/DashboardContent.tsx — restyle loading indicator
  - [x] 9.13.1 Restyle infinite scroll loading indicator: "Fetching deeper archives..." in italic serif (var(--font-display)), warm muted color (text-foreground-muted). Progress bar with accent fill (bg-accent) on warm surface track (bg-surface-inset). No zinc tokens.
  - [x] 9.13.2 Existing `useInView` + intersection observer pattern preserved. Trigger ref at bottom of feed area. Same hasMore/loading guard logic.
Validator notes: italic serif loading text; warm muted color (not zinc); accent-colored progress bar; infinite scroll functional.

---

### 9.14 Search + Refresh + URL Sync
Status: ✓
Spec: stitch/dashboard/SPEC.md (Component #2 TopAppBar search input) — REQ-D05, REQ-D08, REQ-D09, REQ-D14
Files to modify:
  - frontend/components/DashboardContent.tsx — restyle search, verify behaviors
  - [x] 9.14.1 Restyle search input: now delegated to DashboardFilterBar component which uses warm surface (`bg-surface-inset`), warm placeholder, accent focus ring. No zinc/indigo tokens.
  - [x] 9.14.2 Restyle refresh button: removed old standalone refresh button. Filter bar reset button uses accent color. Refresh is triggered by filter changes and DashboardEmptyState "Discover Papers" CTA.
  - [x] 9.14.3 Verify URL sync: existing `useEffect` that syncs filters to URL params (category, start, end, q, sort) preserved and working — REQ-D14. Category param now supports comma-separated multi-select.
  - [x] 9.14.4 Verify scroll position persistence: existing sessionStorage-based scroll restore (`dashboard_scroll`, `dashboard_papers`, `dashboard_page`) preserved — REQ-D08.
Validator notes: search input warm-styled; refresh button warm-styled; URL params update on filter change (REQ-D14); scroll position restores on return (REQ-D08).

---

## Phase 10: Paper Detail Page
SPEC: stitch/paper_detail/SPEC.md
Functional requirements: stitch/paper_detail/FUNCTIONAL_REQUIREMENTS.md (REQ-P01 through REQ-P29)
Dependencies: Phase 1–2 complete (design tokens, fonts, shell, nav); Phase 3 complete (warm card patterns, prose styling reusable)
Current file: frontend/app/paper/[id]/page.tsx (515 lines, single monolithic file — full rewrite)
Resolved escalations: E-014 (drop cap: programmatic span wrapping), E-015 (TOC scroll spy: IntersectionObserver), E-016 (prose styling: Tailwind prose with warm overrides), E-017 (back nav: router.back())

### 10.1 Paper Detail Page Shell + Token Swap
Status: ✓
Spec: stitch/paper_detail/SPEC.md (overall single-column reading layout, max-w-4xl centered, with xl+ sidebar)
Files to modify:
  - frontend/app/paper/[id]/page.tsx — full rewrite of layout, token swap, and state preservation
  - [x] 10.1.1 Remove ALL dark/cool tokens from page.tsx: replace `bg-zinc-800/50`, `bg-zinc-800/30`, `bg-zinc-800`, `bg-zinc-950/50`, `border-white/10`, `border-zinc-700`, `border-zinc-800`, `text-white`, `text-zinc-300`, `text-zinc-400`, `text-zinc-500`, `text-indigo-400`, `text-indigo-300`, `bg-indigo-500/10`, `bg-indigo-600`, `bg-indigo-500`, `shadow-indigo-*`, `glass-card` with warm design tokens (`bg-background`, `bg-surface-card`, `bg-surface-inset`, `text-foreground`, `text-foreground-secondary`, `text-foreground-muted`, `text-accent`, `bg-accent`, `shadow-warm`, etc.)
  - [x] 10.1.2 Restructure outer layout: replace `max-w-4xl mx-auto px-4 py-8` with responsive two-column layout — main content column (max-w-4xl, generous padding `px-12 pt-8 pb-24`) + right sidebar column for TOC (hidden below xl, Task 10.9). Wrap in `relative` container for sidebar positioning.
  - [x] 10.1.3 Replace back navigation: remove hardcoded `<Link href="/">Back to Dashboard</Link>`; replace with `router.back()` call using `useRouter` (E-017 resolution). Style: accent-colored text with ArrowLeft icon, `hover:-translate-x-1` transition preserved.
  - [x] 10.1.4 Implement warm loading state (REQ-P27): replace `border-indigo-500` spinner + `text-zinc-500` text with warm skeleton or pulsing accent dot + `text-foreground-muted` italic serif "Loading paper details..." text. Use `bg-background` on container.
  - [x] 10.1.5 Implement warm not-found state (REQ-P28): replace `text-white` heading + `text-zinc-500` body + `text-indigo-400` link with editorial serif pattern — mixed-weight Newsreader headline ("Paper / not found."), warm foreground, back link via `router.back()` in accent color.
  - [x] 10.1.6 Preserve all existing state hooks (paper, similarPapers, loading, summarizing, isBookmarked, isMounted, paperPatterns, showReasoning, emailStatus) and all API calls (loadPaper, checkBookmark, handleGenerateSummary, toggleBookmark, handleEmailSummary) — no logic changes, only visual restructuring.
Validator notes: zero dark tokens remaining in page.tsx; all state/hooks/API calls intact; loading and not-found states use warm tokens; back link uses router.back() not hardcoded href; layout supports sidebar column on xl+.

---

### 10.2 Paper Title Hero (Featured Surface)
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #2 Paper Title Hero)
REQs: REQ-P01 (metadata), REQ-P03 (reading time), REQ-P09 (bookmark), REQ-P10 (email), REQ-P12 (PDF link)
Files to create/modify:
  - frontend/components/paper/PaperHero.tsx — (create) extracted from page.tsx title/metadata/actions block
  - frontend/app/paper/[id]/page.tsx — import and wire PaperHero (deferred to 10.10)
  - [x] 10.2.1 Create PaperHero.tsx: deep forest-green panel (`bg-surface-featured`, `rounded-2xl`) — this is the single featured surface on the paper detail page. Generous padding (`p-8 md:p-10`). All text white-on-green.
  - [x] 10.2.2 "RESEARCH PAPER" label: uppercase, `tracking-widest`, `text-[10px]`, `font-bold`, white/60 on green surface.
  - [x] 10.2.3 Mixed-weight Newsreader headline: first two words in `font-extralight italic`, remainder in `font-bold`. Both in white on green. Font size generous (text-3xl md:text-4xl).
  - [x] 10.2.4 Metadata row: Calendar icon + date, FileText icon + arxiv_id, category chips (`bg-white/10 rounded-full px-3 py-0.5`). All white text/icons on green.
  - [x] 10.2.5 Action buttons row: Mail icon button (email summary — onEmail prop with emailStatus states: idle/sending/sent/error), Bookmark icon button (onBookmark prop with isBookmarked fill state), "Open PDF" CTA (accent-colored `bg-accent text-on-accent rounded-full`, links to pdf_url in new tab).
  - [x] 10.2.6 Reading time badge: "X MIN READ" (uppercase, tracking-wider) computed from abstract word count (~200 wpm estimated). White/60 text on green.
  - [x] 10.2.7 Wire into page.tsx: deferred to 10.10 (component-only creation per task instructions). Props: paper, isBookmarked, onBookmark, emailStatus, onEmail.
Validator notes: forest green is the only featured/deep surface on this page; mixed-weight serif headline uses Newsreader; "RESEARCH PAPER" label uppercase with tracking; action buttons white-on-green; Open PDF CTA uses accent (terracotta), not green; email button reflects all 4 status states (idle/sending/sent/error).

---

### 10.3 Abstract Section with Drop Cap
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #3 Abstract Section)
REQs: REQ-P02 (markdown + LaTeX), REQ-P01 (abstract display)
Resolved: E-014 (programmatic span wrapping for drop cap)
Files to create/modify:
  - frontend/components/paper/PaperAbstract.tsx — (create) extracted from page.tsx abstract block
  - frontend/app/paper/[id]/page.tsx — import and wire PaperAbstract
  - [x] 10.3.1 Create PaperAbstract.tsx: "ABSTRACT" section label (uppercase, `tracking-widest`, `text-[10px]`, `font-bold`, `text-foreground-muted`) with thin warm rule (`h-px bg-surface-inset`) below.
  - [x] 10.3.2 Implement programmatic drop cap (E-014 resolution): extract first character from abstract text, wrap in `<span>` with `text-5xl font-bold text-accent float-left leading-none mr-3 mt-1 select-none` styling + `fontFamily: var(--font-display)`. Remaining text rendered via ReactMarkdown. Handles edge cases: empty abstract (italic muted fallback), abstract starting with whitespace (trimStart before extraction).
  - [x] 10.3.3 Warm prose styling (E-016 resolution): wrap ReactMarkdown output in `prose` class with warm overrides — `prose-headings:text-foreground prose-p:text-foreground-secondary prose-p:leading-relaxed prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-strong:text-foreground prose-blockquote:border-accent/30`. No prose-invert or prose-indigo. Leading-relaxed body text in Inter.
  - [x] 10.3.4 Preserve full LaTeX support: remarkGfm, remarkMath, rehypeKatex plugins on ReactMarkdown. KaTeX renders with warm prose styling (no white-on-white conflicts).
Validator notes: drop cap is a programmatic span (not CSS ::first-letter); accent color on drop cap; prose class without prose-invert; LaTeX rendering intact; section label uppercase with tracking.

---

### 10.4 AI Synthesis Section
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #4 AI Synthesis Section)
REQs: REQ-P04 (trigger summary), REQ-P05 (progress), REQ-P06 (render summary), REQ-P07 (regenerate), REQ-P08 (notification), REQ-P29 (empty state)
Files to create/modify:
  - frontend/components/paper/AISynthesisSection.tsx — (create) extracted from page.tsx AI summary block
  - frontend/app/paper/[id]/page.tsx — import and wire AISynthesisSection
  - [x] 10.4.1 Create AISynthesisSection.tsx: card surface panel (`bg-surface-card rounded-2xl shadow-warm-sm`). No structural borders.
  - [x] 10.4.2 Header row: Sparkles icon in accent color + "AI SYNTHESIS" label (uppercase, tracking-widest, text-[10px], font-bold) + "Regenerate Analysis" button (accent `bg-accent text-on-accent rounded-full px-5 py-2`). Button text: "Generate Analysis" when no summary, "Regenerate Analysis" when summary exists, "Generating..." when summarizing.
  - [x] 10.4.3 Summary content: warm prose rendering (same prose class overrides as 10.3.3). Key Contributions, Limitations, Relevance sections rendered via ReactMarkdown with remarkGfm + remarkMath + rehypeKatex.
  - [x] 10.4.4 Empty/generating state (REQ-P29): pulsing accent dot (`w-2 h-2 rounded-full bg-accent animate-ping`) during generation. Italic serif muted text: "Reasoning through the paper... this may take 30-60 seconds." when summarizing; "No AI analysis generated yet. Click Generate Analysis to start." when idle.
  - [x] 10.4.5 Status line: "Analysis completed" in `text-foreground-muted text-xs` below the summary content.
  - [x] 10.4.6 Wire into page.tsx: pass paper.generated_summary, summarizing, handleGenerateSummary as props. Preserve polling logic, timeout logic, error handling, and browser notification (REQ-P08) — all remain in page.tsx. (deferred to 10.10)
Validator notes: card surface with shadow-warm-sm (no border); Sparkles icon in accent; pulsing accent dot during generation (not indigo); warm prose rendering; all API/polling logic preserved in page.tsx.

---

### 10.5 References & Citations Section
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #5 References Section)
REQs: REQ-P14 (citations), REQ-P15 (resolved links), REQ-P16 (available locally), REQ-P17 (external links)
Files to create/modify:
  - frontend/components/paper/ReferencesSection.tsx — (create) extracted from page.tsx citations block
  - frontend/app/paper/[id]/page.tsx — import and wire ReferencesSection
  - [x] 10.5.1 Create ReferencesSection.tsx: "REFERENCES" section label (uppercase, tracking-widest, text-[10px], font-bold, text-foreground-muted) with count badge (`bg-surface-inset rounded-md px-2 py-1 text-foreground-muted font-mono text-xs`).
  - [x] 10.5.2 Citation cards: `bg-surface-card rounded-xl p-4 shadow-warm-sm`. No structural borders. Each card contains: title, authors, raw citation text, external link button.
  - [x] 10.5.3 Resolved citation titles: accent-colored link (`text-accent hover:underline`) navigating to `/paper/{resolved_id}` (REQ-P15). Unresolved titles: plain `text-foreground` span.
  - [x] 10.5.4 "Available locally" chip on resolved citations (REQ-P16): `bg-accent/15 text-accent text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded`. Replace current `bg-green-500/10 text-green-400 border border-green-500/20`.
  - [x] 10.5.5 Authors line: italic (`italic text-foreground-muted text-sm`), User icon in foreground-muted. Replace current `text-zinc-400`.
  - [x] 10.5.6 Raw citation: `text-xs text-foreground-muted italic bg-surface-inset p-2 rounded-lg`. Replace current `bg-black/20 border-zinc-800/50`.
  - [x] 10.5.7 External link button (REQ-P17): `bg-surface-inset rounded-lg text-foreground-muted hover:text-accent hover:bg-accent/10`. Group-hover opacity pattern preserved.
  - [x] 10.5.8 Wire into page.tsx: pass paper.citations as prop. Render conditionally when citations exist and length > 0.
Validator notes: count badge on section label; accent links for resolved citations; "Available locally" chip uses accent (not green); no structural borders on cards; italic authors; external link buttons present.

---

### 10.6 Detected Patterns Section
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #6 Detected Patterns Section)
REQs: REQ-P18 (confidence scores), REQ-P19 (confidence bars), REQ-P20 (agentic badge), REQ-P21 (collapsible CoT), REQ-P22 (pattern library link)
Files to create/modify:
  - frontend/components/paper/PatternsSection.tsx — (create) extracted from page.tsx patterns block
  - frontend/app/paper/[id]/page.tsx — import and wire PatternsSection
  - [x] 10.6.1 Create PatternsSection.tsx: "DETECTED PATTERNS" section label (uppercase, tracking-widest, text-[10px], font-bold, text-foreground-muted) with count badge.
  - [x] 10.6.2 Agentic/Non-Agentic badge (REQ-P20): "Agentic System" badge with Sparkles icon (`bg-accent/15 text-accent text-xs font-bold rounded-lg px-3 py-1.5`) or "Non-Agentic" badge (`bg-surface-inset text-foreground-muted`). Replace current `bg-indigo-500/10 text-indigo-300 border-indigo-500/20`.
  - [x] 10.6.3 Pattern cards: `bg-surface-card rounded-2xl p-4 shadow-warm-sm`. No structural borders. Monospace category/name in accent (`font-mono text-accent font-bold`). Confidence percentage badge.
  - [x] 10.6.4 Confidence bar visualization (REQ-P19): surface-inset track (`bg-surface-inset rounded-full h-1.5`) + accent fill (`bg-accent rounded-full h-1.5`) proportional to confidence. Replace current emerald/amber/zinc color tiers with single accent fill.
  - [x] 10.6.5 Evidence quote: `text-xs text-foreground-muted italic`. Replace current `text-zinc-500`.
  - [x] 10.6.6 Collapsible CoT reasoning (REQ-P21): keep existing toggle button (ChevronUp/Down + "Classification Reasoning (CoT)"). Restyle expanded panel: `bg-surface-inset rounded-xl border-none p-4 text-xs text-foreground-muted font-mono leading-relaxed whitespace-pre-wrap`. Replace current `bg-zinc-950/50 border-zinc-800`.
  - [x] 10.6.7 Pattern Library link (REQ-P22): accent-colored link with Layers icon (`text-accent hover:text-accent/80`). Navigate to `/patterns`. Replace current `bg-zinc-800 text-zinc-400 border-zinc-700/50`.
  - [x] 10.6.8 Wire into page.tsx: pass paperPatterns, showReasoning, setShowReasoning as props. Render conditionally when patterns exist and length > 0.
Validator notes: accent fill on confidence bars (single color, not tiered); agentic badge uses accent (not indigo); monospace category names; collapsible CoT reasoning; Pattern Library link present.

---

### 10.7 Action Footer
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #7 Action Footer)
REQs: REQ-P10 (email), REQ-P13 (timeline link), REQ-P12 (PDF link)
Files to create/modify:
  - frontend/components/paper/PaperActionFooter.tsx — (created) extracted from page.tsx footer buttons
  - frontend/app/paper/[id]/page.tsx — import and wire ActionFooter
  - [x] 10.7.1 Create ActionFooter.tsx: three centered buttons with `flex justify-center items-center gap-4` and generous top margin (`mt-16`).
  - [x] 10.7.2 "Email Summary" button (secondary): `bg-surface-card text-foreground hover:bg-surface-inset rounded-xl px-6 py-3 font-medium shadow-warm-sm`. Mail icon. Reflects all 4 emailStatus states (idle/sending/sent/error). Sent state: `bg-emerald-500 text-white`. Error state: `bg-red-500 text-white`.
  - [x] 10.7.3 "Show Timeline" button (secondary): `bg-surface-card text-foreground hover:bg-surface-inset rounded-xl px-6 py-3 font-medium shadow-warm-sm`. GitBranch icon. Navigate to `/timeline?paper={db_id}`.
  - [x] 10.7.4 "Read Full PDF" button (primary accent): `bg-accent text-on-accent hover:bg-accent-hover rounded-full px-8 py-3 font-medium shadow-warm-sm`. Opens pdf_url in new tab.
  - [x] 10.7.5 Wire into page.tsx: pass paper (for db_id, pdf_url), emailStatus, handleEmailSummary as props.
Validator notes: three buttons centered; Email and Timeline are secondary (warm surface); PDF is primary (accent rounded-full); email button has all 4 status states; timeline links to correct route.

---

### 10.8 Recommended Research Section
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #8 Recommended Research Section)
REQs: REQ-P23 (similar papers grid), REQ-P24 (recommendation card content)
Files to create/modify:
  - frontend/components/paper/RecommendedResearch.tsx — (created) lightweight paper-detail-specific card
  - frontend/app/paper/[id]/page.tsx — import and wire RecommendedResearch
  - [x] 10.8.1 Create RecommendedResearch.tsx: "RECOMMENDED RESEARCH" section label (uppercase, tracking-widest, text-[10px], font-bold, text-foreground-muted) with Lightbulb icon in `bg-accent/15 rounded-lg p-1.5`.
  - [x] 10.8.2 2-column grid (`grid grid-cols-1 md:grid-cols-2 gap-6`). Paper cards on warm surface (`bg-surface-card rounded-xl shadow-warm-sm p-5`). No structural borders.
  - [x] 10.8.3 Card content (REQ-P24): category chip (pill-shaped, `bg-surface-inset text-foreground-muted rounded-full px-2.5 py-0.5 text-[10px]`), paper title (`text-foreground font-medium hover:text-accent`), date + reading time estimate.
  - [x] 10.8.4 Card title is Link to `/paper/{arxiv_id}`. Hover state: shadow-warm-sm -> shadow-warm transition.
  - [x] 10.8.5 Created lightweight PaperRecommendationCard inline (DashboardPaperCard not compatible with warm editorial spec).
  - [x] 10.8.6 Wire into page.tsx: pass similarPapers as prop. Render conditionally when similarPapers.length > 0. Wrap in ErrorBoundary (preserve existing pattern).
Validator notes: 2-column grid; warm card surface, no borders; category chip present; title hover → accent; Lightbulb icon in accent; ErrorBoundary preserved.

---

### 10.9 Sticky TOC Sidebar
Status: ✓
Spec: stitch/paper_detail/SPEC.md (Component #9 Sticky TOC Sidebar)
REQs: REQ-P26 (sticky TOC on xl+)
Resolved: E-015 (IntersectionObserver scroll spy)
Files to create/modify:
  - frontend/components/paper/PaperTOC.tsx — (create) new component
  - frontend/app/paper/[id]/page.tsx — wire TOC into right column
  - [x] 10.9.1 Create PaperTOC.tsx: sticky right column (`sticky top-24`) visible on xl+ screens (`hidden xl:block`). Positioned in the sidebar column created in 10.1.2.
  - [x] 10.9.2 Section links: Abstract, AI Analysis, References, Patterns, Recommendations. Each link scrolls to its section via `scrollIntoView({ behavior: 'smooth' })`. Clicking sets the active section.
  - [x] 10.9.3 Implement IntersectionObserver scroll spy (E-015 resolution): observe all section heading elements. When a section enters the viewport (rootMargin `-20% 0px -70% 0px`), set it as active. Use `useEffect` with cleanup to disconnect observer.
  - [x] 10.9.4 Active section styling: accent color text (`text-accent`) + left border (`border-l-2 border-accent pl-3`). Inactive: `text-foreground-muted border-transparent hover:text-foreground-secondary`. Transition on color and border.
  - [x] 10.9.5 Add `id` attributes to each major section in page.tsx (abstract, ai-synthesis, references, patterns, recommendations) to serve as scroll-spy targets.
  - [x] 10.9.6 Wire into page.tsx: render PaperTOC in the right sidebar column. Pass section IDs and labels.
Validator notes: sticky positioning with top offset for fixed TopBar; hidden below xl; IntersectionObserver (not scroll event listener); accent color + left border on active; smooth scroll on click; section IDs present on all major sections.

---

### 10.10 Integration + Final Wiring
Status: ✓
Spec: stitch/paper_detail/SPEC.md (all components)
REQs: all REQ-P01 through REQ-P29
Files to modify:
  - frontend/app/paper/[id]/page.tsx — final assembly
  - [x] 10.10.1 Wire all extracted components (PaperTitleHero, AbstractSection, AISynthesisSection, ReferencesSection, PatternsSection, ActionFooter, RecommendedSection, TableOfContents) back into page.tsx. Verify import paths and prop passing.
  - [x] 10.10.2 Verify all state management: paper, similarPapers, loading, summarizing, isBookmarked, isMounted, paperPatterns, showReasoning, emailStatus states remain in page.tsx. All API calls (loadPaper, checkBookmark, handleGenerateSummary, toggleBookmark, handleEmailSummary) remain in page.tsx. No logic duplication.
  - [x] 10.10.3 Test loading state: warm skeleton/pulsing indicator visible during initial fetch.
  - [x] 10.10.4 Test not-found state: editorial serif pattern with back link via router.back().
  - [x] 10.10.5 Test empty analysis state (REQ-P29): "Analyze with Gemini" CTA visible when no summary; pulsing dot during generation.
  - [x] 10.10.6 Test email flow (REQ-P11): idle → sending (spinner) → sent (check icon, green) → idle after 3s. Error path: → error (red) → idle after 3s.
  - [x] 10.10.7 Test bookmark toggle (REQ-P09): icon fill state toggles correctly.
  - [x] 10.10.8 Verify ErrorBoundary wrapping: entire page and recommended section both wrapped.
  - [x] 10.10.9 Verify responsive behavior: single column below xl (TOC hidden, full-width content); two columns on xl+ (content + TOC sidebar).
  - [x] 10.10.10 Final dark token audit: grep page.tsx and all new components for bg-zinc, text-zinc, bg-indigo, text-indigo, text-white (outside of on-featured context), border-zinc, glass-card, prose-invert. Zero matches required.
Validator notes: all 10 extracted components render; all state/hooks/API preserved; loading/not-found/empty states functional; email 4-state flow works; bookmark toggles; no dark tokens; responsive layout; ErrorBoundary intact.

---

## Phase 11: Chat (Deep Dive) Page

### 11.1 Page Shell + Token Swap
Status: ✓
Spec: stitch/chat/SPEC.md
Current file: frontend/app/chat/page.tsx
  - [x] 11.1.1 Replace all dark tokens (bg-zinc-*, bg-indigo-*, text-white, text-zinc-*) with warm design tokens
  - [x] 11.1.2 Set up full-height flex column layout: scrollable message area (flex-1) + sticky input bar
  - [x] 11.1.3 Remove inline dark-theme color classes; use CSS variable-based tokens throughout

### 11.2 Chat Hero / Welcome State
Status: ✓
  - [x] 11.2.1 Create frontend/components/chat/ChatHero.tsx — featured-surface hero with mixed-weight serif headline, subtitle, and suggested prompts grid
  - [x] 11.2.2 Use bg-surface-featured for hero panel; text-on-featured for content
  - [x] 11.2.3 Implement 2x2 suggested prompt grid using surface-card cards with accent hover
  - [x] 11.2.4 Wire prompt click to handleSubmit

### 11.3 Chat Message Components
Status: ✓
  - [x] 11.3.1 Create frontend/components/chat/ChatMessageBubble.tsx — user bubbles (surface-inset, right-aligned) and AI bubbles (surface-card, left-aligned)
  - [x] 11.3.2 AI messages: full markdown rendering with ReactMarkdown + remarkGfm + remarkMath + rehypeKatex
  - [x] 11.3.3 AI messages: optional source citations section with ChatSourceCard sub-component
  - [x] 11.3.4 Create frontend/components/chat/ChatSourceCard.tsx — inline citation with FileText icon, paper text, /paper/[id] link
  - [x] 11.3.5 Create frontend/components/chat/ChatTypingIndicator.tsx — animated dots with surface-card bg and accent dots

### 11.4 Chat Input Bar
Status: ✓
  - [x] 11.4.1 Create frontend/components/chat/ChatInputBar.tsx — surface-card bg input with warm shadow, accent send button
  - [x] 11.4.2 Disabled state when loading or empty; keyboard submit on Enter

### 11.5 Integration + Dark Token Audit
Status: ✓
  - [x] 11.5.1 Rewrite frontend/app/chat/page.tsx to compose ChatHero, ChatMessageBubble, ChatTypingIndicator, ChatInputBar
  - [x] 11.5.2 Preserve all existing functionality: message state, API call, scroll-to-bottom, error handling
  - [x] 11.5.3 Dark token audit: grep for zinc, indigo, slate, gray, white, black in all chat components; replace any remaining dark tokens
  - [x] 11.5.4 Verify tsc --noEmit and next build pass

---

## Phase 12: Timeline Page
Last updated: 2026-03-28

### 12.1 Timeline Page — Warm Design Overhaul
Status: ✓
Spec: stitch/timeline/SPEC.md
Functional requirements: stitch/timeline/FUNCTIONAL_REQUIREMENTS.md
Current files:
  - frontend/app/timeline/page.tsx
  - frontend/components/TimelineGraph.tsx
  - frontend/components/TimelineNode.tsx
  - frontend/components/TimelineDetailPanel.tsx
  - frontend/lib/timelineCategoryColors.ts (new — warm edge colors)
Tasks:
  - [x] 12.1.1 Create stitch/timeline/FUNCTIONAL_REQUIREMENTS.md (REQ-062 through REQ-071)
  - [x] 12.1.2 Create stitch/timeline/SPEC.md (7 component specs, category color map, interaction patterns)
  - [x] 12.1.3 Restyle page.tsx: sticky search bar (card surface, warm border, accent button), featured-surface hero with Newsreader headings, warm suggestion cards, warm loading/error/empty states. Removed all dark tokens (bg-zinc-*, text-white, bg-indigo-*, border-white/*)
  - [x] 12.1.4 Restyle TimelineGraph.tsx: card surface container with shadow-warm, warm dot-grid background (#D5CFC4 dots), warm minimap (inset surface bg, warm border), warm controls toolbar, warm stats pill. Created lib/timelineCategoryColors.ts with warm-compatible edge colors (brown, mauve, teal, sage, gold, clay, plum)
  - [x] 12.1.5 Restyle TimelineNode.tsx: card-surface node backgrounds, warm borders (#D5CFC4), accent color for seminal nodes (ring, glow, pulsing dot, handles), inset-surface category badges, foreground/foreground-muted text. Ghost nodes use foreground-muted dashed border
  - [x] 12.1.6 Restyle TimelineDetailPanel.tsx: card-surface background with shadow-warm, accent-colored seminal badge, inset-surface category/citation badges, accent-colored primary CTA and bookmark border, Newsreader display font for title and buttons
  - [x] 12.1.7 Year marker nodes: font-display, foreground-muted color, opacity 0.1
  - [x] 12.1.8 Dark token audit — confirmed zero remaining dark tokens (no bg-zinc-*, bg-black, text-white, bg-indigo-*, #131315, #201f22, #0e0e10, #353437, #c0c1ff, #ffb95f, #908fa0, #e5e1e4, #c7c4d7, #464554, #2a2a2c)
  - [x] 12.1.9 TypeScript check: PASS (npx tsc --noEmit)
  - [x] 12.1.10 Next.js build: PASS (npx next build)
Validator notes:
  [PASS] Warm surfaces: all containers use var(--color-surface-card), var(--color-surface-inset), var(--color-background) — no dark hex values
  [PASS] Featured surface: hero uses var(--color-surface-featured) (#2A4A1A) — single use on page
  [PASS] Accent: search button, seminal node borders/handles/glow, CTA buttons, high-impact labels all use var(--color-accent) (#C4614A)
  [PASS] Typography: Newsreader (--font-display) for hero title, seminal title, detail title, CTA buttons. Inter (--font-body) for body text
  [PASS] No dark remnants: grep confirms zero instances of bg-zinc, bg-black, text-white, bg-indigo, #131315, #201f22 in timeline files
  [PASS] Functionality preserved: ReactFlow graph, node types, edge computation, layout algorithm, detail panel, import, bookmark all unchanged
  [PASS] Build: tsc --noEmit and next build both pass clean
  Overall: PASS

---

## Phase 13: Settings Page
Last updated: 2026-03-28

### 13.1 Settings Page — Warm Design Overhaul
Status: ✓
Spec: stitch/settings/SPEC.md
Functional requirements: stitch/settings/FUNCTIONAL_REQUIREMENTS.md
Current file: frontend/app/settings/page.tsx
Tasks:
  - [x] 13.1.1 Create stitch/settings/FUNCTIONAL_REQUIREMENTS.md (REQ-S01 through REQ-S08)
  - [x] 13.1.2 Create stitch/settings/SPEC.md (token map, layout, dark token removal checklist)
  - [x] 13.1.3 Token swap in page.tsx: replace all dark tokens (bg-zinc-*, text-white, border-zinc-*, bg-indigo-*, focus:ring-indigo-*) with warm design tokens per SPEC.md
  - [x] 13.1.4 Layout refinement: separate section cards for Research Interests and Notifications, rounded-xl, shadow-warm-sm, warm borders
  - [x] 13.1.5 Typography: Newsreader serif (font-display) for page title and section headings, Inter for body/labels
  - [x] 13.1.6 Save button: accent bg, on-accent text, font-display, shadow-warm-sm
  - [x] 13.1.7 Dark token audit: confirmed zero remaining dark tokens (grep for zinc, indigo, slate, text-white, bg-black, bg-gray returned 0 matches)
  - [x] 13.1.8 Verify tsc --noEmit and next build pass
  - [x] 13.1.9 Functionality preserved: keywords input, email load, frequency select, save, toast notifications
Validator notes:
  [PASS] Warm surfaces: page bg-background, cards bg-surface-card, inputs bg-surface-inset
  [PASS] No featured surface: settings is a utility page, no hero or featured surface used (per spec)
  [PASS] Accent: save button uses bg-accent/hover:bg-accent-hover/text-on-accent, focus rings use focus:ring-accent
  [PASS] Typography: font-display (Newsreader) for page title, section headings, save button. Inter for labels/body
  [PASS] No dark remnants: grep confirms zero instances of bg-zinc, text-white, border-zinc, bg-indigo, focus:ring-indigo in settings/page.tsx
  [PASS] Functionality preserved: keywords input, email load, frequency select, save with loading state, toast notifications
  [PASS] Build: tsc --noEmit and next build both pass clean (13/13 routes)
  Overall: PASS

---

## Escalations

### E-005 — Root route ownership
Status: ✓ RESOLVED — Option A: `/` is permanent queue alias.
Phase: 3 | Task: 3.1
Question: The root route `/` currently renders `<QueuePage />` directly (frontend/app/page.tsx). In the new nav model, the four primary nav items are Library, Queue, Collections, Archive — there is no "Dashboard" or "Home" in the primary rail. Should `/` remain an alias for queue, or should it become a distinct landing/dashboard experience once Phase 9 is designed?
Options:
  A) Keep `/` as alias for queue indefinitely. Simple; no dedicated home page.
  B) Keep `/` as queue alias now; change to a real landing page when Phase 9 (Dashboard) is specced. Requires a routing change later.
  C) Make `/` redirect to `/queue` immediately (cleaner separation but adds a redirect hop).
Blocking: 3.1.1 (root route decision) and Phase 9 planning.

### E-006 — Advanced filter panel contents (queue page)
Status: ✓ RESOLVED — Option B: comprehensive filter sheet (status, source, date, category). TopBar tabs = presets. Reference: stitch/queue/reading_queue_expanded_filters/.
Phase: 3 | Task: 3.5
Question: The filter icon button in the sort/filter bar (SPEC Component #6) triggers an advanced filter panel whose contents are never shown in any Stitch output. SPEC open question #2 notes this is unresolved. The panel needs to handle at minimum: read-status multi-select (All / Unread / Reading / Read / Skipped — currently handled by top-bar tabs) and possibly date-range filter.
Options:
  A) Panel contains: date range filter + any filters not covered by source pills and status tabs. Status tabs in TopBar remain the primary read-status control.
  B) Panel is a comprehensive filter sheet with all filter dimensions: status, source, date range, category. Status tabs in TopBar become a shortcut to filter presets.
  C) Defer the filter panel entirely until a Stitch design is produced for the expanded filter state (stitch/queue/reading_queue_expanded_filters/ exists but was not reviewed in SPEC.md).
Blocking: 3.5.3 (filter panel implementation).
Note: stitch/queue/reading_queue_expanded_filters/ exists and should be reviewed before resolving this escalation.

---

## Phase 9: Dashboard Page — Validation

Run date: 2026-03-26
Agent: behavior-validator

### Visual / Token Checks

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | No dark tokens in DashboardContent.tsx | PASS | Zero matches for bg-zinc, bg-gray-9, bg-black, text-white, border-zinc, text-indigo, bg-indigo |
| 2 | No dark tokens in active dashboard/* components | PASS (WARN) | Active components clean. Legacy dead files (CategoryHeatmap, SparklineTile, HeroCard, StatsTile) still contain dark tokens but are NOT imported by DashboardContent. Recommend deletion. |
| 3 | HeroLeadStory forest green | PASS | Uses `bg-[#1B3022]` |
| 4 | Mixed-weight serif headline in hero | PASS | `font-light italic` + `font-bold` spans with `font-display` class |
| 5 | CategoryChart uses recharts | PASS | Imports BarChart, AreaChart from recharts; uses `tokens.colors.accent` for warm palette |

### Functional Capability Checks

| # | REQ | Check | Result | Notes |
|---|-----|-------|--------|-------|
| 6 | D01 | Browse feed with title, category, date | PASS | DashboardPaperCard renders all three |
| 7 | D02 | Collapsible date groups | PASS | DashboardDateGroup with isCollapsed/onToggle + collapsedGroups state |
| 8 | D03 | Lead story with abstract, reading time | PASS | HeroLeadStory renders papers[0], estimateReadTime, summary |
| 9 | D05 | Manual refresh | PASS | handleRefresh resets page and re-fetches |
| 10 | D06 | Grid/list toggle | PASS | viewMode state + onViewModeChange wired to DashboardFilterBar |
| 11 | D09 | Search | PASS | searchQuery state + onSearchChange wired |
| 12 | D10 | Category filter (multi-select) | PASS | selectedCategories + toggleCategory in DashboardFilterBar |
| 13 | D11 | Date range | PASS | DatePicker wired via onDateChange(start, end) |
| 14 | D12 | Sort | PASS | sortBy state + 3 options (relevance, newest, title) |
| 15 | D13 | Reset filters | PASS | onReset = handleResetFilters clears all filter state |
| 16 | D17 | Sparkline (By Day tab) | PASS | CategoryChart "By Day" tab renders DailyAreaChart with 14-day data |
| 17 | D18 | Category breakdown | PASS | CategoryChart "By Category" tab renders CategoryBarChart |
| 18 | D19 | Bookmark | PASS | onBookmark prop on DashboardPaperCard + HeroLeadStory |
| 19 | D20 | Quick-peek | PASS | DashboardQuickPeek wired with peekPaper state |
| 20 | D21 | Prev/next in peek | PASS | onPrev/onNext with hasPrev/hasNext + title previews |
| 21 | D23 | Keyboard j/k | PASS | useKeyboardNav hook with j/k keydown, focusedIndex state |
| 22 | D26 | Empty state | PASS | DashboardEmptyState when papers.length===0 && !searchQuery |
| 23 | D27 | No-results state | PASS | DashboardNoResults when papers.length===0 && searchQuery |

### Summary

- **23 PASS**, **1 WARN**, **0 FAIL**
- WARN: Legacy dashboard components (CategoryHeatmap.tsx, SparklineTile.tsx, HeroCard.tsx, StatsTile.tsx) contain dark tokens (bg-zinc, text-indigo, bg-indigo, text-white) but are dead code — not imported by DashboardContent.tsx. Recommend deleting these files in a cleanup pass.
- No blockers for Phase 10.

---

## Phase 10 Validation: Paper Detail Page

Date: 2026-03-28
Agent: behavior-validator

### Visual / Token Checks

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | No dark tokens in page.tsx | PASS | grep for bg-zinc, text-white, border-zinc, text-indigo, bg-indigo, prose-invert returned 0 matches |
| 2 | No dark tokens in paper/* components | WARN | text-white found in PaperActionFooter.tsx (lines 27,29) for email status feedback states (bg-emerald-500 text-white, bg-red-500 text-white). All text-white in PaperHero.tsx is acceptable (featured surface). |
| 3 | PaperHero featured surface | PASS | Uses bg-surface-featured (line 43) |
| 4 | Mixed-weight serif headline | PASS | font-extralight italic + font-bold with fontFamily var(--font-display) in PaperHero h1 |
| 5 | Drop cap in PaperAbstract | PASS | Programmatic span, text-accent, float-left (line 44) — not CSS ::first-letter |

### Functional Capability Checks

| # | Req | Check | Result | Notes |
|---|-----|-------|--------|-------|
| 6 | REQ-P01 | Paper metadata | PASS | Title (h1), date (Calendar icon), arxiv_id (FileText icon), categories (chips) all in PaperHero |
| 7 | REQ-P02 | Markdown + LaTeX in abstract | PASS | ReactMarkdown with remark-math, rehype-katex in PaperAbstract |
| 8 | REQ-P03 | Reading time | PASS | estimateReadingTime() in PaperHero, displayed with Clock icon |
| 9 | REQ-P04 | Generate summary | PASS | onGenerate prop in AISynthesisSection wired to handleGenerateSummary |
| 10 | REQ-P05 | Progress indicator | PASS | Pulsing dot (animate-ping) + italic serif text in AISynthesisSection |
| 11 | REQ-P06 | Render AI summary | PASS | ReactMarkdown with remark-math, rehype-katex in AISynthesisSection |
| 12 | REQ-P09 | Toggle bookmark | PASS | onBookmark prop in PaperHero wired to toggleBookmark in page.tsx |
| 13 | REQ-P10 | Email summary | PASS | onEmail prop in PaperHero + PaperActionFooter, wired to handleEmailSummary |
| 14 | REQ-P12 | PDF link | PASS | Open PDF CTA in PaperHero + Read Full PDF in PaperActionFooter |
| 15 | REQ-P13 | Timeline link | PASS | Show Timeline link in PaperActionFooter with href=/timeline?paper={paperId} |
| 16 | REQ-P14 | Citations displayed | PASS | ReferencesSection renders citation cards with title, authors, raw text |
| 17 | REQ-P15 | Resolved citation links | PASS | Link to /paper/${citation.resolved_id} in ReferencesSection |
| 18 | REQ-P16 | Available locally indicator | PASS | "Available locally" chip on resolved citations |
| 19 | REQ-P18 | Pattern confidence scores | PASS | PatternsSection displays confidence percentage + bar visualization |
| 20 | REQ-P21 | Collapsible CoT | PASS | showReasoning toggle with ChevronDown/ChevronUp in PatternsSection |
| 21 | REQ-P23 | Similar papers grid | PASS | RecommendedResearch with grid-cols-1 md:grid-cols-2 |
| 22 | REQ-P25 | Back link | PASS | router.back() button with ArrowLeft icon in page.tsx |
| 23 | REQ-P26 | Sticky TOC | PASS | PaperTOC with sticky top-24 + IntersectionObserver |
| 24 | REQ-P27 | Loading state | PASS | Warm spinner (border-accent, animate-spin) with serif italic text |
| 25 | REQ-P28 | Not-found state | PASS | Mixed-weight serif headline (font-extralight + font-black italic) |

### Summary

- **24 PASS**, **1 WARN**, **0 FAIL**
- WARN (Check 2): PaperActionFooter.tsx uses `text-white` on status feedback buttons (emerald sent, red error). These are transient UI states on colored backgrounds, not dark-theme tokens, but deviate from the "text-white only in PaperHero" rule. Recommend replacing with `text-on-accent` or a dedicated `text-on-status` token for consistency.
- No blockers. Paper Detail page overhaul is validated.
