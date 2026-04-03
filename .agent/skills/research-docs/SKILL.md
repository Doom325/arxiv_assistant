---
name: research-docs
description: Uses Context7 MCP to fetch up-to-date documentation for libraries and frameworks used in arxiv_assistant. Use when the user asks about API usage, library features, migration guides, or when you need current docs for FastAPI, Next.js, SQLAlchemy, pgvector, Tailwind, Framer Motion, or any other dependency.
---

# Research Documentation

Use the **context7** MCP tool to fetch current, version-specific documentation instead of relying on training data. This prevents hallucinated APIs and ensures correct usage patterns.

## When to Use

- Before using a library API you're not 100% certain about
- When the user asks "how do I do X with <library>?"
- When implementing a feature that depends on recent library changes
- When debugging an error that might be caused by API changes
- When upgrading a dependency to a new version

## arxiv_assistant Dependencies to Research

### Backend (Python)
| Library | What to Look Up |
|---------|----------------|
| **FastAPI** | Route decorators, dependency injection, lifespan events, WebSocket, BackgroundTasks |
| **SQLAlchemy** | ORM queries, relationship patterns, async sessions, column types |
| **pgvector** | Vector column types, distance operators (`<=>`, `<->`), index types (IVFFlat, HNSW) |
| **Pydantic** | Model validation, `model_validator`, `from_attributes`, Settings |
| **APScheduler** | Scheduler configuration, job stores, triggers, async jobs |
| **google-generativeai** | Gemini API: embeddings, generate_content, batch API, safety settings |
| **ollama** | Python client: chat, embeddings, model management |
| **GLiNER** | Entity extraction, model loading, token classification |
| **Resend** | Email API: send, templates, attachments |
| **PyMuPDF (fitz)** | PDF text extraction, page rendering, metadata |
| **pytest** | Fixtures, markers, parametrize, mock, conftest patterns |

### Frontend (TypeScript)
| Library | What to Look Up |
|---------|----------------|
| **Next.js 16** | App Router, Server Components, route handlers, middleware, caching |
| **React 19** | New hooks, React Compiler, Server Components, Suspense, transitions |
| **Tailwind CSS v4** | New config format, CSS-first config, `@theme`, custom properties |
| **Framer Motion** | AnimatePresence, layout animations, gestures, variants |
| **@react-three/fiber** | Canvas, useFrame, mesh, geometry, materials |
| **Recharts** | Chart types, responsive containers, custom tooltips, axes |
| **cmdk** | Command palette API, groups, items, keyboard handling |
| **react-markdown** | Plugins (remark-gfm, remark-math), custom renderers |
| **KaTeX** | Math rendering, supported functions, rehype-katex config |

## How to Query

When using Context7, be specific about the library and version:
- "FastAPI dependency injection with async generators"
- "pgvector HNSW index creation in SQLAlchemy"
- "Next.js 16 App Router dynamic routes with loading states"
- "Framer Motion AnimatePresence exit animations"

## Guidelines

- Always verify Context7 results against the library's actual API before implementing.
- If Context7 returns outdated info, fall back to the official docs URL.
- Cache frequently needed patterns mentally — don't re-query for basics.
- For arxiv_assistant-specific patterns, check the codebase first (existing implementations are the best reference).
