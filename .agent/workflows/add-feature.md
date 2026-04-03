---
description: End-to-end workflow for adding a new feature spanning backend API, frontend UI, and tests.
---

# /add-feature — Full-Stack Feature Development

## Step 1: Plan

1. Ask the user to describe the feature in one sentence.
2. Generate an implementation plan covering:
   - Database model changes (if any)
   - Backend API endpoints needed
   - Frontend pages/components needed
   - Test coverage plan
3. Present the plan as a checklist and get user approval before proceeding.

## Step 2: Backend — Data Layer

4. If new database models are needed, create them following the `add-model` skill.
5. Write a migration script (`migrate_<feature>.py`).
6. Export models from `models/__init__.py`.

## Step 3: Backend — API Layer

7. Create or extend a router in `backend/routers/`.
8. Add service logic in `backend/services/`.
9. Add Pydantic schemas in `backend/schemas.py`.
10. Register the router in `main.py` (if new).
11. Write tests in `backend/tests/test_<feature>.py`.

## Step 4: Frontend — UI Layer

12. Add API functions to `frontend/lib/api.ts`.
13. Create the page at `frontend/app/<route>/page.tsx`.
14. Add navigation entry in `Sidebar.tsx`.
15. Add to `CommandPalette.tsx` search results.
16. Add keyboard shortcut in `useKeyboardNav.ts`.
17. Use proper loading skeletons and error handling.

## Step 5: Verify

18. Run backend tests:
    ```bash
    cd backend && make test-unit
    ```

19. Run lint checks:
    ```bash
    cd backend && make lint
    ```

20. Start the dev environment and manually verify the feature works:
    ```bash
    cd backend && uvicorn main:app --reload &
    cd frontend && npm run dev &
    ```

## Step 6: Commit

21. Stage the changes and create a conventional commit:
    ```bash
    git add -A
    git commit -m "feat: <short description of the feature>"
    ```
