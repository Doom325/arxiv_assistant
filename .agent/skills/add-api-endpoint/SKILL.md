---
name: add-api-endpoint
description: Creates a new FastAPI API endpoint with router, service logic, Pydantic schemas, and tests. Use when the user asks to add a new API route, endpoint, or backend feature.
---

# Add API Endpoint

When creating a new API endpoint, follow this checklist:

## Step 1: Define the Schema

Add Pydantic request/response models in `backend/schemas.py` or co-located with the router if complex.

```python
class MyFeatureResponse(BaseModel):
    id: int
    data: str
    created_at: datetime
```

## Step 2: Create or Extend a Router

- If it's a new domain, create `backend/routers/<feature>.py`.
- If it extends an existing domain, add to the relevant router.
- All handlers must be `async def`.
- Use `Depends(get_db)` for database sessions.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/feature", response_model=list[MyFeatureResponse])
async def list_features(db: Session = Depends(get_db)):
    # Delegate to service layer
    return feature_service.list_all(db)
```

## Step 3: Add Service Logic

Business logic goes in `backend/services/<feature>_service.py`. Follow the singleton pattern:

```python
class FeatureService:
    def list_all(self, db: Session) -> list:
        return db.query(Feature).all()

feature_service = FeatureService()
```

## Step 4: Register the Router

Add to `backend/main.py`:

```python
from routers.feature import router as feature_router
app.include_router(feature_router, tags=["feature"])
```

## Step 5: Write Tests

Create `backend/tests/test_feature.py`:
- Test happy path for each endpoint.
- Test error cases (404, validation errors).
- Mock external services.

## Step 6: Verify

```bash
cd backend
make test-unit
make lint
```
