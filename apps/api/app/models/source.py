from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    website_url = Column(String, nullable=False)
    rss_url = Column(String, nullable=True)
    trust_tier = Column(Integer, default=2, nullable=False)
    allowed_domains = Column(JSON, nullable=False, default=list)
    ingestion_method = Column(String(30), nullable=False, default="rss")
    refresh_minutes = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, nullable=False, default=True)
    last_ingested_at = Column(DateTime(timezone=True), nullable=True)
    last_ingestion_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
