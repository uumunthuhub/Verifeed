import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.services.ingestion",
        "app.services.fraud_ingestion",
        "app.services.facebook_ingestor",  # Phase 1: Facebook RSS Bridge
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    # Existing schedules
    "poll-institutions": {
        "task": "poll_all_institutions",
        "schedule": 900.0,  # Every 15 minutes
    },
    "ingest-news": {
        "task": "ingest_all_sources",
        "schedule": 900.0,  # Every 15 minutes
    },
    # Phase 1: Facebook RSS Bridge — every 5 minutes
    "poll-facebook-rss-feeds": {
        "task": "poll_facebook_rss_feeds",
        "schedule": 300.0,  # Every 5 minutes
    },
}
