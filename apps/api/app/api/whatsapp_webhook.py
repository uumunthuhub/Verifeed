"""
WhatsApp Webhook Receiver — Phase 3 Live Data Pipeline.
"""

import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from app.services.whatsapp_bot import process_whatsapp_message

logger = logging.getLogger(__name__)
router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
WABA_TOKEN   = os.getenv("WHATSAPP_BUSINESS_API_TOKEN", "")
PHONE_ID     = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("[WhatsApp] Webhook verification successful.")
        return int(hub_challenge) if hub_challenge else 0
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                background_tasks.add_task(
                    process_whatsapp_message,
                    message=message,
                    sender_phone=message.get("from"),
                    msg_type=message.get("type"),
                )
    return {"status": "ok"}
