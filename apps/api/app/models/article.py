from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    headline = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    content = Column(Text, nullable=True)
    embedding = Column(Vector(768))  # 768 dims for Gemini text-embedding-004
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", backref="articles")
    story = relationship("Story", backref="articles")
