from models import Paper
from datetime import date

def test_get_papers_null_authors(client, db_session):
    # Create a paper with null authors
    paper = Paper(
        arxiv_id="9999.8888",
        title="Null Authors Paper",
        authors=None, # This used to cause 500
        summary="Summary",
        published_date=date(2023, 1, 1),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
        embedding=[0.1]*768
    )
    db_session.add(paper)
    db_session.commit()

    response = client.get("/papers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["authors"] is None

def test_get_library_null_authors(client, db_session):
    # Create a paper with null authors
    paper = Paper(
        id=10,
        arxiv_id="1111.2222",
        title="Lib Null Authors Paper",
        authors=None,
        summary="Summary",
        published_date=date(2023, 1, 1),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
        embedding=[0.1]*768
    )
    db_session.add(paper)
    db_session.commit()
    
    # Add to library
    from models import UserLibrary, User
    # Ensure user 1 exists
    if not db_session.query(User).filter(User.id == 1).first():
        db_session.add(User(id=1, email="test@ex.com", hashed_password="pw"))
        db_session.commit()
        
    lib = UserLibrary(user_id=1, paper_id=10, list_name="Bookmarks")
    db_session.add(lib)
    db_session.commit()
    
    response = client.get("/library/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["authors"] is None
