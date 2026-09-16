"""
Scam Pattern Seed Data

Initial seed of known scam patterns, suspicious short codes, and known
fraudulent domains for the VeriFeed fraud intelligence database.

Run with:
    cd apps/api && uv run python -m database.seeds.scam_patterns

Architecture note: These seed patterns are inputs to LocalScreeningEngine's
Stage 1 deterministic screening. They do NOT by themselves produce verdicts —
only the full evidence pipeline (Stage 2) can issue a final verdict.
"""

import os
import sys

# Add the apps/api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.models.fraud import KnownScamPattern, SuspiciousSender, SuspiciousUrl

# ---------------------------------------------------------------------------
# Scam phrase patterns
# ---------------------------------------------------------------------------

SCAM_PHRASE_PATTERNS: list[dict] = [
    {
        "name": "urgency_act_now",
        "pattern_type": "keyword_phrase",
        "pattern_value": "act now",
        "description": "Creates false urgency to pressure victims into immediate action",
        "severity": "medium",
    },
    {
        "name": "urgency_limited_time",
        "pattern_type": "keyword_phrase",
        "pattern_value": "limited time",
        "description": "Artificial time pressure — a hallmark of advance-fee and prize scams",
        "severity": "medium",
    },
    {
        "name": "urgency_account_suspended",
        "pattern_type": "keyword_phrase",
        "pattern_value": "account suspended",
        "description": "Fake account suspension claim to trick users into clicking phishing links",
        "severity": "high",
    },
    {
        "name": "monetary_send_money",
        "pattern_type": "keyword_phrase",
        "pattern_value": "send money",
        "description": "Direct request to send funds — immediate high-risk indicator",
        "severity": "high",
    },
    {
        "name": "monetary_processing_fee",
        "pattern_type": "keyword_phrase",
        "pattern_value": "processing fee",
        "description": "Advance-fee scam: requesting a 'fee' before releasing non-existent funds",
        "severity": "high",
    },
    {
        "name": "monetary_activation_fee",
        "pattern_type": "keyword_phrase",
        "pattern_value": "activation fee",
        "description": "Fake activation fee before promised reward or loan",
        "severity": "high",
    },
    {
        "name": "monetary_registration_fee",
        "pattern_type": "keyword_phrase",
        "pattern_value": "registration fee",
        "description": "Fake registration fee — common in job offer and prize scams",
        "severity": "high",
    },
    {
        "name": "prize_you_have_won",
        "pattern_type": "keyword_phrase",
        "pattern_value": "you have won",
        "description": "Unsolicited prize notification — lottery/prize scam",
        "severity": "high",
    },
    {
        "name": "prize_claim_your_prize",
        "pattern_type": "keyword_phrase",
        "pattern_value": "claim your prize",
        "description": "Prompts victim to claim a prize they never entered to win",
        "severity": "high",
    },
    {
        "name": "prize_lucky_winner",
        "pattern_type": "keyword_phrase",
        "pattern_value": "lucky winner",
        "description": "Classic lottery/prize scam language",
        "severity": "medium",
    },
]

# ---------------------------------------------------------------------------
# Suspicious URL patterns (regex)
# ---------------------------------------------------------------------------

SUSPICIOUS_URL_PATTERNS: list[dict] = [
    {
        "name": "bitly_shortener",
        "pattern_type": "regex_url",
        "pattern_value": r"bit\.ly/",
        "description": "Bit.ly URL shortener — hides destination domain in phishing messages",
        "severity": "high",
    },
    {
        "name": "tinyurl_shortener",
        "pattern_type": "regex_url",
        "pattern_value": r"tinyurl\.com/",
        "description": "TinyURL shortener — commonly used to obfuscate phishing domains",
        "severity": "high",
    },
    {
        "name": "airtel_typosquat",
        "pattern_type": "regex_url",
        "pattern_value": r"airtel-mw\.",
        "description": "Typosquat impersonating Airtel Malawi — not the official domain (airtelmalawi.com)",
        "severity": "high",
    },
    {
        "name": "standard_bank_typosquat",
        "pattern_type": "regex_url",
        "pattern_value": r"standard-bank-mw\.",
        "description": "Typosquat impersonating Standard Bank Malawi",
        "severity": "high",
    },
    {
        "name": "tnm_mpamba_typosquat",
        "pattern_type": "regex_url",
        "pattern_value": r"tnm-mpamba\.",
        "description": "Typosquat impersonating TNM Mpamba",
        "severity": "high",
    },
    {
        "name": "malawi_gov_typosquat",
        "pattern_type": "regex_url",
        "pattern_value": r"malawi-gov\.",
        "description": "Typosquat impersonating the Malawi Government",
        "severity": "high",
    },
]

# ---------------------------------------------------------------------------
# Suspicious senders (known reported)
# ---------------------------------------------------------------------------

SUSPICIOUS_SENDERS: list[dict] = [
    {
        "sender_value": "+12025551234",
        "sender_type": "phone_number",
        "status": "reported",
        "notes": "US number reported in SMS prize phishing to Malawian numbers",
    },
    {
        "sender_value": "+447700900001",
        "sender_type": "phone_number",
        "status": "reported",
        "notes": "UK number used in loan offer SMS phishing",
    },
]

# ---------------------------------------------------------------------------
# Known suspicious domains
# ---------------------------------------------------------------------------

SUSPICIOUS_DOMAINS: list[dict] = [
    {
        "domain": "airtel-mw.promo",
        "status": "confirmed_malicious",
        "threat_type": "impersonation",
        "notes": "Confirmed phishing domain impersonating Airtel Money Malawi",
    },
    {
        "domain": "standardbank-mw.net",
        "status": "reported",
        "threat_type": "phishing",
        "notes": "Reported phishing domain impersonating Standard Bank",
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

def seed_scam_patterns(db) -> None:
    """Seed the fraud intelligence tables with initial pattern data."""

    seeded = {"patterns": 0, "urls": 0, "senders": 0, "domains": 0}

    # Scam phrase patterns
    for data in SCAM_PHRASE_PATTERNS:
        existing = db.query(KnownScamPattern).filter_by(name=data["name"]).first()
        if not existing:
            db.add(KnownScamPattern(**data))
            seeded["patterns"] += 1

    # URL patterns
    for data in SUSPICIOUS_URL_PATTERNS:
        existing = db.query(KnownScamPattern).filter_by(name=data["name"]).first()
        if not existing:
            db.add(KnownScamPattern(**data))
            seeded["urls"] += 1

    # Suspicious senders
    for data in SUSPICIOUS_SENDERS:
        existing = db.query(SuspiciousSender).filter_by(sender_value=data["sender_value"]).first()
        if not existing:
            db.add(SuspiciousSender(**data))
            seeded["senders"] += 1

    # Suspicious domains
    for data in SUSPICIOUS_DOMAINS:
        existing = db.query(SuspiciousUrl).filter_by(domain=data["domain"]).first()
        if not existing:
            db.add(SuspiciousUrl(**data))
            seeded["domains"] += 1

    db.commit()
    print(
        f"Seeded: {seeded['patterns']} phrase patterns, "
        f"{seeded['urls']} URL patterns, "
        f"{seeded['senders']} suspicious senders, "
        f"{seeded['domains']} suspicious domains"
    )


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_scam_patterns(db)
    finally:
        db.close()
