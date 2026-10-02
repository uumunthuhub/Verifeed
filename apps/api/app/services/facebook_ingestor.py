"""
Facebook RSS Bridge Ingestor — Phase 1 Live Data Pipeline.

Polls public Facebook pages of Malawian institutions via RSS Bridge feeds
every 5 minutes and ingests new posts as InstitutionalAlerts with embeddings
into the Pgvector ground-truth store.

This feeds the VeriFeed evidence pipeline with real-time official statements,
fraud warnings, and press releases — without requiring Meta API approval.

Architecture:
    RSS Bridge (Docker) → feedparser → classify_fraud_alert() → InstitutionalAlert + embedding
    Triggered by: Celery beat schedule (every 5 minutes)

Usage:
    # Start the RSS Bridge container first (see docker-compose.yml)
    # Then run workers:
    celery -A app.worker worker --loglevel=info
    celery -A app.worker beat --loglevel=info
"""

import datetime
import logging
import os
import calendar
from dataclasses import dataclass

import feedparser

from app.db.session import SessionLocal
from app.models.institution import Institution, InstitutionalAlert
from app.services.ingestion import get_embedding
from app.services.fraud_ingestion import classify_fraud_alert
from app.worker import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RSS Bridge base URL (set in .env, defaults to local Docker service)
# ---------------------------------------------------------------------------
RSS_BRIDGE_URL = os.getenv("RSS_BRIDGE_URL", "http://localhost:3000")


@dataclass
class RssFeedConfig:
    """Maps a Facebook page to its RSS Bridge feed URL and institution metadata."""
    page_slug: str        # Facebook page name (used in RSS Bridge URL)
    institution_name: str # Friendly name for logging and DB lookup
    trust_tier: float     # 1.0 = Government/Regulatory, 0.9 = Telecom, 0.85 = Media
    always_ingest: bool = False  # If True, skip fraud classification and ingest all posts


# ---------------------------------------------------------------------------
# Target Facebook pages — Malawi-first, ordered by priority
# ---------------------------------------------------------------------------
FACEBOOK_RSS_FEEDS: list[RssFeedConfig] = [
    # Critical — Regulatory / Government (always ingest all posts)
    RssFeedConfig("ReserveBankMalawi",       "Reserve Bank of Malawi",           trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MalawiRevenueAuthority",  "Malawi Revenue Authority (MRA)",   trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MalawiCommunicationsRegulatoryAuthorityMACRA", "Malawi Communications Regulatory Authority - MACRA", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MalawiPoliceService",     "Malawi Police Service",            trust_tier=0.95, always_ingest=True),
    RssFeedConfig("MalawiMinistryOfFinance", "Ministry of Finance Malawi",       trust_tier=1.0, always_ingest=True),
    RssFeedConfig("TheMalawiNationalExaminationsBoardMANEB", "The Malawi National Examinations Board (MANEB)", trust_tier=0.90, always_ingest=True),
    RssFeedConfig("MalawiStockExchangeMSE",     "Malawi Stock Exchange MSE",             trust_tier=0.85, always_ingest=True),
    RssFeedConfig("TheMalawiDefenceForce", "The Malawi Defence Force", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("AntiCorruptionBureauMalawi", "Anti Corruption Bureau Malawi", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("SouthernRegionWaterBoard", "Southern Region Water Board", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("CentralRegionWaterBoard", "Central Region Water Board", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("NorthernRegionWaterBoard", "Northern Region Water Board", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("BlantyreWaterBoard", "Blantyre Water Board", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("LilongweWaterBoard", "Lilongwe Water Board", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MajeteWildlifeReserve", "Majete Wildlife Reserve", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("NkhotakotaWildlifeReserve", "Nkhotakota Wildlife Reserve", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MalawiTourism", "Malawi Tourism", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("DepartmentofClimateChangeandMeteorologicalServices", "Department of Climate Change and Meteorological Services", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("MinistryOfHealthMalawi", "Ministry of Health Malawi", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("NationalAssemblyofMalawi", "National Assembly of Malawi", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("OfficeOfthePresidentandCabinetMalawi", "Office of the President and Cabinet Malawi", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("VicePresidentDrSaulosKlausChilima", "Vice President Dr. Saulos Klaus Chilima", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("RtHonDrLazarusChakwera", "Rt Hon Dr Lazarus Chakwera", trust_tier=1.0, always_ingest=True),
    RssFeedConfig("DrJoyceBanda", "Dr. Joyce Banda", trust_tier=1.0, always_ingest=True),

    # High — Telecoms (only ingest fraud/scam posts)    
    RssFeedConfig("TNMMalawi",               "TNM Malawi",                       trust_tier=0.90, always_ingest=False),
    RssFeedConfig("AirtelMalawi",            "Airtel Malawi",                    trust_tier=0.90, always_ingest=False),
    
    # Medium — Media (only ingest fraud-related articles)
    RssFeedConfig("Times360Malawi",          "Times 360 Malawi",                 trust_tier=0.85, always_ingest=False),
    RssFeedConfig("ZodiakOnline",            "Zodiak Broadcasting Station",      trust_tier=0.85, always_ingest=False),
    RssFeedConfig("Malawi24",               "Malawi 24",                         trust_tier=0.85, always_ingest=False),
]


def _build_rss_url(page_slug: str) -> str:
    """Constructs the RSS Bridge Atom feed URL for a given Facebook page slug."""
    return (
        f"{RSS_BRIDGE_URL}/?action=display"
        f"&bridge=Facebook"
        f"&context=User"
        f"&u={page_slug}"
        f"&format=Atom"
    )


def _get_or_create_institution(db, name: str) -> Institution | None:
    """
    Looks up an Institution by name. Creates a placeholder record if none exists
    so RSS posts can be stored without blocking on manual DB setup.
    """
    inst = db.query(Institution).filter(Institution.name == name).first()
    if inst:
        return inst

    logger.info("Creating placeholder institution for RSS ingestor: %s", name)
    inst = Institution(
        name=name,
        sector="Regulatory" if any(k in name for k in ["Bank", "Revenue", "Bureau", "MACRA", "Finance", "Police"]) else "Media",
        website_url=f"https://www.facebook.com/{name.replace(' ', '')}",
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


# ---------------------------------------------------------------------------
# Core per-feed ingestion task
# ---------------------------------------------------------------------------

@celery_app.task(name="ingest_facebook_rss_feed", bind=True, max_retries=3)
def ingest_facebook_rss_feed(self, page_slug: str, institution_name: str, trust_tier: float, always_ingest: bool):
    """
    Fetches a single Facebook page's RSS Bridge feed and ingests new posts
    as InstitutionalAlerts with vector embeddings.

    Args:
        page_slug:        Facebook page slug (e.g. 'ReserveBankMalawi')
        institution_name: Human-readable institution name for DB lookup
        trust_tier:       Trust weight (1.0 = official government, 0.85 = media)
        always_ingest:    If True, skip AI fraud classification and store all posts
    """
    feed_url = _build_rss_url(page_slug)
    logger.info("[FacebookRSS] Polling %s → %s", institution_name, feed_url)

    db = SessionLocal()
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning("[FacebookRSS] Feed parse error for %s: %s", institution_name, feed.bozo_exception)

        institution = _get_or_create_institution(db, institution_name)
        if not institution:
            logger.error("[FacebookRSS] Could not resolve institution: %s", institution_name)
            return f"Skipped: no institution record for {institution_name}"

        new_posts = 0
        for entry in feed.entries[:10]:  # Max 10 most-recent per poll
            url: str = getattr(entry, "link", "") or ""
            title: str = getattr(entry, "title", "") or ""
            content: str = (
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
                or ""
            )

            if not url or not (title or content):
                continue

            # Deduplicate — skip if already indexed
            existing = (
                db.query(InstitutionalAlert)
                .filter(InstitutionalAlert.source_url == url)
                .first()
            )
            if existing:
                continue

            # Decide whether to ingest this post
            text_for_embed = f"{title}. {content}".strip()
            if not always_ingest:
                is_fraud_alert = classify_fraud_alert(title, content)
                if not is_fraud_alert:
                    logger.debug("[FacebookRSS] Skipping non-alert post from %s: %s", institution_name, title[:60])
                    continue

            # Parse publication date safely
            # Use calendar.timegm() to avoid FeedParserDict subscript type issues
            published: datetime.datetime | None = None
            raw_time = getattr(entry, "published_parsed", None)
            if raw_time is not None:
                try:
                    timestamp = calendar.timegm(raw_time)  # accepts time.struct_time directly
                    published = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                except (TypeError, ValueError, OverflowError):
                    published = None

            # Generate embedding
            embedding = get_embedding(text_for_embed)

            alert = InstitutionalAlert(
                institution_id=institution.id,
                title=title or f"[Facebook] {institution_name} Post",
                alert_text=content[:3000],
                source_url=url,
                published_date=published or datetime.datetime.now(datetime.UTC),
                embedding=embedding,
            )
            db.add(alert)
            db.commit()
            new_posts += 1
            logger.info("[FacebookRSS] ✓ Ingested from %s: %s", institution_name, title[:80])

        return f"Ingested {new_posts} new post(s) from {institution_name}"

    except Exception as exc:
        db.rollback()
        logger.error("[FacebookRSS] Error processing %s: %s", institution_name, exc)
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Orchestrator — polls all configured feeds (called by Celery beat)
# ---------------------------------------------------------------------------

@celery_app.task(name="poll_facebook_rss_feeds")
def poll_facebook_rss_feeds():
    """
    Dispatcher task called every 5 minutes by Celery beat.
    Fans out individual ingest_facebook_rss_feed tasks for each configured page.
    """
    logger.info("[FacebookRSS] Starting poll cycle for %d feeds", len(FACEBOOK_RSS_FEEDS))
    dispatched = 0
    for feed_cfg in FACEBOOK_RSS_FEEDS:
        ingest_facebook_rss_feed.delay(
            page_slug=feed_cfg.page_slug,
            institution_name=feed_cfg.institution_name,
            trust_tier=feed_cfg.trust_tier,
            always_ingest=feed_cfg.always_ingest,
        )
        dispatched += 1
    logger.info("[FacebookRSS] Dispatched %d feed ingestion tasks", dispatched)
    return f"Dispatched {dispatched} Facebook RSS ingestion tasks"
