"""
Facebook Webhook Receiver — Phase 2 Live Data Pipeline.

Handles two types of requests from Meta:
  1. GET  /api/v1/facebook/webhook — Meta's verification handshake (hub challenge)
  2. POST /api/v1/facebook/webhook — Live page feed events (new posts)

When a subscribed Facebook Page publishes a new post, Meta sends a POST payload here.
The payload is parsed, classified as fraud/non-fraud, and saved as an InstitutionalAlert.
"""

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from app.db.session import SessionLocal
from app.models.institution import Institution, InstitutionalAlert
from app.services.ingestion import get_embedding
from app.services.fraud_ingestion import classify_fraud_alert

logger = logging.getLogger(__name__)
router = APIRouter()

VERIFY_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET   = os.getenv("FACEBOOK_APP_SECRET", "")


# ---------------------------------------------------------------------------
# Step 1: Meta verification handshake (GET)
# ---------------------------------------------------------------------------

@router.get("/webhook")
def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    """
    Meta sends a GET request when you first set up a Webhook or update the URL.
    We must respond with hub.challenge if hub.verify_token matches our secret.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("[Webhook] Meta verification challenge accepted.")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("[Webhook] Verification failed — token mismatch or bad mode.")
    raise HTTPException(status_code=403, detail="Verification failed")


# ---------------------------------------------------------------------------
# Step 2: Receive live page feed events (POST)
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Meta sends a POST request for every subscribed page event (new post, etc).
    We validate the X-Hub-Signature-256 header, then process in the background.
    """
    body = await request.body()

    # --- Validate the request is genuinely from Meta ---
    if APP_SECRET:
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        mac = hmac.new(APP_SECRET.encode(), body, hashlib.sha256)
        expected = "sha256=" + mac.hexdigest()
        if not hmac.compare_digest(signature_header, expected):
            logger.warning("[Webhook] Invalid X-Hub-Signature-256 — request rejected.")
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload: dict[str, Any] = await request.json()

    # Respond to Meta immediately with 200 OK (Meta requires <5s response time)
    # Process feeds synchronously in background
    background_tasks.add_task(_process_webhook_payload, payload)
    
    # Process Messenger messages (if any)
    if payload.get("object") == "page":
        from app.services.messenger_bot import process_messenger_message
        for entry in payload.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                message = messaging_event.get("message", {})
                if sender_id and message and not message.get("is_echo"):
                    background_tasks.add_task(
                        process_messenger_message,
                        message=message,
                        sender_id=sender_id
                    )

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------

def _process_webhook_payload(payload: dict[str, Any]) -> None:
    """
    Parse the Meta webhook payload and save qualifying posts as InstitutionalAlerts.

    Meta Page Feed payload structure:
    {
      "object": "page",
      "entry": [
        {
          "id": "<page_id>",
          "time": 1234567890,
          "changes": [
            {
              "value": {
                "message": "Post text here",
                "post_id": "...",
                "permalink_url": "https://facebook.com/..."
              },
              "field": "feed"
            }
          ]
        }
      ]
    }
    """
    if payload.get("object") != "page":
        logger.debug("[Webhook] Ignoring non-page object: %s", payload.get("object"))
        return

    db = SessionLocal()
    try:
        for entry in payload.get("entry", []):
            page_id = str(entry.get("id", ""))
            for change in entry.get("changes", []):
                if change.get("field") != "feed":
                    continue

                value = change.get("value", {})
                message: str = value.get("message", "") or value.get("story", "")
                post_id: str = value.get("post_id", "") or value.get("id", "")
                permalink: str = value.get("permalink_url", f"https://facebook.com/{page_id}/posts/{post_id}")

                if not message:
                    logger.debug("[Webhook] Skipping entry with no message text.")
                    continue

                logger.info("[Webhook] Received post from page %s: %s", page_id, message[:80])

                # --- Look up the institution by its Facebook page ID ---
                institution = (
                    db.query(Institution)
                    .filter(Institution.verified_social.contains({"facebook_page_id": page_id}))
                    .first()
                )

                # Fallback: create or use a generic "Facebook Webhook" institution row
                if not institution:
                    institution = db.query(Institution).filter(Institution.name == "Facebook Webhook").first()
                    if not institution:
                        institution = Institution(
                            name="Facebook Webhook",
                            sector="social_media",
                            website_url="https://facebook.com",
                        )
                        db.add(institution)
                        db.flush()

                # --- Check for duplicate (same post_id already stored) ---
                duplicate = (
                    db.query(InstitutionalAlert)
                    .filter(InstitutionalAlert.source_url.contains(post_id))
                    .first()
                )
                if duplicate:
                    logger.debug("[Webhook] Duplicate post skipped: %s", post_id)
                    continue

                # --- Classify: is this a fraud/scam-related post? ---
                title = (message[:120] + "…") if len(message) > 120 else message

                should_ingest = classify_fraud_alert(title=title, content=message)

                if not should_ingest:
                    logger.info("[Webhook] Post not fraud-related, skipping: %s", message[:60])
                    continue

                # --- Generate embedding ---
                embedding = get_embedding(message)

                # --- Save to database ---
                alert = InstitutionalAlert(
                    institution_id=institution.id,
                    title=title,
                    alert_text=message,
                    source_url=permalink,
                    embedding=embedding,
                )
                db.add(alert)
                db.commit()
                logger.info("[Webhook] ✓ Saved new alert (id=%s) from page %s", alert.id, page_id)

    except Exception:
        logger.exception("[Webhook] Error processing webhook payload")
        db.rollback()
    finally:
        db.close()
