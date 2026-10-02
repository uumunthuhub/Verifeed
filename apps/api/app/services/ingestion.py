import datetime
import hashlib
import logging
from urllib.parse import urlparse

import feedparser
import trafilatura

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


def _host_is_allowed(url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not hostname:
        return False
    return any(hostname == domain.lower().rstrip(".") or hostname.endswith(f".{domain.lower().rstrip('.')}") for domain in allowed_domains)


def _extract_source_content(url: str, source: Source) -> str | None:
    allowed_domains = source.allowed_domains or []
    if not _host_is_allowed(url, allowed_domains):
        logger.warning("Skipped article outside approved source domains: %s", url)
        return None
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    return trafilatura.extract(downloaded, include_comments=False, include_tables=False)


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
        if not source or not source.rss_url or not source.is_active or source.ingestion_method != "rss":
            return f"Source {source_id} not found or has no RSS URL."

        feed = feedparser.parse(source.rss_url)
        new_articles = 0

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not url or not title:
                continue

            content = _extract_source_content(url, source)
            if not content:
                continue
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            existing = db.query(Article).filter(Article.url == url).first()
            if existing and existing.content_hash == content_hash:
                existing.retrieved_at = datetime.datetime.now(datetime.UTC)
                db.commit()
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                p: tuple[int, ...] = tuple(entry.published_parsed)  # type: ignore
                try:
                    published = datetime.datetime(p[0], p[1], p[2], p[3], p[4], p[5])
                except (TypeError, IndexError, ValueError):
                    published = None

            if existing:
                article = existing
                article.headline = title
                article.published_at = published
                article.content = content
                article.content_hash = content_hash
                article.retrieved_at = datetime.datetime.now(datetime.UTC)
                article.content_type = "text/html"
            else:
                article = Article(
                    source_id=source.id,
                    headline=title,
                    url=url,
                    published_at=published,
                    content=content,
                    content_hash=content_hash,
                    retrieved_at=datetime.datetime.now(datetime.UTC),
                    content_type="text/html",
                )
                db.add(article)
            db.commit()
            db.refresh(article)
            new_articles += 1

            # Enqueue background embedding + categorization
            categorize_and_embed_article.delay(article.id)

        source.last_ingested_at = datetime.datetime.now(datetime.UTC)
        source.last_ingestion_error = None
        db.commit()
        return f"Ingested {new_articles} new articles from {source.name}."
    except Exception as exc:
        db.rollback()
        if "source" in locals() and source:
            source.last_ingestion_error = str(exc)[:1000]
            db.commit()
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
        now = datetime.datetime.now(datetime.UTC)
        sources = db.query(Source).filter(
            Source.rss_url.isnot(None),
            Source.is_active.is_(True),
            Source.ingestion_method == "rss",
        ).all()
        due_sources = []
        for source in sources:
            last_ingested_at = source.last_ingested_at
            if last_ingested_at and last_ingested_at.tzinfo is None:
                last_ingested_at = last_ingested_at.replace(tzinfo=datetime.UTC)
            if not last_ingested_at or now - last_ingested_at >= datetime.timedelta(minutes=source.refresh_minutes):
                due_sources.append(source)
        for source in due_sources:
            ingest_rss_feed.delay(source.id)
        return f"Queued ingestion for {len(due_sources)} due sources."
    finally:
        db.close()


@celery_app.task(name="ingest_web_page", bind=True, max_retries=3)
def ingest_web_page(self, url: str, source_id: int):
    """Scrape a single web page, extract content, and index into Pgvector."""
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id, Source.is_active.is_(True)).first()
        if not source:
            return f"Active source {source_id} not found."
        if not _host_is_allowed(url, source.allowed_domains or []):
            return f"URL is not approved for source {source_id}."

        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return f"Failed to download {url}"

        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        metadata = trafilatura.extract_metadata(downloaded)
        if not text:
            return f"Could not extract content from {url}"

        title = metadata.title if metadata and metadata.title else url

        published_date = None
        if metadata and metadata.date:
            try:
                published_date = datetime.datetime.fromisoformat(metadata.date)
            except ValueError:
                pass

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        article = db.query(Article).filter(Article.url == url).first()
        if article and article.content_hash == content_hash:
            article.retrieved_at = datetime.datetime.now(datetime.UTC)
            db.commit()
            return f"Article {url} is already current."
        if article:
            article.headline = title
            article.published_at = published_date
            article.content = text
            article.content_hash = content_hash
            article.retrieved_at = datetime.datetime.now(datetime.UTC)
            article.content_type = "text/html"
        else:
            article = Article(
                source_id=source_id,
                headline=title,
                url=url,
                published_at=published_date,
                content=text,
                content_hash=content_hash,
                retrieved_at=datetime.datetime.now(datetime.UTC),
                content_type="text/html",
            )
            db.add(article)
        db.commit()
        db.refresh(article)

        # Enqueue embedding
        categorize_and_embed_article.delay(article.id)

        return f"Ingested and queued embedding for web page: {url}"
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
