
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy.orm import Session

from app.api.admin import require_ingestion_admin
from app.db.session import get_db
from app.models.source import Source

router = APIRouter()

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website_url: str
    rss_url: str | None = None
    trust_tier: int
    allowed_domains: list[str]
    ingestion_method: str
    refresh_minutes: int
    is_active: bool

@router.get("/", response_model=list[SourceResponse])
def get_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sources = db.query(Source).offset(skip).limit(limit).all()
    return sources


@router.post("/ingest", dependencies=[Depends(require_ingestion_admin)])
def trigger_ingestion(db: Session = Depends(get_db)):
    """Trigger RSS ingestion across all sources via Celery."""
    from app.services.ingestion import ingest_all_sources
    ingest_all_sources.delay()
    return {"message": "RSS ingestion tasks queued in Celery successfully."}


class ScrapeRequest(BaseModel):
    url: str
    source_id: int


class SourceRegistryUpdate(BaseModel):
    rss_url: HttpUrl | None = None
    allowed_domains: list[str] = Field(min_length=1)
    trust_tier: int = Field(ge=1, le=4)
    refresh_minutes: int = Field(ge=5, le=1440)
    is_active: bool


@router.put("/{source_id}/registry", dependencies=[Depends(require_ingestion_admin)])
def update_source_registry(source_id: int, payload: SourceRegistryUpdate, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if payload.rss_url and payload.rss_url.scheme != "https":
        raise HTTPException(status_code=422, detail="The feed URL must use HTTPS")

    source.rss_url = str(payload.rss_url) if payload.rss_url else None  # type: ignore
    source.allowed_domains = [domain.lower().strip() for domain in payload.allowed_domains]  # type: ignore
    source.trust_tier = payload.trust_tier  # type: ignore
    source.refresh_minutes = payload.refresh_minutes  # type: ignore
    source.is_active = payload.is_active  # type: ignore
    source.last_ingestion_error = None  # type: ignore
    db.commit()
    db.refresh(source)
    return source

@router.post("/scrape", dependencies=[Depends(require_ingestion_admin)])
def trigger_scrape(req: ScrapeRequest, db: Session = Depends(get_db)):
    """Trigger direct URL scraping and indexing."""
    from app.services.ingestion import ingest_web_page
    ingest_web_page.delay(req.url, req.source_id)
    return {"message": f"Web scraping task queued for {req.url}"}
