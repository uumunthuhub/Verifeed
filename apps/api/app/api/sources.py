
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source import Source

router = APIRouter()

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website_url: str
    rss_url: str

@router.get("/", response_model=list[SourceResponse])
def get_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sources = db.query(Source).offset(skip).limit(limit).all()
    return sources


@router.post("/ingest")
def trigger_ingestion(db: Session = Depends(get_db)):
    """Trigger RSS ingestion across all sources."""
    from database.seeds.seed_stories import seed_news_data
    seed_news_data()
    return {"message": "Ingestion and seeding completed successfully."}

