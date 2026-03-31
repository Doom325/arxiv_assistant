from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UserConfig
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

class UserConfigCreate(BaseModel):
    email: str
    keywords: list[str]
    categories: list[str]

@router.post("/config")
def update_config(config: UserConfigCreate, db: Session = Depends(get_db)):
    db_config = db.query(UserConfig).filter(UserConfig.email == config.email).first()
    if not db_config:
        db_config = UserConfig(email=config.email)
        db.add(db_config)
    
    db_config.keywords = config.keywords
    db_config.categories = config.categories
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/config/{email}")
def get_config(email: str, db: Session = Depends(get_db)):
    db_config = db.query(UserConfig).filter(UserConfig.email == email).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="User config not found")
    return db_config
