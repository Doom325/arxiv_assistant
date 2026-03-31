import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from models import UserLibrary, Paper
from schemas import LibraryPaperResponse
from services import reading_queue_service as rqs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/library", tags=["library"])

# Hardcoded user ID for now
USER_ID = 1

@router.post("/lists/{list_name}")
def create_list(list_name: str, db: Session = Depends(get_db)):
    # Check if list already exists for user
    exists = db.query(UserLibrary).filter(
        UserLibrary.user_id == USER_ID,
        UserLibrary.list_name == list_name
    ).first()
    
    if exists:
        return {"message": f"List {list_name} already exists"}
    
    # Create a bookmark entry with NO paper_id to represent the list
    new_list = UserLibrary(user_id=USER_ID, list_name=list_name, paper_id=None)
    db.add(new_list)
    db.commit()
    return {"message": f"List {list_name} created"}

@router.post("/{paper_id}")
def add_bookmark(paper_id: int, list_name: str = "Bookmarks", db: Session = Depends(get_db)):
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if already bookmarked in THIS list
    exists = db.query(UserLibrary).filter(
        UserLibrary.user_id == USER_ID,
        UserLibrary.paper_id == paper_id,
        UserLibrary.list_name == list_name
    ).first()
    
    if exists:
        return {"message": f"Already bookmarked in {list_name}"}
    
    # Mark as not in drive for this list
    details = paper.in_drive_details or {}
    details[list_name] = False
    paper.in_drive_details = details
    flag_modified(paper, "in_drive_details")

    new_bookmark = UserLibrary(user_id=USER_ID, paper_id=paper_id, list_name=list_name)
    db.add(new_bookmark)
    db.commit()

    # Auto-add to reading queue
    try:
        rqs.add_paper_to_queue(db, paper_id, user_id=USER_ID)
    except Exception as e:
        logger.warning("Failed to add paper %d to queue: %s", paper_id, e)

    return {"message": f"Bookmark added to {list_name}"}

@router.delete("/{paper_id}")
def remove_bookmark(paper_id: int, list_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserLibrary).filter(
        UserLibrary.user_id == USER_ID,
        UserLibrary.paper_id == paper_id
    )
    if list_name:
        query = query.filter(UserLibrary.list_name == list_name)
    
    bookmark = query.first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()

    # Remove from reading queue if no bookmarks remain
    remaining = (
        db.query(UserLibrary)
        .filter(
            UserLibrary.user_id == USER_ID,
            UserLibrary.paper_id == paper_id,
        )
        .first()
    )
    if not remaining:
        try:
            rqs.remove_from_queue(db, paper_id, user_id=USER_ID)
        except Exception as e:
            logger.warning(
                "Failed to remove paper %d from queue: %s",
                paper_id,
                e,
            )

    return {"message": "Bookmark removed"}

@router.get("/ids", response_model=List[int])
def get_bookmarked_ids(list_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserLibrary.paper_id).filter(UserLibrary.user_id == USER_ID)
    if list_name:
        query = query.filter(UserLibrary.list_name == list_name)
    bookmarks = query.all()
    return [b[0] for b in bookmarks]

@router.get("/lists", response_model=List[str])
def get_library_lists(db: Session = Depends(get_db)):
    lists = db.query(UserLibrary.list_name).filter(UserLibrary.user_id == USER_ID).distinct().all()
    return [l[0] for l in lists]

@router.get("", response_model=List[LibraryPaperResponse])
def get_library(list_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserLibrary).filter(UserLibrary.user_id == USER_ID)
    if list_name and list_name != "All":
        query = query.filter(UserLibrary.list_name == list_name)
    
    bookmarks = query.all()
    results = []
    for b in bookmarks:
        paper = db.query(Paper).filter(Paper.id == b.paper_id).first()
        if paper:
            results.append({
                "id": paper.id,
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "summary": paper.summary,
                "published_date": paper.published_date,
                "category": paper.category,
                "pdf_url": paper.pdf_url,
                "added_at": b.added_at,
                "list_name": b.list_name
            })
    return results

