---
description: Run quality gates — lint, type check, unit tests, and import verification for the project.
---

# /verify — Quality Gates

Run all quality checks before committing or deploying.

## Backend Checks

1. Syntax check critical files:
   ```bash
   cd backend && make lint
   ```

2. Verify all imports resolve:
   ```bash
   cd backend && make check
   ```

3. Run unit tests:
   ```bash
   cd backend && make test-unit
   ```

## Frontend Checks

4. TypeScript type checking:
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. Build verification:
   ```bash
   cd frontend && npm run build
   ```

## Report

6. Summarize results:
   - List any failing checks with details
   - If all pass: confirm "All quality gates passed"
   - If any fail: prioritize fixes by severity (type errors > test failures > lint warnings)
