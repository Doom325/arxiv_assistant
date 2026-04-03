---
name: add-frontend-page
description: Creates a new Next.js App Router page with navigation, keyboard shortcuts, API integration, and animations. Use when the user asks to add a new page, view, or frontend route.
---

# Add Frontend Page

When creating a new page in the frontend, follow this checklist:

## Step 1: Create the Page

Create `frontend/app/<route>/page.tsx`:

```tsx
import { PageTransition } from '@/components/PageTransition';

export default function FeaturePage() {
  return (
    <PageTransition>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Feature Name</h1>
        {/* Page content */}
      </div>
    </PageTransition>
  );
}
```

- Server Component by default. Add `"use client"` only if needed.
- Wrap in `PageTransition` for enter/exit animations.
- Follow the dark theme: white text, semi-transparent backgrounds, glassmorphism.

## Step 2: Add API Functions

Add data fetching functions to `frontend/lib/api.ts`:

```typescript
export async function fetchFeatureData(): Promise<FeatureData[]> {
  const response = await fetch('/api/feature');
  if (!response.ok) throw new Error('Failed to fetch feature data');
  return response.json();
}
```

## Step 3: Add Navigation

Update `frontend/components/Sidebar.tsx` — add a nav entry with a lucide-react icon:

```tsx
{ href: '/feature', icon: FeatureIcon, label: 'Feature Name' }
```

## Step 4: Add to Command Palette

Update `frontend/components/CommandPalette.tsx` to include the new route in search results.

## Step 5: Add Keyboard Shortcut

Update `frontend/lib/useKeyboardNav.ts` — add a `g+<letter>` chord:

```typescript
// g+f → navigate to /feature
```

## Step 6: Loading & Error States

- Use `SkeletonCard` or a custom skeleton for loading states.
- Use the `ErrorBoundary` component for error handling.
- Use `sonner` toast for transient notifications.

## Design Patterns

- Dashboard-style: use bento grid layout (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`).
- List views: use `StaggerList` for animated item entry.
- Charts: use Recharts components (see `components/dashboard/` for examples).
- Paper cards: reuse `PaperCard.tsx` for paper listings.
