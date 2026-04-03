# TypeScript Frontend Standards

These rules apply when working on files in `frontend/`.

## Next.js 16 Conventions

- App Router only. Pages go in `frontend/app/<route>/page.tsx`.
- React Server Components by default. Only add `"use client"` when the component uses hooks, event handlers, or browser APIs.
- API proxy at `app/api/[...path]/route.ts` handles all backend communication — never bypass it.
- Standalone output mode for Docker builds.

## React 19

- Functional components only. No class components.
- React Compiler is enabled — avoid manual `useMemo`/`useCallback` unless profiler shows a problem.
- Use named exports for all components.
- Props type: `type ComponentNameProps = { ... }` (not interface).
- Colocate component-specific types in the same file.

## API & Data Fetching

- All API calls go through `lib/api.ts`. Never use raw `fetch()` in components.
- When adding a new backend endpoint, add the corresponding function in `lib/api.ts`.
- Handle loading and error states explicitly. Use skeleton components for loading.

## Styling

- Tailwind CSS v4. No inline styles or CSS modules.
- Dark theme by default — use CSS variables defined in `globals.css`.
- Glassmorphism pattern: `backdrop-blur`, semi-transparent backgrounds.
- Use Framer Motion for animations and transitions — no raw CSS transitions on interactive elements.

## Component Architecture

- Dashboard: `app/page.tsx` → `DashboardContent.tsx` → sub-components in `components/dashboard/`.
- Paper cards: `PaperCard.tsx` for list items, `QuickPeekSheet.tsx` for detail peek.
- Navigation: `Sidebar.tsx` (left nav), `CommandPalette.tsx` (Cmd+K), keyboard nav via `useKeyboardNav.ts`.
- Space background: togglable 3D (Three.js) vs CSS parallax in `components/parallax/`.

## UI/UX Patterns

- Command palette (Cmd+K) for global search and navigation.
- Keyboard navigation: `j/k` for items, `space` for quick-peek, `b` for bookmark, `g+letter` chords.
- Toast notifications via `sonner`.
- Loading skeletons via `SkeletonCard.tsx`.
- Error boundaries via `ErrorBoundary.tsx`.

## New Page Checklist

1. Create `frontend/app/<route>/page.tsx`.
2. Add navigation entry in `Sidebar.tsx`.
3. Add route to `CommandPalette.tsx` if searchable.
4. Add keyboard chord in `useKeyboardNav.ts` (e.g., `g+x`).
5. Wrap page content in `PageTransition` for enter/exit animations.
