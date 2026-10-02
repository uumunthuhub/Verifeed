"""
Facebook Messenger Bot Service
"""
import logging
import os
import httpx

from app.db.session import SessionLocal
from app.services.verification_agent import verify_claim

logger = logging.getLogger(__name__)

PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")

async def send_messenger_reply(recipient_id: str, text: str):
    if not PAGE_ACCESS_TOKEN:
        logger.warning("[Messenger] Missing PAGE_ACCESS_TOKEN, cannot send reply.")
        return
        
    url = f"https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            logger.info("[Messenger] Reply sent successfully to %s", recipient_id)
        except Exception as e:
            logger.error("[Messenger] Failed to send reply: %s", e)

async def process_messenger_message(message: dict, sender_id: str):
    claim_text = message.get("text", "")

    if not claim_text.strip():
        if "attachments" in message:
            logger.warning("[Messenger] Attachment received but not implemented yet.")
        await send_messenger_reply(
            sender_id,
            "⚠️ VeriFeed could not extract readable content. Please forward the original text or a clearer image."
        )
        return

    logger.info("[Messenger] Processing claim for %s: %s", sender_id, claim_text[:50])

    # Run verification
    db = SessionLocal()
    try:
        # verify_claim is an async function
        result = await verify_claim(db=db, query=claim_text)
        
        verdict_emoji = {"Confirmed Scam": "❌", "Confirmed": "✅", "Unconfirmed": "⚠️", "Disputed / False": "❌", "No Coverage Found": "🔍"}.get(
            result.get("verdict", ""), "🔍"
        )
        sources = result.get("sources", [])
        sources_text = "\n".join([f"• {s['title']} — {s['url']}" for s in sources[:3]])
        
        reply = (
            f"{verdict_emoji} *VeriFeed Verdict: {result.get('verdict', 'Unknown')}*\n\n"
            f"{result.get('summary', '')}\n\n"
            f"📰 *Evidence:*\n{sources_text or 'No sources found.'}\n\n"
            f"_Reply with any follow-up question about this claim._"
        )
        await send_messenger_reply(sender_id, reply)
    except Exception:
        logger.exception("[Messenger] Error processing claim")
        await send_messenger_reply(sender_id, "⚠️ An error occurred while verifying the claim. Please try again later.")
    finally:
        db.close()
