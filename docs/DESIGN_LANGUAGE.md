# Design Language
Last updated: 2026-03-25

This document is the visual and typographic baseline for the UI overhaul.
Every Stitch prompt, every agent, and every implementation decision references this file.

It defines **principles**, not exact specs. Stitch interprets within these principles.
The goal is coherence across pages — not uniformity.

---

## Spirit

This is a research tool for people who read seriously. The design should feel like
the best version of a physical research environment: considered, warm, uncluttered.
Not a productivity app. Not a SaaS dashboard. A place where thinking happens.

**The emotional target:** calm confidence. The interface recedes so the content leads.

---

## 1. Color

### Base palette — warm, never cold
The page surface lives in the warm cream-to-parchment range. Never pure white (`#FFFFFF`).
Never cool grey. The warmth communicates quality and reduces eye fatigue across long sessions.

- **Page surface:** warm cream — somewhere in `#F0EAE0` to `#FAF6EF`
- **Card surface:** a step warmer/darker than the page — tonal shift creates depth without borders
- **Nested / inset elements:** one further step in the same warm direction

Stitch picks the exact values. The constraint is: warm, light, no cool tones.

### Accent — one color, used with discipline
One accent color for all interactive elements: links, CTAs, active states, focus rings.
It should be warm and saturated — terracotta, amber, warm red, or similar.
It never appears decoratively. Only on things the user can interact with or that demand attention.

### Featured surface — one per page, used sparingly
Each page may have one surface that breaks from the neutral palette — a deep, rich color
(forest green, deep navy, warm charcoal, deep plum) used for a single featured or
hero-level element. This creates one strong focal point. Never more than one per page.

### What this is not
- No dark backgrounds as the primary surface
- No blue-greys or cool neutrals
- No multiple competing accent colors
- No gradient fills on backgrounds or cards

---

## 2. Typography

Typography is the primary design tool. Hierarchy comes from type, not from boxes or color.

### Display / headlines — variable-weight serif
Use a variable-weight serif (Fraunces, Playfair Display, Cormorant, or similar) for
page-level headlines and hero text. The defining technique: **mix weights within a single
headline** — light or thin weight for context words, bold/heavy for the key phrase.

Example spirit:
> "Search for a topic to explore its" [light]
> **"research timeline"** [heavy]

This creates visual drama from type alone.

### Body and UI — humanist sans
Inter, DM Sans, or a similar humanist sans-serif for all body text, metadata, navigation,
and UI labels. Clean, readable, unpretentious.

### Descriptions and annotations — italic
Supporting text, card descriptions, and helper copy use italic — either italic serif or
italic sans. This creates a clear register distinction between "label" and "explanation."

### Metadata labels — small caps with tracking
Section headers, category tags, timestamps, and count labels use uppercase with generous
letter-spacing (+0.06em to +0.10em). Small but authoritative.

### Type scale — generous
Go larger than feels necessary at first. Headlines should command the page.
Whitespace between type blocks should feel almost excessive.

---

## 3. Space

Whitespace is a feature, not waste. The design should breathe.

- Between major sections: 48px minimum
- Card internal padding: 24px minimum
- Between cards in a grid: 16–20px
- Line height for body text: 1.65–1.75

When in doubt, add more space. Dense, cramped layouts conflict with the editorial spirit.

---

## 4. Surfaces and Depth

### Tonal hierarchy — no structural borders
Cards and panels sit on the page because their background is different — never because
they have a border drawn around them. The depth system:

```
Page surface (warmest, lightest)
  └─ Card surface (slightly warmer/darker)
       └─ Inset / nested element (one step further)
            └─ Featured surface (one rich deep color per page)
```

### Shadows — warm and soft
When shadows appear (floating panels, modals, hover states), they should be warm-tinted
and very diffuse. No hard, cool, or dark shadows.

Example spirit: `box-shadow: 0 4px 24px rgba(60, 40, 20, 0.08)`

### Corners — generous
Cards: `border-radius: 16px` minimum. Floating panels: `20px+`.
Chips and badges: pill (`border-radius: 999px`).
No sharp corners on any interactive surface.

---

## 5. Interaction and States

### Active / selected state
The accent color marks the active item. Bold weight shifts can reinforce selection.
No heavy background fills on selected list items — a left border accent or color change
on the text is usually sufficient.

### Hover
Subtle — a slight background shift (one tonal step) or a shadow appearance.
Never jarring. The interface is calm.

### Empty states
Should feel intentional and inviting, not like an error. Use the display serif,
generous space, and a simple visual motif. The user should feel "this is ready for me"
not "something is missing."

---

## 6. What Stitch Should Feel Free to Invent

- The layout structure (grid, split-panel, single column, canvas)
- The navigation model (sidebar, top nav, bottom bar, hybrid)
- The information hierarchy within a page
- Specific interaction patterns (how a filter opens, how a preview appears)
- The exact color values within the principles above
- Which typeface within the role (display serif, humanist sans)

## 7. What Stitch Should Not Change

- The warmth of the base palette (always cream/parchment range)
- The principle of one accent color used only for interaction
- The principle of one featured surface per page (rich, deep, used once)
- The mixed-weight serif headline technique
- The generous spacing
- The tonal-shift-over-borders approach

---

## Coherence Check (for reviewing Stitch outputs)

Before accepting any Stitch output, verify:
- [ ] Background is warm cream/parchment, not white or cool grey
- [ ] Only one accent color appears, only on interactive elements
- [ ] Only one featured/deep surface element per page
- [ ] Headlines use the mixed-weight serif technique
- [ ] No structural borders on cards or panels
- [ ] Spacing feels generous — sections breathe
- [ ] Metadata labels use uppercase with tracking
