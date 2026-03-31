# SPEC: Deep Dive Chat Page
Date: 2026-03-28

## Design Summary

The Deep Dive page is a warm, scholarly conversational interface for AI-assisted research discussion. The layout is a single-column centered chat with a featured-surface hero welcome state, a scrollable message area, and a fixed bottom input bar. The design avoids the generic chatbot look by using the warm editorial design language: parchment surfaces, serif display headings, terracotta accents on interactive elements, and generous whitespace.

---

## Design Language Coherence

| Check | Status | Notes |
|-------|--------|-------|
| Warm cream/parchment surface | PASS | Page base uses `bg-background` (#F5F0E8); message area sits directly on page surface |
| One accent color on interactive elements only | PASS | Terracotta (#C4614A) used exclusively on send button, suggested prompt hover states, and source links |
| One featured/deep surface per page | PASS | Forest-green hero panel (#2A4A1A) used only for the welcome state header; disappears once conversation begins |
| Mixed-weight serif headline | PASS | Welcome headline uses Newsreader: "Deep" extralight + "Dive" bold italic |
| No structural borders on cards/panels | PASS | Message bubbles use tonal surface shifts (surface-card for AI, surface-inset for user); no borders |
| Generous whitespace | PASS | Message area uses `px-6 md:px-12`, bubbles have `p-5`, gap between messages is `gap-5` |
| Metadata labels uppercase with tracking | PASS | "Sources" label on citations, welcome label, all use uppercase + tracking-label |

---

## Coverage

| REQ | Capability | Status | Evidence |
|-----|-----------|--------|---------|
| REQ-053 | Conversational chat with paper library | Covered | Full message thread with user/AI bubbles; API call to POST /papers/chat |
| REQ-054 | Suggested example prompts | Covered | Welcome state shows 4 prompt cards in 2x2 grid on surface-card |
| REQ-055 | Source citation navigation | Covered | AI messages show "Sources" section with paper title, arxiv link to /paper/[id] |
| REQ-020 | Markdown + LaTeX rendering | Covered | AI messages render via ReactMarkdown + remarkGfm + remarkMath + rehypeKatex |
| REQ-056 | Persistent navigation | Covered | AppShell sidebar/rail always visible |
| REQ-057 | Command palette | Covered | Inherited from layout.tsx CommandPalette |
| REQ-060 | Keyboard shortcut overlay | Covered | Inherited from AppShell |

**Summary: 7 Covered, 0 Partial, 0 Missing**

---

## Component Inventory

1. **ChatHero** — Featured-surface welcome panel shown when no messages exist. Contains: uppercase tracked label "Deep Dive", mixed-weight serif headline, italic subtitle describing the feature, and a 2x2 grid of suggested prompt cards.

2. **ChatMessageBubble** — A single message bubble. User messages: right-aligned, surface-inset background, foreground text. AI messages: left-aligned, surface-card background, with a small Bot icon, full markdown rendering, and optional source citations block.

3. **ChatSourceCard** — Inline citation card within an AI message. Shows FileText icon, paper title/text, and a "View paper" link to /paper/[arxivId]. Uses surface-inset background.

4. **ChatTypingIndicator** — Animated three-dot indicator shown while awaiting AI response. Uses surface-card background with terracotta dots.

5. **ChatInputBar** — Fixed-bottom input area. Large text input on surface-card with warm shadow, terracotta send button with Send icon. Disabled state when loading or empty input.

6. **ChatPage (page shell)** — Orchestrates all components. Manages message state, scroll-to-bottom behavior, API calls. Full-height layout with flex column: hero/messages area (flex-1 overflow-y-auto) + input bar (sticky bottom).

---

## Tokens Used

| Token | CSS Variable | Hex | Usage |
|-------|-------------|-----|-------|
| Page background | --color-background | #F5F0E8 | Page base |
| Card surface | --color-surface-card | #EDE9E1 | AI message bubbles, input bar bg, prompt cards |
| Inset surface | --color-surface-inset | #E5E0D5 | User message bubbles, source cards |
| Featured surface | --color-surface-featured | #2A4A1A | Welcome hero panel |
| Accent | --color-accent | #C4614A | Send button, links, hover states |
| Accent hover | --color-accent-hover | #B05540 | Send button hover |
| On accent | --color-on-accent | #FFFFFF | Send button icon |
| On featured | --color-on-featured | #FFFFFF | Hero text |
| Foreground | --color-foreground | #1C1915 | Primary text |
| Foreground secondary | --color-foreground-secondary | #6B6258 | Subtitles, metadata |
| Foreground muted | --color-foreground-muted | #9B9086 | Placeholder text, timestamps |
| Display font | --font-display | Newsreader | Headlines, subtitles |
| Body font | --font-body | Inter | Message text, UI labels |
| Label tracking | --tracking-label | 0.08em | Uppercase metadata labels |

---

## Open Questions

None. All REQs are covered and the API surface (POST /papers/chat) is well-defined.
