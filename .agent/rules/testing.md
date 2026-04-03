# Testing Standards

## Framework

- **pytest** with markers: `remote` (needs network), `live` (needs real DB), `mlx` (Apple Silicon only).
- Test files: `backend/tests/test_*.py` (34 existing test files).
- Fixtures: `conftest.py` provides SQLite in-memory DB, mocked pgvector (`Vector` → JSON type), mocked scheduler.

## Running Tests

```bash
cd backend
make test          # All tests
make test-unit     # Unit tests only (excludes remote/live/mlx) — USE THIS FOR LOCAL DEV
make test-fast     # Stop on first failure (-x)
make lint          # Syntax check critical files
make check         # Import verification
```

## Writing Tests

- Every new API endpoint must have at least one test.
- Every new service method that contains business logic must have a test.
- Test files live next to nothing — they all go in `backend/tests/`.
- Name test files `test_<module>.py` and test functions `test_<behavior>`.
- Use `describe`-style grouping with classes: `class TestSearchRouter:`.
- Write tests that describe behavior, not implementation details.

## Mocking

- Mock external APIs (arXiv, Gemini, Ollama, Resend) in unit tests.
- The conftest provides a mocked pgvector — tests use SQLite in-memory, not PostgreSQL.
- The scheduler is mocked to prevent background jobs during tests.
- Use `unittest.mock.patch` or `pytest-mock` for service mocking.

## Test Coverage

- Prioritize testing routers (API contracts) and services (business logic).
- Worker pipeline tests should mock PDF downloads and LLM calls.
- Do not test SQLAlchemy model definitions — they are declarative.

## Before Committing

- Run `make test-unit` — all tests must pass.
- Run `make lint` — no syntax errors in critical files.
- If you added a new dependency, verify `make check` passes (import verification).
