from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Index
from datetime import datetime
from .base import Base


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
    list_name = Column(String, default="Bookmarks", index=True)

    __table_args__ = (
        Index("idx_user_list", "user_id", "list_name"),
    )
