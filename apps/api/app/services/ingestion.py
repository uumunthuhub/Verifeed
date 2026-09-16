import datetime
import logging

import feedparser

from app.db.session import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.story import Story
from app.services.ai import get_ai_service
from app.worker import celery_app

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Politics", "Health", "Business", "Sports",
    "Regional", "Technology", "World", "Entertainment", "Other"
]

import re

KEYWORD_RULES: dict[str, list[str]] = {
    "Regional": ["africa", "malawi", "south africa", "nigeria", "kenya", "zambia", "sadc", "lilongwe", "blantyre", "pretoria", "johannesburg", "lagos"],
    "World": ["global", "un", "treaty", "nato", "ukraine", "russia", "china", "eu", "summit", "conflict", "diplomat", "foreign", "sanction"],
    "Politics": ["election", "president", "minister", "parliament", "vote", "senate", "congress", "policy", "government", "politician", "cabinet", "court", "lawmaker"],
    "Health": ["covid", "virus", "health", "hospital", "doctor", "disease", "vaccine", "cancer", "medical", "outbreak", "fda", "who", "medicine", "patient"],
    "Business": ["market", "stock", "economy", "inflation", "bank", "trade", "revenue", "profit", "ceo", "financial", "shares", "dollar", "crypto", "company", "investor"],
    "Sports": ["football", "soccer", "league", "match", "cup", "champion", "nba", "nfl", "olympic", "tournament", "goal", "trophy", "athlete", "coach", "tennis", "cricket"],
    "Technology": ["ai", "apple", "google", "microsoft", "tech", "software", "app", "cyber", "chip", "data", "startup", "smartphone", "robot", "cloud", "iphone", "nvidia"],
    "Entertainment": ["movie", "film", "hollywood", "music", "album", "actor", "actress", "celebrity", "cinema", "grammy", "oscar", "tv", "series", "concert"],
}


def get_embedding(text: str) -> list[float] | None:
    """Generate a vector embedding via the AI service boundary."""
    return get_ai_service().embed(text)


def categorize_headline(headline: str) -> str:
    """Categorize a headline using fast word-boundary rules, falling back to the AI service."""
    text_lower = headline.lower()
    for cat, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return cat

    prompt = (
        f"Categorize the following news headline into exactly one of these categories: "
        f"{', '.join(CATEGORIES)}. Reply with ONLY the category name, nothing else.\n"
        f"Headline: {headline}"
    )
    result = get_ai_service().generate(prompt)
    text = (result or "").strip()
    return text if text in CATEGORIES else "Other"


@celery_app.task(name="ingest_rss_feed", bind=True, max_retries=3)
def ingest_rss_feed(self, source_id: int):
    """Parse an RSS feed and queue embedding tasks for new articles."""
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source or not source.rss_url:
            return f"Source {source_id} not found or has no RSS URL."

        feed = feedparser.parse(source.rss_url)
        new_articles = 0

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not url or not title:
                continue

            existing = db.query(Article).filter(Article.url == url).first()
            if existing:
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                p: tuple[int, ...] = tuple(entry.published_parsed)  # type: ignore
                try:
                    published = datetime.datetime(p[0], p[1], p[2], p[3], p[4], p[5])
                except (TypeError, IndexError, ValueError):
                    published = None

            article = Article(
                source_id=source.id,
                headline=title,
                url=url,
                published_at=published,
                content=getattr(entry, "summary", ""),
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            new_articles += 1

            # Enqueue background embedding + categorization
            categorize_and_embed_article.delay(article.id)

        return f"Ingested {new_articles} new articles from {source.name}."
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="categorize_and_embed_article", bind=True, max_retries=3)
def categorize_and_embed_article(self, article_id: int):
    """Generate embeddings, categorize the article, and cluster it into a story."""
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return f"Article {article_id} not found."

        # 1. Categorize
        category = categorize_headline(str(article.headline))

        # 2. Generate embedding
        text = f"{article.headline}. {article.content or ''}"
        embedding = get_embedding(text)
        if embedding:
            article.embedding = embedding  # type: ignore

        # 3. Cluster into a story via cosine distance
        if embedding:
            similar = (
                db.query(Article)
                .filter(
                    Article.id != article.id,
                    Article.story_id.isnot(None),
                    Article.embedding.isnot(None),
                )
                .order_by(Article.embedding.cosine_distance(embedding))
                .first()
            )
            if similar and similar.story_id:
                article.story_id = similar.story_id
                story = db.query(Story).filter(Story.id == similar.story_id).first()
                if story and not story.category:
                    story.category = category  # type: ignore
            else:
                story = Story(title=article.headline, category=category)
                db.add(story)
                db.commit()
                db.refresh(story)
                article.story_id = story.id
        else:
            story = Story(title=article.headline, category=category)
            db.add(story)
            db.commit()
            db.refresh(story)
            article.story_id = story.id

        db.commit()
        return f"Processed article {article_id} → story {article.story_id} [{category}]."

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="ingest_all_sources")
def ingest_all_sources():
    """Trigger RSS ingestion for every known source. Schedule via Celery Beat."""
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.rss_url.isnot(None)).all()
        for source in sources:
            ingest_rss_feed.delay(source.id)
        return f"Queued ingestion for {len(sources)} sources."
    finally:
        db.close()
