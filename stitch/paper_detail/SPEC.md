# SPEC: Paper Detail Page
Date: 2026-03-28
Stitch output: stitch/paper_detail/paper_detail/code.html

## Design Summary

Stitch produced a single-column reading layout (max-w-4xl, centered) with a deep forest-green hero panel for the paper title, followed by clearly delineated content sections: abstract with drop cap, AI synthesis card, references list, detected patterns, action footer, and recommended research grid. A sticky right-side table of contents appears on xl+ screens. The design prioritizes readability — generous whitespace, warm parchment surfaces, and typographic hierarchy via mixed-weight Newsreader headlines.

---

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | ✅ | Page background uses `#F5F0E8`. All cards use `#EDE9E1`. Inset elements use `#E5E0D5`. No pure white or cool grey. |
| One accent color on interactive elements only | ✅ | Terracotta `#C4614A` used exclusively on CTAs, links, active TOC, drop cap accent. No decorative accent use. |
| One featured/deep surface per page | ✅ | Deep forest green `#2A4A1A` hero panel is the single featured surface. No other dark surfaces. |
| Mixed-weight serif headline | ✅ | Paper title in hero: first two words italic `font-extralight`, remainder `font-bold`. Newsreader throughout. |
| No structural borders on cards/panels | ✅ | All cards use tonal shift + `shadow-warm-sm` for depth. No `border-*` on content cards. |
| Generous whitespace | ✅ | Main content uses `px-12`, `py-8`, sections spaced with `space-y-16`. Card padding `p-6` to `p-10`. |
| Metadata labels uppercase with tracking | ✅ | "RESEARCH PAPER", "ABSTRACT", "AI SYNTHESIS", "REFERENCES", "DETECTED PATTERNS", "RECOMMENDED RESEARCH" all uppercase with tracking-widest or tracking-[0.2em]. |

---

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|---------|
| REQ-P01 | Display paper metadata | Covered | Title in hero, date/arxiv_id/categories as metadata chips, reading time |
| REQ-P02 | Markdown + LaTeX abstract | Design only | Abstract section present — actual rendering requires react-markdown at build time |
| REQ-P03 | Reading time estimate | Covered | "12 MIN READ" shown in hero metadata row |
| REQ-P04 | Trigger AI summary | Covered | "Regenerate Analysis" button in AI Synthesis section header |
| REQ-P05 | Generation progress | Partial | Status line shows "Analysis completed March 16, 2026" — pulsing indicator not visible in static mock but described in spec |
| REQ-P06 | Render AI summary | Covered | Full markdown-rendered summary with Key Contributions, Limitations, Relevance sections |
| REQ-P07 | Regenerate analysis | Covered | "Regenerate Analysis" button present |
| REQ-P08 | Browser notification | N/A | Runtime feature — not designable in static mock |
| REQ-P09 | Toggle bookmark | Covered | Bookmark icon button in hero action row |
| REQ-P10 | Email summary | Covered | Mail icon button in hero + "Email Summary" button in action footer |
| REQ-P11 | Email status feedback | Partial | Button present — animation states require runtime |
| REQ-P12 | Link to PDF | Covered | "Open PDF" terracotta CTA in hero + "Read Full PDF" button in footer |
| REQ-P13 | Link to timeline | Covered | "Show Timeline" button in action footer |
| REQ-P14 | Display citations | Covered | 5 citation cards with title, authors, raw text |
| REQ-P15 | Link resolved citations | Covered | Resolved citations show title as accent-colored link |
| REQ-P16 | "Available locally" indicator | Covered | Green chip on resolved citations |
| REQ-P17 | External link for citations | Covered | External link icon button on cards with URLs |
| REQ-P18 | Pattern confidence scores | Covered | 3 patterns with percentage badges |
| REQ-P19 | Confidence bar visualization | Covered | Horizontal bars with accent fill proportional to confidence |
| REQ-P20 | Agentic badge | Covered | "Agentic System" badge with sparkle icon |
| REQ-P21 | Collapsible CoT reasoning | Covered | Native `<details>` toggle for "Classification Reasoning" |
| REQ-P22 | Pattern Library link | Covered | "View Pattern Library" link present |
| REQ-P23 | Similar papers grid | Covered | 2-column grid with 3 recommendation cards |
| REQ-P24 | Recommendation card content | Covered | Category chip, title, date, reading time on each card |
| REQ-P25 | Back link | Covered | "← Back to Reading Queue" link at top |
| REQ-P26 | Sticky TOC sidebar | Covered | Right sidebar with section links, active state highlighting |
| REQ-P27 | Loading state | Missing | Not shown in static mock — will implement at build time |
| REQ-P28 | Paper not found state | Missing | Not shown — will implement with editorial serif pattern |
| REQ-P29 | Empty analysis state | Partial | Button text changes but empty state not explicitly shown |

**Summary: 21 Covered, 4 Partial, 2 Missing, 2 N/A**

---

## Component Inventory

1. **Back Navigation** — Accent-colored "← Back to Reading Queue" link with hover translate-x animation.

2. **Paper Title Hero** (featured surface) — Deep forest green `#2A4A1A` panel, `rounded-2xl`, generous padding. "RESEARCH PAPER" label uppercase tracking. Mixed-weight Newsreader title. Metadata row: Calendar icon + date, FileText icon + arxiv_id, category chips (bg-white/10 rounded-full). Action buttons: Mail, Bookmark (icons), Open PDF (terracotta CTA). Reading time badge.

3. **Abstract Section** — "ABSTRACT" label with thin warm rule. Drop cap first letter (text-5xl, accent color, float-left). Prose body text in Inter, leading-relaxed. Full markdown rendering.

4. **AI Synthesis Section** — Card surface panel (bg-surface-card rounded-2xl shadow-warm-sm). Header: Sparkles icon in accent + "AI SYNTHESIS" label + "Regenerate Analysis" button (accent rounded-full). Content: bulleted key contributions, limitations, relevance assessment. Status line with timestamp.

5. **References Section** — "REFERENCES" label with count badge (bg-surface-inset). Citation cards: bg-surface-card rounded-xl p-4. Each: title (accent link if resolved), authors (italic muted), "Available locally" chip (accent/15), raw citation (smaller muted italic). External link icon button.

6. **Detected Patterns Section** — "DETECTED PATTERNS" label with count badge. Pattern badges: "Agentic System" (accent/15). Pattern cards: monospace category/name in accent, confidence percentage badge, confidence bar (surface-inset track + accent fill), evidence quote italic. Collapsible CoT reasoning via `<details>`.

7. **Action Footer** — Three centered buttons: Email Summary (surface-card secondary), Show Timeline (surface-card secondary), Read Full PDF (accent primary rounded-full).

8. **Recommended Research Section** — "RECOMMENDED RESEARCH" label with Lightbulb icon. 2-column grid. Cards: surface-card, category chip, title with hover:accent, date, reading time.

9. **Sticky TOC Sidebar** — Fixed right column on xl+ screens. Section links: Abstract, AI Analysis, References, Patterns, Recommendations. Active: accent color + left border. Muted for inactive.

---

## Escalations

### E-001 — Drop Cap Styling
**Issue:** The drop cap uses CSS `::first-letter` pseudo-element with float. This can conflict with React's hydration and markdown rendering (ReactMarkdown wraps text in `<p>` tags).
**Options:**
- A) Implement drop cap as a separate styled `<span>` wrapping the first character programmatically
- B) Use CSS `::first-letter` on a wrapper div (simpler but less control)
**Recommendation:** A — more reliable with React rendering

### E-002 — Sticky TOC Scroll Spy
**Issue:** The sticky TOC highlights the active section based on scroll position. This requires an IntersectionObserver or scroll event listener.
**Options:**
- A) Implement with IntersectionObserver watching section headings
- B) Skip scroll spy — just show the TOC links without active highlighting
- C) Use a lightweight library
**Recommendation:** A — IntersectionObserver is clean and performant

### E-003 — Prose Styling for Markdown
**Issue:** The AI summary and abstract render markdown via ReactMarkdown. Current page uses `prose prose-invert` (dark mode). Need to switch to warm prose styling.
**Options:**
- A) Use Tailwind `prose` class with custom warm overrides (`prose-headings:text-foreground prose-p:text-foreground-secondary`)
- B) Style markdown output with custom CSS classes on the wrapper
**Recommendation:** A — Tailwind prose with overrides is cleanest

### E-004 — Back Navigation Target
**Issue:** The back link currently hardcodes "Back to Dashboard" but users arrive from both queue and dashboard.
**Options:**
- A) Use router.back() for true browser back navigation
- B) Keep hardcoded link but make it configurable via URL param
- C) Use a "Back to Queue" / "Back to Dashboard" based on referrer
**Recommendation:** A — router.back() is simplest and always correct
