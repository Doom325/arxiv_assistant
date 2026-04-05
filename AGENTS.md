# arxiv_assistant — Cross-Tool Agent Rules

This file provides shared rules for AI coding agents across tools (Antigravity, Cursor, Claude Code).
For Antigravity-specific overrides, see `GEMINI.md`. For Claude Code context, see `CLAUDE.md`.

## Tech Stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy ORM, PostgreSQL 16 + pgvector
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4
- **LLM Providers:** Google Gemini API, Ollama (Gemma 3), GLiNER
- **Infrastructure:** Docker Compose (4 containers), APScheduler, Resend email

## Code Quality

- Keep functions under 40 lines; extract helpers if longer.
- Use meaningful, intention-revealing names. Avoid abbreviations except well-known ones (`db`, `api`, `url`, `id`).
- Use early returns to reduce nesting. Maximum two levels of indentation in logic.
- Do not duplicate logic — if the same code appears twice, extract it into a shared utility.
- Remove all debug statements (`print()`, `console.log`) before completing a task.

## Python (Backend)

- Full PEP 484 type annotations on all function signatures.
- Use `async def` for all FastAPI route handlers and service methods that do I/O.
- Use `ruff` for linting and formatting.
- Use `pathlib.Path` over `os.path` for file operations.
- Never use mutable default arguments (`def foo(items=[])`).
- All new services follow the existing singleton pattern (lazy-loaded global instances).
- All database queries go through SQLAlchemy ORM — no raw SQL strings unless for pgvector-specific operations.
- Wrap external API calls (arXiv, Gemini, Ollama, Resend) in try/except with structured logging.

## TypeScript (Frontend)

- TypeScript strict mode. Never use `any` — use `unknown` and narrow.
- Prefer named exports over default exports.
- React Server Components by default. Add `"use client"` only when using hooks or browser APIs.
- Use `cn()` from `@/lib/utils` for conditional classNames if available.
- Colocate component-specific types in the same file.
- Use Framer Motion for animations — no raw CSS transitions on interactive elements.
- All API calls go through `lib/api.ts` — never call `fetch()` directly in components.

## Database

- PostgreSQL 16 + pgvector. Port 5434 (not default 5432).
- Embeddings are 3072-dimensional stored in pgvector columns.
- All schema changes must be backward-compatible or handled via migration scripts (`migrate_*.py`).
- Use SQLAlchemy ORM models. New models go in `backend/models/` and must be exported from `models/__init__.py`.
- Use FastAPI dependency injection (`Depends(get_db)`) for sessions — never create sessions manually in routers.

## Testing

- pytest with markers: `remote` (needs network), `live` (needs real DB), `mlx` (Apple Silicon).
- `make test-unit` for local development (excludes remote/live/mlx).
- Every new router endpoint must have at least one test in `backend/tests/`.
- Tests use SQLite in-memory with mocked pgvector (see `conftest.py`).
- Test files live in `backend/tests/` and follow the naming pattern `test_*.py`.

## Security

- Never hardcode API keys, tokens, or secrets. All credentials come from environment variables via `config.py`.
- Never commit `.env` files. Use `.env.example` as the template.
- Always use parameterized queries — no string interpolation in SQL.
- Validate all user input at API boundaries using Pydantic schemas.
- CORS is currently allow-all for development; flag any changes to CORS config.

## Git Workflow

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `chore:`, `test:`, `config:`, `security:`, `docs:`
- Subject line under 72 characters. One logical change per commit.
- **NEVER commit directly to `main`.** Always use feature branches + pull requests.
- Run `make test-unit` and `make lint` before committing.

## Architecture Rules

- New API endpoints: create router in `backend/routers/`, register in `main.py`.
- New background tasks: add to `production_worker.py` pipeline or `scheduler.py`.
- New frontend pages: create in `frontend/app/<route>/page.tsx`, add to Sidebar navigation.
- Provider changes: extend `LLMProvider` base class in `llm_service.py`. Never hard-code provider-specific logic in routers.
- All paper processing goes through the worker pipeline — never process PDFs synchronously in API handlers.

---

## Reviewer Agent Integration (MANDATORY)

This repo is tracked by the [Reviewer Agent](https://github.com/Doom325/reviewer-agent), an autonomous AI code review system. **Every code change must go through a PR and be reviewed by the Reviewer Agent before merging.**

### Identity: CoderAgent GitHub App

All agents (Claude Code, Antigravity) act as `coder-agent[bot]` when creating PRs. Before performing git/GitHub operations, generate a token:

```bash
export GITHUB_TOKEN=$(python ~/git/reviewer_agent/scripts/generate_app_token.py \
  --app-id 3275701 \
  --private-key ~/.config/reviewer-agent/keys/coder-agent.pem \
  --installation-id 121415198)
```

Configure git identity for commits:

```bash
git config user.name "coder-agent[bot]"
git config user.email "3275701+Doom325-CoderAgent[bot]@users.noreply.github.com"
```

### PR Submission Workflow (follow this for EVERY task)

After completing implementation:

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/short-description
   ```

2. **Commit changes** with conventional commit messages:
   ```bash
   git add <specific files>
   git commit -m "feat: short description of change"
   ```

3. **Push and create a PR:**
   ```bash
   git push -u origin feat/short-description
   gh pr create --title "feat: short description" --body "## Summary\n- ...\n\n## Test plan\n- [ ] ..."
   ```

4. **Apply the `reviewer:pending` label** to trigger AI review:
   ```bash
   gh pr edit --add-label "reviewer:pending"
   ```

5. **Do NOT merge.** Wait for the Reviewer Agent to post its review.

### After Reviewer Agent Posts Its Review

| Verdict | What to do |
|---|---|
| **APPROVED** | Merge the PR |
| **CONDITIONAL** | Address minor items, then merge |
| **REJECTED** | Fix each finding in new commits, push, re-apply `reviewer:pending` |
| **HARD_REJECTED** | Redesign the approach before resubmitting |
| **ESCALATED** | Cycle limit reached — notify the human for manual review |

### Rules

- **NEVER** push directly to `main` — always use feature branches + PRs
- **NEVER** merge a PR without a Reviewer Agent verdict
- **NEVER** remove `reviewer:in-progress` manually — the agent manages labels
- **ALWAYS** apply `reviewer:pending` after creating a PR or pushing fixes
- Maximum review cycles before escalation: 3 (CRITICAL), 4 (MAJOR), 5 (MINOR)
