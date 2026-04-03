---
description: Structured debugging workflow for diagnosing and fixing issues in arxiv_assistant.
---

# /debug — Structured Debugging

Follow this systematic approach when diagnosing bugs.

## Step 0: Check Existing Context

1. Read `ISSUES_LOG.md` (if it exists) for previously diagnosed issues:
   ```bash
   cat ISSUES_LOG.md 2>/dev/null || echo "No issues log found"
   ```

2. Check recent git history for related changes:
   ```bash
   git log --oneline -20
   ```

## Step 1: Reproduce

3. Ask the user for exact reproduction steps.
4. Reproduce the issue and capture:
   - Error message (full traceback)
   - Which service is affected (backend, worker, frontend, db)
   - When it started (after a recent change? always?)

## Step 2: Isolate

5. Narrow down the component:
   - **Backend API error:** Check `backend/routers/` → trace to `services/` → check `models/`
   - **Worker failure:** Check `JobLog` table for failed jobs, identify the pipeline stage
   - **Frontend error:** Check browser console, trace API call in `lib/api.ts`
   - **Database issue:** Check connection pool, query plans, missing indexes

6. Read the relevant source files. Do not guess — read the code.

## Step 3: Hypothesize

7. Form an evidence-based hypothesis. State it clearly before making changes.
8. Check if the hypothesis explains ALL symptoms, not just some.

## Step 4: Fix

9. Make the minimal change that fixes the root cause.
10. Do not refactor surrounding code while fixing a bug.
11. Add a test that would have caught this bug.

## Step 5: Verify

12. Run the reproduction steps — confirm the bug is fixed.
13. Run the test suite:
    ```bash
    cd backend && make test-unit
    ```

14. If the fix is in the worker pipeline, verify by checking the worker processes a paper successfully.

## Step 6: Document

15. If the bug was non-obvious, add it to `ISSUES_LOG.md` with:
    - Symptoms
    - Root cause
    - Fix applied
    - Date
