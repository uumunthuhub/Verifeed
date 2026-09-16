import pytest
from app.services.email_screener import EmailScreener
from app.schemas.email import EmailVerificationRequest


def test_domain_spoofing_detection():
    screener = EmailScreener()
    payload = EmailVerificationRequest(
        sender_address="security-update@scam-domain-123.com",
        display_name="PayPal Support",
        subject="Urgent: Your account is suspended",
        body_text="Please click http://bit.ly/verify-paypal to restore access immediately."
    )

    result = screener.screen(payload)
    assert result.risk_level == "High"
    assert result.domain_spoof_detected is True
    assert result.email_authenticity_verdict == "SPOOFED_SENDER"
    assert result.message_authenticity_verdict == "PHISHING / SCAM LURE"
    assert len(result.suspicious_links) > 0


def test_authentic_email_screening():
    screener = EmailScreener()
    payload = EmailVerificationRequest(
        sender_address="service@paypal.com",
        display_name="PayPal",
        subject="Your monthly statement is ready",
        body_text="Your receipt for transaction #12345 is ready to view in your account dashboard."
    )

    result = screener.screen(payload)
    assert result.risk_level == "Low"
    assert result.domain_spoof_detected is False
    assert result.email_authenticity_verdict == "AUTHENTIC"
    assert result.official_domain_match == "paypal.com"
