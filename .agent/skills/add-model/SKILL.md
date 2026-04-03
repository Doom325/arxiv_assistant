---
name: add-model
description: Creates a new SQLAlchemy ORM model with migration script and test. Use when the user asks to add a new database table, model, or schema.
---

# Add Database Model

When adding a new SQLAlchemy ORM model, follow this checklist:

## Step 1: Create the Model

Add to an existing domain file in `backend/models/` or create a new one:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from models.base import Base

class NewEntity(Base):
    __tablename__ = "new_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### For pgvector columns:
```python
from pgvector.sqlalchemy import Vector

embedding = Column(Vector(3072))  # Always 3072 dimensions
```

### For full-text search:
```python
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import TSVECTOR

search_vector = Column(TSVECTOR)
__table_args__ = (
    Index('ix_new_entities_search', 'search_vector', postgresql_using='gin'),
)
```

## Step 2: Export from __init__.py

Add to `backend/models/__init__.py`:

```python
from models.new_entity import NewEntity
```

This ensures the model is discovered by SQLAlchemy's `Base.metadata.create_all()`.

## Step 3: Write Migration Script

Create `backend/migrate_add_new_entities.py`:

```python
"""Migration: Add new_entities table.

Run: python migrate_add_new_entities.py
"""
from database import engine
from models.new_entity import NewEntity
from models.base import Base

def migrate():
    Base.metadata.create_all(bind=engine, tables=[NewEntity.__table__])
    print("Created new_entities table")

if __name__ == "__main__":
    migrate()
```

## Step 4: Add Pydantic Schemas

Add response/request models in `backend/schemas.py`:

```python
class NewEntityResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True
```

## Step 5: Verify

```bash
cd backend
make check    # Verify imports work
make test-unit  # Run tests
```

## Conventions

- Table names: lowercase, plural, snake_case (`new_entities`, not `NewEntity`).
- Always include `id` (Integer, primary key), `created_at`, `updated_at`.
- Foreign keys reference the table name (`ForeignKey("papers.id")`).
- Nullable by default for new columns (backward compatibility).
- Add indexes on columns used in WHERE clauses or JOINs.
