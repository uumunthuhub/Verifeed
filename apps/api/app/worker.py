import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.ingestion", "app.services.fraud_ingestion"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "poll-institutions-daily": {
        "task": "poll_all_institutions",
        "schedule": 86400.0, # Run daily
    },
    "ingest-news-hourly": {
        "task": "ingest_all_sources",
        "schedule": 3600.0, # Run hourly
    }
}
