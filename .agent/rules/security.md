# Security Rules

## Secrets Management

- All credentials loaded via environment variables through `backend/config.py` (Pydantic BaseSettings).
- Never hardcode API keys, tokens, or passwords in source code.
- Never commit `.env` files. Only `.env.example` (with placeholder values) goes in version control.
- Never log, print, or expose secret values in API responses or error messages.

## Input Validation

- All API request bodies validated via Pydantic schemas.
- Metadata search filters (`category:`, `after:`, `before:`, `author:`, `entity:`) are parsed and parameterized — never injected raw into queries.
- PDF file paths are constructed via `pdf_utils.py` — never accept raw file paths from user input.
- arXiv IDs are validated against the expected format before use.

## Database Security

- Always use parameterized queries or SQLAlchemy ORM — no string interpolation in SQL.
- Database credentials come from `DATABASE_URL` env var only.
- Connection pooling prevents connection exhaustion (pool size 20, overflow 30).

## API Security

- CORS is currently allow-all (for development/mobile testing). Flag any proposed changes.
- No authentication on API endpoints currently — this is a single-user application.
- Rate limiting on arXiv API calls (3s delay) is enforced in `arxiv_service.py`.
- Google Drive OAuth2 tokens stored server-side, refreshed automatically.

## External Communications

- Email sent only via Resend API with configured sender address.
- Google Drive operations require explicit OAuth2 consent flow.
- Never send file contents to external URLs without explicit user instruction.

## Destructive Operations

- Ask for confirmation before: deleting papers, dropping database tables, modifying production data.
- Ask for confirmation before: `git push`, `git reset --hard`, `./deploy.sh`.
- The deploy scripts (`deploy.sh`, `deploy-staging.sh`) rsync to remote servers — always verify the target.
