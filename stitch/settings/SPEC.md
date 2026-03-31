# Settings Page -- Design Spec

Page: `/settings`
Last updated: 2026-03-28

---

## Design Direction

Settings is a **utility page** -- clean, organized, no hero, no featured surface.
Simple serif headline at top, section cards for each settings group.

---

## Token Map

| Element | Token / Class |
|---------|--------------|
| Page background | `bg-background` (#F5F0E8) |
| Page headline | `font-display text-3xl font-light text-foreground` (Newsreader) |
| Page subtitle | `text-foreground-secondary` |
| Section card | `bg-surface-card rounded-xl border border-[#D5CFC4] shadow-warm-sm` |
| Section heading | `font-display text-xl text-foreground` |
| Label text | `text-sm font-medium text-foreground-secondary` |
| Help text | `text-xs text-foreground-muted` |
| Text input | `bg-surface-inset border border-[#D5CFC4] rounded-lg text-foreground placeholder:text-foreground-muted focus:ring-2 focus:ring-accent` |
| Select dropdown | Same as text input |
| Load button (secondary) | `bg-surface-inset border border-[#D5CFC4] text-foreground hover:bg-[#DDD8CD] rounded-lg` |
| Save button (primary) | `bg-accent text-on-accent hover:bg-accent-hover rounded-lg font-display shadow-warm-sm` |
| Divider | `border-t border-[#D5CFC4]` |

---

## Layout

```
+--------------------------------------------------+
|  Settings                          (serif, light) |
|  Manage your preferences and notifications.       |
|                                                    |
|  +----------------------------------------------+ |
|  | Research Interests          (section heading) | |
|  |                                              | |
|  | Keywords (comma separated)                   | |
|  | [____________________________________]       | |
|  | We will prioritize papers matching these...  | |
|  +----------------------------------------------+ |
|                                                    |
|  +----------------------------------------------+ |
|  | Notifications               (section heading) | |
|  |                                              | |
|  | Email Address                                | |
|  | [____________________________________] [Load]| |
|  |                                              | |
|  | Frequency                                    | |
|  | [Daily Digest________________v]              | |
|  +----------------------------------------------+ |
|                                                    |
|  [ Save Changes ]  (full-width accent button)      |
+--------------------------------------------------+
```

Max width: `max-w-2xl`. Vertical spacing: `space-y-6` between sections.

---

## Component Inventory

This page is small enough to remain a single file (`app/settings/page.tsx`).
No component extraction needed -- all elements are standard form controls.

### Existing component reuse:
- **RippleButton** -- used for Save Changes (accent primary)
- **toast (sonner)** -- success/error feedback

### No new components required.

---

## Interaction Patterns

1. **Load**: User types email, clicks Load. If config found, keywords populate. If 404, silent fail.
2. **Save**: User edits fields, clicks Save Changes. Button shows "Saving..." + disabled state. Toast on success/error.
3. **Focus ring**: All inputs use `focus:ring-2 focus:ring-accent` (terracotta ring).

---

## Dark Token Removal Checklist

Current dark tokens to replace:

| Old Token | New Token |
|-----------|-----------|
| `text-white` (headings) | `text-foreground` |
| `text-zinc-400` (labels, subtitle) | `text-foreground-secondary` |
| `text-zinc-500` (help text) | `text-foreground-muted` |
| `bg-zinc-900` (card) | `bg-surface-card` |
| `bg-zinc-800` (inputs, load btn) | `bg-surface-inset` |
| `border-zinc-800` (card border, divider) | `border-[#D5CFC4]` |
| `border-zinc-700` (input border) | `border-[#D5CFC4]` |
| `bg-indigo-600 hover:bg-indigo-700` (save btn) | `bg-accent hover:bg-accent-hover` |
| `focus:ring-indigo-500` (inputs) | `focus:ring-accent` |
| `hover:bg-zinc-700` (load btn hover) | `hover:bg-[#DDD8CD]` |
