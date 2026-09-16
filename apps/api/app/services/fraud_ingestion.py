import datetime
import logging
import os

import feedparser
import google.generativeai as genai

from app.db.session import SessionLocal
from app.models.institution import Institution, InstitutionalAlert
from app.services.ingestion import get_embedding
from app.worker import celery_app

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-1.5-flash"

def classify_fraud_alert(title: str, content: str) -> bool:
    """Use Gemini to determine if a press release/article is a fraud disclaimer."""
    if not GEMINI_API_KEY:
        return False
        
    try:
        model = genai.GenerativeModel(GENERATION_MODEL)
        prompt = (
            "Analyze the following institutional announcement. Does this announcement "
            "warn the public about a scam, fraud, fake offer, or impersonation attempt? "
            "Reply with exactly 'YES' or 'NO'.\n\n"
            f"Title: {title}\n"
            f"Content: {content}"
        )
        response = model.generate_content(prompt)
        text = response.text.strip().upper()
        return "YES" in text
    except Exception as e:
        logger.error(f"Error classifying fraud alert: {e}")
        return False

@celery_app.task(name="ingest_institutional_alerts", bind=True, max_retries=3)
def ingest_institutional_alerts(self, institution_id: int, feed_url: str):
    """
    Fetch an institution's news/alert feed and identify scam disclaimers.
    In a real implementation, this would scrape their press page or consume an RSS feed.
    """
    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            return f"Institution {institution_id} not found."

        # Parse the RSS/Mock Feed
        feed = feedparser.parse(feed_url)
        new_alerts = 0

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            content = getattr(entry, "summary", getattr(entry, "description", ""))

            if not url or not title:
                continue

            # Skip if we already indexed this
            existing = db.query(InstitutionalAlert).filter(InstitutionalAlert.source_url == url).first()
            if existing:
                continue

            # Classify if this is a scam alert
            is_alert = classify_fraud_alert(title, content)
            if not is_alert:
                continue

            # It's an alert! Embed and save.
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                p: tuple[int, ...] = tuple(entry.published_parsed) # type: ignore
                try:
                    published = datetime.datetime(
                        p[0], p[1], p[2], p[3], p[4], p[5]
                    )
                except (TypeError, IndexError, ValueError):
                    published = None

            embedding = get_embedding(f"{title}. {content}")

            alert = InstitutionalAlert(
                institution_id=inst.id,
                title=title,
                alert_text=content[:2000], # Keep it sane
                source_url=url,
                published_date=published,
                embedding=embedding
            )
            db.add(alert)
            db.commit()
            new_alerts += 1

        return f"Ingested {new_alerts} new fraud alerts for {inst.name}."
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()

@celery_app.task(name="poll_all_institutions")
def poll_all_institutions():
    """Trigger ingestion for all known institutions."""
    db = SessionLocal()
    try:
        institutions = db.query(Institution).all()
        queued = 0
        for inst in institutions:
            # We assume the website URL has an RSS feed or we use a fallback mock URL.
            # In a real system, Institution would have a specific `rss_url` column.
            feed_url = f"{inst.website_url}/rss" 
            ingest_institutional_alerts.delay(inst.id, feed_url)
            queued += 1
        return f"Queued fraud ingestion for {queued} institutions."
    finally:
        db.close()
