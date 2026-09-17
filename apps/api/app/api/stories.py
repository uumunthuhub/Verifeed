from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article
from app.models.story import Story

router = APIRouter()

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website_url: str

class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    headline: str
    url: str
    published_at: datetime | None
    source: SourceResponse

class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str | None
    summary: str | None
    created_at: datetime
    article_count: int
    sources: list[str] = []
    primary_source: str | None = None

class StoryDetailResponse(StoryResponse):
    articles: list[ArticleResponse]

@router.get("/", response_model=list[StoryResponse])
def get_stories(
    category: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(
        Story,
        func.count(Article.id).label('article_count')
    ).outerjoin(Article).group_by(Story.id).order_by(Story.created_at.desc())

    if category:
        query = query.filter(Story.category == category)

    stories = query.offset(skip).limit(limit).all()

    result = []
    for story, article_count in stories:
        story_dict = {c.name: getattr(story, c.name) for c in story.__table__.columns}
        story_dict['article_count'] = article_count
        source_names = [a.source.name for a in story.articles if a.source]
        story_dict['sources'] = source_names
        story_dict['primary_source'] = source_names[0] if source_names else None
        result.append(story_dict)

    return result

@router.get("/search", response_model=list[StoryResponse])
def search_stories(
    q: str = Query(..., min_length=2, description="Keyword search across story titles and article headlines"),
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    """
    Full-text keyword search across story titles and article headlines.
    Uses PostgreSQL ILIKE for MVP; can be upgraded to plainto_tsquery for scale.
    """
    term = f"%{q}%"

    # Subquery: story IDs matched via article headlines
    matching_story_ids = (
        db.query(Article.story_id)
        .filter(Article.story_id.isnot(None), Article.headline.ilike(term))
        .distinct()
        .scalar_subquery()
    )

    stories_with_counts = (
        db.query(Story, func.count(Article.id).label("article_count"))
        .outerjoin(Article)
        .filter(
            or_(
                Story.title.ilike(term),
                Story.id.in_(matching_story_ids),
            )
        )
        .group_by(Story.id)
        .order_by(Story.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for story, article_count in stories_with_counts:
        story_dict = {c.name: getattr(story, c.name) for c in story.__table__.columns}
        story_dict["article_count"] = article_count
        source_names = [a.source.name for a in story.articles if a.source]
        story_dict["sources"] = source_names
        story_dict["primary_source"] = source_names[0] if source_names else None
        result.append(story_dict)

    return result

@router.get("/{story_id}", response_model=StoryDetailResponse)
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    articles = db.query(Article).filter(Article.story_id == story_id).all()

    story_dict = {c.name: getattr(story, c.name) for c in story.__table__.columns}
    story_dict['article_count'] = len(articles)
    story_dict['articles'] = articles
    source_names = [a.source.name for a in articles if a.source]
    story_dict['sources'] = source_names
    story_dict['primary_source'] = source_names[0] if source_names else None

    return story_dict
