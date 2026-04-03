---
description: Run the test suite and lint checks for the arxiv_assistant backend.
---

# /test — Run Tests & Lint

1. Change to the backend directory:
   ```bash
   cd backend
   ```

2. Run the linter to catch syntax errors:
   ```bash
   make lint
   ```

3. Run import verification:
   ```bash
   make check
   ```

4. Run unit tests (excludes remote/live/mlx markers):
   ```bash
   make test-unit
   ```

5. Report results:
   - If all pass: summarize with "All tests passing" and the count.
   - If any fail: show the failing test names and error messages. Suggest fixes.
