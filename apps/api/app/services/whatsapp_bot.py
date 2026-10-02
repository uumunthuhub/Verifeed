"""
WhatsApp Bot Service
"""
import logging
import os
import httpx

from app.db.session import SessionLocal
from app.services.verification_agent import verify_claim

logger = logging.getLogger(__name__)

WABA_TOKEN   = os.getenv("WHATSAPP_BUSINESS_API_TOKEN", "")
PHONE_ID     = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

async def send_whatsapp_reply(to: str, text: str):
    if not WABA_TOKEN or not PHONE_ID:
        logger.warning("[WhatsApp] Missing tokens, cannot send reply.")
        return
        
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp", 
        "to": to, 
        "type": "text", 
        "text": {"body": text}
    }
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("[WhatsApp] Reply sent successfully to %s", to)
        except Exception as e:
            logger.error("[WhatsApp] Failed to send reply: %s", e)

async def process_whatsapp_message(message: dict, sender_phone: str, msg_type: str):
    claim_text = ""

    if msg_type == "text":
        claim_text = message.get("text", {}).get("body", "")
    elif msg_type == "audio":
        # Placeholder for audio processing
        logger.warning("[WhatsApp] Audio message received but transcription not implemented yet.")
        claim_text = ""
    elif msg_type in ("image", "document"):
        # Placeholder for image OCR
        logger.warning(f"[WhatsApp] {msg_type} message received but OCR not implemented yet.")
        claim_text = ""

    if not claim_text.strip():
        await send_whatsapp_reply(
            sender_phone,
            "⚠️ VeriFeed could not extract readable content. Please forward the original text or a clearer image."
        )
        return

    logger.info("[WhatsApp] Processing claim for %s: %s", sender_phone, claim_text[:50])

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
        await send_whatsapp_reply(sender_phone, reply)
    except Exception:
        logger.exception("[WhatsApp] Error processing claim")
        await send_whatsapp_reply(sender_phone, "⚠️ An error occurred while verifying the claim. Please try again later.")
    finally:
        db.close()
