"""
VeriFeed Master Database Seeder.

Executes all seeding workflows sequentially:
1. Governed Source Registry (app.db.seed)
2. Fraud Intelligence & Scam Patterns (database.seeds.scam_patterns)
3. Verified Institutions & Alerts (app.api.institutions)
4. News Stories & Articles (database.seeds.seed_stories)
5. Text Dataset Samples & Scams (ingest_samples.py)
6. Media Assets & Dataset Samples (ingest_media_samples.py)
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.db.seed import seed as seed_sources
from database.seeds.scam_patterns import seed_scam_patterns
from database.seeds.seed_stories import seed_news_data
from ingest_samples import ingest_samples
from ingest_media_samples import scan_and_ingest_media
from app.models.institution import Institution, InstitutionalAlert
from app.api.institutions import SEED_INSTITUTIONS
from app.services.ai import get_ai_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VeriFeedMasterSeeder")


def seed_institutions_registry(db):
    """Seed 25+ verified Malawian institutions and their official fraud alerts."""
    logger.info("Seeding Verified Institutions & Official Alerts...")
    ai_service = get_ai_service()
    created_insts = 0
    created_alerts = 0

    for inst_data in SEED_INSTITUTIONS:
        inst = db.query(Institution).filter(Institution.name == inst_data["name"]).first()
        if not inst:
            inst = Institution(
                name=inst_data["name"],
                sector=inst_data["sector"],
                website_url=inst_data["website_url"],
            )
            db.add(inst)
            db.flush()
            created_insts += 1

        for alert_data in inst_data["alerts"]:
            existing_alert = db.query(InstitutionalAlert).filter(
                InstitutionalAlert.title == alert_data["title"]
            ).first()

            if not existing_alert:
                full_text = f"{alert_data['title']} {alert_data['alert_text']}"
                emb = ai_service.embed(full_text)

                alert = InstitutionalAlert(
                    institution_id=inst.id,
                    title=alert_data["title"],
                    alert_text=alert_data["alert_text"],
                    source_url=alert_data["source_url"],
                    embedding=emb,
                )
                db.add(alert)
                created_alerts += 1

    db.commit()
    logger.info(f"✅ Institutions Seeding Complete: {created_insts} new institutions, {created_alerts} new alerts.")


def run_master_seeding():
    logger.info("==================================================")
    logger.info("   Starting VeriFeed Master Database Seeding      ")
    logger.info("==================================================")

    # Ensure all tables exist in target database
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # Ensure all models are registered
    logger.info("Ensuring database tables are initialized...")
    Base.metadata.create_all(bind=engine)

    # Step 1: Governed Source Registry
    logger.info("\n--- STEP 1: Seeding Governed Source Registry ---")
    seed_sources()

    # Step 2: Scam Patterns & Fraud Intelligence
    logger.info("\n--- STEP 2: Seeding Scam Patterns & Suspicious Identifiers ---")
    db = SessionLocal()
    try:
        seed_scam_patterns(db)
    finally:
        db.close()

    # Step 3: Verified Institutions & Alerts
    logger.info("\n--- STEP 3: Seeding Verified Institutions & Alerts ---")
    db = SessionLocal()
    try:
        seed_institutions_registry(db)
    finally:
        db.close()

    # Step 4: News Stories & Articles
    logger.info("\n--- STEP 4: Seeding News Stories & Articles ---")
    seed_news_data()

    # Step 5: Text Dataset Samples
    logger.info("\n--- STEP 5: Ingesting Text Dataset Samples & Scams ---")
    ingested_text_count = ingest_samples()

    # Step 6: Media Assets
    logger.info("\n--- STEP 6: Ingesting Media Assets ---")
    ingested_media_count = scan_and_ingest_media()

    logger.info("==================================================")
    logger.info("   VeriFeed Database Master Seeding Complete!     ")
    logger.info(f"   - Text Samples: {ingested_text_count}")
    logger.info(f"   - Media Assets: {ingested_media_count}")
    logger.info("==================================================")


if __name__ == "__main__":
    run_master_seeding()
