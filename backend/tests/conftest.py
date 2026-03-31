import os
import sys
from unittest.mock import MagicMock

# Set SQLite DB URL before importing anything
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock pgvector.sqlalchemy.Vector to avoid SQLite errors
# We need to do this BEFORE importing models
import sqlalchemy.types as types
class MockVector(types.TypeDecorator):
    impl = types.JSON
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.JSON)

sys.modules["pgvector.sqlalchemy"] = MagicMock()
sys.modules["pgvector.sqlalchemy"].Vector = MockVector

# Mock scheduler to prevent it from starting during tests
sys.modules["scheduler"] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from models import Paper, UserConfig, Base

# Re-create engine for SQLite (since database.py might have created one already, but we want to be sure)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database session for a test.
    """
    # Create tables
    # We need to make sure models use the MockVector
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
