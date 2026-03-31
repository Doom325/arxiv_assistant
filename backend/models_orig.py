from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for SQLite which doesn't support pgvector natively
    # In a real app, you might use a generic JSON type or a proper SQLite extension
    from sqlalchemy import JSON
    def Vector(dim):
        return JSON

from datetime import datetime
from config import settings

Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String, unique=True, index=True)
    title = Column(String)
    authors = Column(JSON)  # List of strings
    summary = Column(Text)
    generated_summary = Column(Text, nullable=True)
    published_date = Column(Date)
    updated_date = Column(Date)
    category = Column(String)
    pdf_url = Column(String)
    
    # Embedding for the summary/content (assuming 768 dim for Gemini)
    if "sqlite" in settings.DATABASE_URL:
         embedding = Column(JSON)
    else:
         embedding = Column(Vector(768))

class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    keywords = Column(JSON)  # List of keywords to track
    categories = Column(JSON) # List of categories to track (e.g., ["cs.AI", "cs.LG"])
    schedule_time = Column(String, default="06:00") # 24h format

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class UserLibrary(Base):
    __tablename__ = "user_library"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    paper_id = Column(Integer, ForeignKey("papers.id"))
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
