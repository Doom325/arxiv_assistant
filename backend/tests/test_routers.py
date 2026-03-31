import pytest
from models import Paper, UserConfig
from datetime import date

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to arXiv AI Assistant API"}

def test_get_papers(client, db_session):
    # Create a dummy paper
    paper = Paper(
        arxiv_id="1234.5678",
        title="Test Paper",
        authors=["Author A"],
        summary="Summary",
        published_date=date(2023, 1, 1),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
        embedding=[0.1]*768 # Mock embedding
    )
    db_session.add(paper)
    db_session.commit()

    response = client.get("/papers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Paper"

def test_update_user_config(client):
    config_data = {
        "email": "test@example.com",
        "keywords": ["AI", "ML"],
        "categories": ["cs.AI"]
    }
    response = client.post("/users/config", json=config_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["keywords"] == ["AI", "ML"]

def test_get_user_config(client, db_session):
    # Create config
    config = UserConfig(email="existing@example.com", keywords=["Old"], categories=[])
    db_session.add(config)
    db_session.commit()

    response = client.get("/users/config/existing@example.com")
    assert response.status_code == 200
    assert response.json()["email"] == "existing@example.com"

    response = client.get("/users/config/nonexistent@example.com")
    assert response.status_code == 404
