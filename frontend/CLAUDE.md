# arxiv_assistant — Frontend

Next.js web UI for browsing, searching, and analyzing arXiv papers. Dark-themed with space background, glassmorphism, and motion design.

## Stack

- **Framework:** Next.js 16 with App Router (React Compiler enabled, standalone output)
- **UI:** React 19, TypeScript, Tailwind CSS v4
- **Animation:** Framer Motion, @use-gesture/react
- **3D:** Three.js via @react-three/fiber + @react-three/drei (space background)
- **Charts:** Recharts (analytics tiles, sparklines, heatmaps)
- **Math:** KaTeX via remark-math + rehype-katex
- **Markdown:** react-markdown with remark-gfm
- **Command Palette:** cmdk
- **Notifications:** sonner (toast)
- **Icons:** lucide-react

## Pages (App Router)

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — bento grid with stats tiles, paper grid, category heatmap |
| `/paper/[id]` | Paper detail with summaries, bookmarking, similar papers |
| `/research` | Semantic search exploration |
| `/chat` | RAG chat interface |
| `/bookmarks` | Saved papers with list management and Google Drive export |
| `/patterns` | Agentic patterns classification library |
| `/analysis` | Analytics dashboard with stats and heatmaps |
| `/settings` | User preferences (keywords, email, frequency) |

## Key Features

- **Command Palette (Cmd+K):** Global search and navigation via cmdk
- **Keyboard Navigation:** `j/k` item nav, `space` quick-peek, `b` bookmark, `g+letter` chord nav (g+d dashboard, g+r research, etc.), `?` shortcut overlay
- **Paper Peek Popup:** Clicking a paper title on the dashboard opens a bottom sheet with full abstract, "Analyze with Gemini" button (triggers summarization with polling), and inline AI summary. Drag-to-dismiss, prev/next navigation, swipe gestures.
- **Space Background:** Toggleable 3D (Three.js) or CSS parallax starfield
- **Page Transitions:** Framer Motion fade animations
- **Skeleton Loading:** Bento skeleton placeholders
- **Button Ripple Effect:** Radial white gradient animation on primary action button clicks
- **Category Trend Badges:** Color-coded arXiv category indicators on paper cards

## API Proxy

`app/api/[...path]/route.ts` proxies all `/api/*` requests to the FastAPI backend (`BACKEND_URL` or `INTERNAL_API_URL`, default `http://backend:8000`). Handles GET, POST, DELETE. Strips trailing slashes to prevent FastAPI redirects.

## Project Structure

```
frontend/
├── app/                        # Next.js App Router pages
│   ├── page.tsx                # Home/dashboard
│   ├── layout.tsx              # Root layout (sidebar, space bg, transitions)
│   ├── error.tsx               # Error page handler
│   ├── api/[...path]/          # API proxy to backend
│   ├── paper/[id]/             # Paper detail
│   ├── research/               # Semantic search
│   ├── chat/                   # RAG chat
│   ├── bookmarks/              # Saved papers
│   ├── patterns/               # Pattern library
│   ├── analysis/               # Analytics
│   └── settings/               # User preferences
├── components/                 # React components
│   ├── DashboardContent.tsx    # Main dashboard with filters, search, stats grid
│   ├── PaperCard.tsx           # Paper card — click title opens peek sheet, "Full Details" link for navigation
│   ├── Sidebar.tsx             # Left nav with add-paper form
│   ├── CommandPalette.tsx      # Global search/nav palette (cmdk)
│   ├── QuickPeekSheet.tsx      # Paper peek popup with abstract, AI summary, and Gemini analysis
│   ├── RippleButton.tsx        # Button with radial ripple effect on click
│   ├── BookmarkButton.tsx      # Bookmark with portal menu & list selection
│   ├── ShortcutOverlay.tsx     # Keyboard shortcut help overlay
│   ├── PageTransition.tsx      # Framer Motion page fade
│   ├── SkeletonCard.tsx        # Loading placeholders
│   ├── EmptyState.tsx          # Empty state fallback
│   ├── ErrorBoundary.tsx       # React error boundary
│   ├── LibraryContext.tsx      # Bookmark/library state context
│   ├── dashboard/              # Dashboard sub-components
│   │   ├── HeroCard.tsx        # Featured paper with tilt effect
│   │   ├── StatsTile.tsx       # Stats card with trend indicator
│   │   ├── SparklineTile.tsx   # Mini chart tiles
│   │   └── CategoryHeatmap.tsx # Paper distribution heatmap
│   ├── animations/
│   │   └── StaggerList.tsx     # Staggered animation wrapper
│   └── parallax/               # Space background system
│       ├── SpaceBackgroundClient.tsx
│       ├── SpaceBackgroundSwitcher.tsx
│       ├── SpaceBackground3D.tsx   # Three.js starfield
│       ├── SpaceBackgroundCSS.tsx  # CSS parallax fallback
│       ├── ParallaxBackground.tsx
│       ├── ParallaxLayer.tsx
│       ├── ScrollProgress.tsx
│       └── TiltCard.tsx        # Mouse-tracking tilt effect
├── lib/
│   ├── api.ts                  # API client (papers, chat, library, patterns, analytics)
│   ├── categoryColors.ts       # arXiv category color mapping & helpers
│   ├── useKeyboardNav.ts       # Keyboard navigation hook (j/k nav, space peek, g+letter chords)
│   └── useSummarize.ts         # Reusable hook for Gemini summarization with polling
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── next.config.ts
└── Dockerfile                  # Multi-stage Node 20 build
```

## Development

```bash
npm install
npm run dev       # Dev server on port 3000
npm run build     # Production build (standalone output)
```

## Configuration

Backend URL configured via `BACKEND_URL` or `INTERNAL_API_URL` env vars, defaults to `http://backend:8000` in Docker.
