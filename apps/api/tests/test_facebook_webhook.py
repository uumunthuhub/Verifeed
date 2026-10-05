"""
Unit and integration tests for Facebook Webhook and Messenger Bot ingestion.
"""

import hashlib
import hmac
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.facebook_webhook import _process_webhook_payload
from app.services.messenger_bot import process_messenger_message, send_messenger_reply

client = TestClient(app)

VERIFY_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")


def test_facebook_webhook_verification_success():
    """Verify Meta handshake returns hub.challenge when token matches."""
    with patch("app.api.facebook_webhook.VERIFY_TOKEN", "test_secret_token"):
        response = client.get(
            "/api/v1/facebook/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_secret_token",
                "hub.challenge": "123456789",
            },
        )
        assert response.status_code == 200
        assert response.text == "123456789"


def test_facebook_webhook_verification_invalid_token():
    """Verify Meta handshake returns 403 when verify token is wrong."""
    with patch("app.api.facebook_webhook.VERIFY_TOKEN", "test_secret_token"):
        response = client.get(
            "/api/v1/facebook/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "123456789",
            },
        )
        assert response.status_code == 403


def test_facebook_webhook_signature_validation():
    """Verify POST request fails with 403 when signature does not match APP_SECRET."""
    secret = "my_app_secret"
    payload_data = b'{"object": "page"}'
    
    with patch("app.api.facebook_webhook.APP_SECRET", secret):
        # Invalid signature
        response = client.post(
            "/api/v1/facebook/webhook",
            content=payload_data,
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"},
        )
        assert response.status_code == 403

        # Valid signature
        valid_mac = "sha256=" + hmac.new(secret.encode(), payload_data, hashlib.sha256).hexdigest()
        response_valid = client.post(
            "/api/v1/facebook/webhook",
            content=payload_data,
            headers={"X-Hub-Signature-256": valid_mac},
        )
        assert response_valid.status_code == 200


def test_facebook_page_post_processing():
    """Test background processing of Facebook Page feed post event."""
    sample_payload = {
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
                            "post_id": "100200300_99999",
                            "message": "WARNING: SCAM ALERT! Fake loan page offering instant money.",
                            "permalink_url": "https://facebook.com/100200300/posts/99999",
                        },
                    }
                ],
            }
        ],
    }

    mock_db = MagicMock()
    # No existing duplicate alert
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.api.facebook_webhook.SessionLocal", return_value=mock_db), \
         patch("app.api.facebook_webhook.classify_fraud_alert", return_value=True), \
         patch("app.api.facebook_webhook.get_embedding", return_value=[0.1] * 1536):
        
        _process_webhook_payload(sample_payload)

        # Assert DB add and commit were called
        assert mock_db.add.called
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_messenger_bot_processing_test_mode(monkeypatch):
    """Test process_messenger_message generates formatted reply in test mode."""
    monkeypatch.setenv("TEST_MODE", "true")
    
    sample_message = {"text": "Is Reserve Bank giving free $500 grants?"}
    sender_id = "test_user_fb_123"

    mock_verdict = {
        "verdict": "Confirmed Scam",
        "summary": "This is a fraudulent scheme falsely impersonating RBM.",
        "sources": [{"title": "RBM Warning", "url": "https://rbm.mw/warning"}],
    }

    with patch("app.services.messenger_bot.SessionLocal"), \
         patch("app.services.messenger_bot.verify_claim", new_callable=AsyncMock, return_value=mock_verdict):

        result = await process_messenger_message(sample_message, sender_id)
        
        assert result["status"] == "test_mode"
        assert result["recipient_id"] == sender_id
        assert "❌ *VeriFeed Verdict: Confirmed Scam*" in result["text"]
        assert "RBM Warning" in result["text"]
