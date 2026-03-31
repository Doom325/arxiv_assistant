# Functional Requirements — Deep Dive Chat (/chat)

Coverage checklist for post-stitch review.
Source: docs/FUNCTIONAL_REQUIREMENTS.md — filtered to REQs served by this page.

---

## Chat Core

REQ-053 | CHAT
The user can hold a conversational chat session with an AI assistant that has access to their indexed paper library. The assistant answers questions grounded in the user's papers.
Backend: POST /papers/chat?query=<text>

REQ-054 | CHAT
The user is presented with suggested example prompts on the empty/welcome state to help bootstrap a conversation.
Backend: none (client-side)

REQ-055 | CHAT
When the AI response includes source citations, the user can see which papers were referenced and navigate to those papers' detail pages.
Backend: response.sources[] from POST /papers/chat

---

## Navigation (active on this page)

REQ-056 | NAV
Persistent navigation between all major sections is available.

REQ-057 | NAV
Global command palette via Cmd/Ctrl+K.

REQ-060 | NAV
View keyboard shortcut reference overlay.

---

## Cross-cutting

REQ-020 | GENERAL
The system renders Markdown content (including LaTeX via KaTeX) in AI responses.
