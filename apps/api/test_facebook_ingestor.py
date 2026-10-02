#!/usr/bin/env python3
"""
Phase 1 — Facebook RSS Ingestor Manual Test Script.

Run this to:
  1. Immediately fire the RSS poll cycle against all configured Facebook pages
  2. Tail the Celery worker logs to see what gets ingested
  3. Query the database to verify InstitutionalAlerts were created

Usage (from apps/api directory with .venv active):
    uv run python test_facebook_ingestor.py

Requirements:
  - RSS Bridge container must be running:
      docker compose up rss-bridge -d
  - Redis must be running:
      docker compose up redis -d
  - Database must be running and migrated:
      docker compose up db -d
  - Celery worker must be running in another terminal:
      uv run celery -A app.worker.celery_app worker --loglevel=info
"""

import os
import sys

# Allow running from the apps/api directory
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://verifeed_user:verifeed_password@localhost:5433/verifeed_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RSS_BRIDGE_URL", "http://localhost:3001")  # docker-compose exposes port 3001 → container:80

from app.services.facebook_ingestor import (
    FACEBOOK_RSS_FEEDS,
    _build_rss_url,
    poll_facebook_rss_feeds,
    ingest_facebook_rss_feed,
)
import feedparser

print("\n" + "=" * 60)
print("  VeriFeed — Facebook RSS Bridge Ingestor Test")
print("=" * 60)

# Step 1: Check RSS Bridge is reachable
print("\n[1] Checking RSS Bridge connectivity...")
rss_bridge = os.getenv("RSS_BRIDGE_URL", "http://localhost:3001")
test_feed = _build_rss_url("ReserveBankMalawi")
print(f"    Feed URL: {test_feed}")

try:
    result = feedparser.parse(test_feed)
    if result.bozo:
        print(f"    ⚠️  Parse warning: {result.bozo_exception}")
    entry_count = len(result.entries)
    print(f"    ✓  RSS Bridge reachable — {entry_count} entries returned from ReserveBankMalawi")
    if entry_count > 0:
        print(f"    ✓  Latest post: {(result.entries[0].get('title') or 'No title')[:80]}")
except Exception as e:
    print(f"    ✗  RSS Bridge unreachable: {e}")
    print("    → Make sure RSS Bridge is running: docker compose up rss-bridge -d")
    sys.exit(1)

# Step 2: Show all configured feeds
print(f"\n[2] Configured feeds ({len(FACEBOOK_RSS_FEEDS)} pages):")
for cfg in FACEBOOK_RSS_FEEDS:
    mode = "always_ingest" if cfg.always_ingest else "fraud_only"
    print(f"    • {cfg.institution_name:<40} tier={cfg.trust_tier}  mode={mode}")

# Step 3: Dispatch the full poll cycle
print("\n[3] Dispatching poll_facebook_rss_feeds task...")

try:
    # Option A: Run synchronously (no Celery worker needed, for quick testing)
    print("    Running synchronously (no worker required)...")
    from app.services.facebook_ingestor import ingest_facebook_rss_feed
    total_ingested = 0
    for cfg in FACEBOOK_RSS_FEEDS:
        print(f"    → Polling {cfg.institution_name}...", end=" ", flush=True)
        try:
            result_msg = ingest_facebook_rss_feed(
                page_slug=cfg.page_slug,
                institution_name=cfg.institution_name,
                trust_tier=cfg.trust_tier,
                always_ingest=cfg.always_ingest,
            )
            print(f"✓  {result_msg}")
        except Exception as e:
            print(f"✗  {e}")
except Exception as e:
    print(f"    ✗  Error during sync run: {e}")

# Step 4: Query DB to show what was stored
print("\n[4] Verifying database records...")
try:
    from app.db.session import SessionLocal
    from app.models.institution import InstitutionalAlert, Institution

    db = SessionLocal()
    total_alerts = db.query(InstitutionalAlert).count()
    recent = (
        db.query(InstitutionalAlert)
        .order_by(InstitutionalAlert.id.desc())
        .limit(5)
        .all()
    )
    db.close()

    print(f"    Total InstitutionalAlerts in DB: {total_alerts}")
    print("    5 most recent:")
    for alert in recent:
        print(f"      [{alert.id}] {alert.title[:60]} — {alert.source_url[:50]}")
except Exception as e:
    print(f"    ✗  DB query error: {e}")

print("\n" + "=" * 60)
print("  Phase 1 test complete.")
print("=" * 60 + "\n")
