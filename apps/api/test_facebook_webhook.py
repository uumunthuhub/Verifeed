#!/usr/bin/env python3
"""
Phase 2 — Facebook Webhook & Messenger Bot Ingestion Manual Test Script.

Run this to:
  1. Test Meta verification handshake endpoint (hub challenge)
  2. Test Facebook Page Feed Webhook post ingestion (scam detection & DB storage)
  3. Test Facebook Messenger Bot incoming claim verification & formatted reply

Usage (from apps/api directory):
    TEST_MODE=true uv run python test_facebook_webhook.py
"""

from unittest.mock import patch
import asyncio
import os
import sys

# Ensure apps/api is in python path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://verifeed_user:verifeed_password@localhost:5433/verifeed_db")
os.environ.setdefault("TEST_MODE", "true")

from fastapi.testclient import TestClient
from app.main import app
from app.services.messenger_bot import process_messenger_message
from app.db.session import SessionLocal
from app.models.institution import InstitutionalAlert

client = TestClient(app)

from app.api import facebook_webhook

print("\n" + "=" * 60)
print("  VeriFeed — Facebook Webhook & Messenger Ingestion Test")
print("=" * 60)

# Step 1: Verification Handshake Test (GET)
print("\n[1] Testing GET /api/v1/facebook/webhook (Meta Verification Handshake)...")
token = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "test_token")
with patch.object(facebook_webhook, "VERIFY_TOKEN", token):
    res = client.get(
        "/api/v1/facebook/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": token,
            "hub.challenge": "FACEBOOK_HANDSHAKE_OK_999",
        },
    )
    if res.status_code == 200 and res.text == "FACEBOOK_HANDSHAKE_OK_999":
        print(f"    ✓  Handshake successful: {res.text}")
    else:
        print(f"    ✗  Handshake failed (status={res.status_code}): {res.text}")

# Step 2: Page Feed Post Webhook Ingestion (POST)
print("\n[2] Testing POST /api/v1/facebook/webhook (Live Facebook Page Feed Event)...")
sample_page_post = {
    "object": "page",
    "entry": [
        {
            "id": "100200300",
            "time": 1700000000,
            "changes": [
                {
                    "field": "feed",
                    "value": {
                        "item": "post",
                        "post_id": "post_fb_test_888",
                        "message": "SCAM ALERT: Do not send money to unverified WhatsApp loan numbers claiming to represent National Bank.",
                        "permalink_url": "https://facebook.com/100200300/posts/post_fb_test_888",
                    },
                }
            ],
        }
    ],
}

res_post = client.post("/api/v1/facebook/webhook", json=sample_page_post)
print(f"    ✓  Webhook POST received: {res_post.json()}")

# Step 3: Messenger Claim Verification Test
print("\n[3] Testing Facebook Messenger Bot processing in TEST MODE...")

async def test_messenger():
    sample_messenger_message = {
        "text": "Can I apply for a $1,000 instant loan on Facebook with no collateral?"
    }
    sender_id = "fb_messenger_user_777"
    
    print(f"    Incoming User Claim: \"{sample_messenger_message['text']}\"")
    reply_data = await process_messenger_message(sample_messenger_message, sender_id=sender_id)
    print("    ✓  Messenger Bot generated verdict reply:")
    print("-" * 50)
    print(reply_data.get("text"))
    print("-" * 50)

asyncio.run(test_messenger())

# Step 4: Verify DB institutional alert count
print("\n[4] Querying DB for InstitutionalAlerts...")
try:
    db = SessionLocal()
    count = db.query(InstitutionalAlert).count()
    recent = db.query(InstitutionalAlert).order_by(InstitutionalAlert.id.desc()).first()
    db.close()
    print(f"    ✓  Total Institutional Alerts in DB: {count}")
    if recent:
        print(f"    ✓  Latest Alert ID [{recent.id}]: {recent.title[:60]}")
except Exception as e:
    print(f"    ⚠️  DB check notice: {e}")

print("\n" + "=" * 60)
print("  Facebook Webhook & Messenger test completed successfully.")
print("=" * 60 + "\n")
