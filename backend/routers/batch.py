
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.batch_service import batch_service
from models import BatchQueue, Paper
from datetime import datetime

router = APIRouter(prefix="/batch", tags=["batch"])

@router.post("/trigger")
def trigger_batch(db: Session = Depends(get_db)):
    batch_id = batch_service.create_daily_batch_job(db)
    if batch_id:
        return {"message": "Batch job submitted", "batch_id": batch_id}
    else:
        return {"message": "No papers to process or job failed"}

# --- Queue Management ---

@router.post("/queue/{paper_id}")
def add_to_queue(paper_id: int, db: Session = Depends(get_db)):
    # 1. Check paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        pass # Try searching by arxiv_id? For now ID.
        # Actually API might use integer ID
        # If not, assume paper_id is integer.
    
    if not paper: 
        raise HTTPException(status_code=404, detail="Paper not found")
        
    # 2. Check if already in queue
    exists = db.query(BatchQueue).filter(BatchQueue.paper_id == paper_id, BatchQueue.status == "PENDING").first()
    if exists:
        return {"message": "Already in queue"}
        
    # 3. Add
    item = BatchQueue(paper_id=paper_id, status="PENDING")
    db.add(item)
    db.commit()
    return {"message": "Added to batch queue"}

@router.delete("/queue/{paper_id}")
def remove_from_queue(paper_id: int, db: Session = Depends(get_db)):
    item = db.query(BatchQueue).filter(BatchQueue.paper_id == paper_id, BatchQueue.status == "PENDING").first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in pending queue")
        
    db.delete(item)
    db.commit()
    return {"message": "Removed from queue"}

@router.get("/queue")
def get_queue(db: Session = Depends(get_db)):
    # Join with Paper to get titles
    queue = db.query(BatchQueue, Paper.title, Paper.arxiv_id).join(Paper, BatchQueue.paper_id == Paper.id).filter(BatchQueue.status == "PENDING").all()
    
    return [
        {
            "id": item.BatchQueue.id,
            "paper_id": item.BatchQueue.paper_id,
            "arxiv_id": item.arxiv_id,
            "title": item.title,
            "added_at": item.BatchQueue.created_at
        }
        for item in queue
    ]
