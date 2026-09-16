"""
Fraud Intelligence Domain Models — Phase B

These models support the proactive protection architecture:

  FraudSignal      — scored risk indicators from content analysis
  KnownScamPattern — maintained database of scam pattern definitions
  SuspiciousSender — flagged phone numbers / short codes / sender IDs
  SuspiciousUrl    — flagged domains and URL patterns
  VerificationCase — links UserSubmission → VerificationLog as a formal case

Architecture rule: a UserSubmission cluster + community reports ≠ Confirmed Scam.
Only institutional backing + verified evidence elevates to a final verdict.
"""

import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class FraudSignal(Base):
    """
    A scored risk indicator extracted from a piece of content during Stage 1
    or Stage 2 screening.

    These are intermediate signals — NOT final verdicts.
    """
    __tablename__ = "fraud_signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_type = Column(String(50), nullable=False, index=True)
    # Types: urgency_language, suspicious_url, known_scam_number,
    #        impersonation_keyword, monetary_request, unsolicited_prize,
    #        suspicious_sender, institution_mention
    description = Column(Text, nullable=False)
    matched_text = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="medium")  # low | medium | high

    # Optional link to a specific submission that triggered this signal
    submission_id = Column(Integer, ForeignKey("user_submissions.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class KnownScamPattern(Base):
    """
    A maintained database of known scam pattern definitions.

    Used by LocalScreeningEngine for Stage 1 deterministic matching.
    Patterns are regex strings or plain phrase lists keyed by type.
    """
    __tablename__ = "known_scam_patterns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)
    # Types: keyword_phrase, regex_url, regex_sender, regex_phone, ussd_code

    pattern_value = Column(Text, nullable=False)
    # The actual phrase, regex, or keyword

    description = Column(Text, nullable=True)
    # Human-readable description of what this pattern detects

    severity = Column(String(20), nullable=False, default="medium")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    hit_count = Column(Integer, nullable=False, default=0)
    # How many times this pattern has been matched (for tuning)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class SuspiciousSender(Base):
    """
    A flagged phone number, short code, or sender ID.

    Source: community submissions + institutional alerts.
    Note: a high report count alone does NOT confirm fraud — only
    institutional verification or law enforcement confirmation does.
    """
    __tablename__ = "suspicious_senders"

    id = Column(Integer, primary_key=True, index=True)
    sender_value = Column(String(100), nullable=False, unique=True, index=True)
    # Phone: +265991234567, Short code: 212, Sender ID: FAKEBANK

    sender_type = Column(String(30), nullable=False)
    # Types: phone_number, short_code, sender_id, email

    report_count = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="reported", index=True)
    # Statuses: reported, under_review, confirmed_suspicious, cleared

    notes = Column(Text, nullable=True)
    first_reported = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    last_reported = Column(DateTime, default=datetime.datetime.utcnow)


class SuspiciousUrl(Base):
    """
    A flagged domain or URL pattern.

    Source: community submissions + external threat intelligence.
    """
    __tablename__ = "suspicious_urls"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    url_pattern = Column(Text, nullable=True)
    # Optional regex pattern if the full domain isn't known

    report_count = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="reported", index=True)
    # Statuses: reported, under_review, confirmed_malicious, cleared

    threat_type = Column(String(50), nullable=True)
    # Types: phishing, impersonation, malware, advance_fee_scam

    notes = Column(Text, nullable=True)
    first_reported = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    last_reported = Column(DateTime, default=datetime.datetime.utcnow)


class VerificationCase(Base):
    """
    Links a user-submitted report (UserSubmission) to a formal
    verification investigation (VerificationLog).

    Provides traceability: submission → screening signals → evidence → verdict.
    One submission can be linked to one verification case.
    """
    __tablename__ = "verification_cases"

    id = Column(Integer, primary_key=True, index=True)

    submission_id = Column(
        Integer, ForeignKey("user_submissions.id"), nullable=True, index=True
    )
    verification_log_id = Column(
        Integer, ForeignKey("verification_logs.id"), nullable=True, index=True
    )

    # Stage 1 screening result snapshot
    screening_risk_level = Column(String(20), nullable=True)
    screening_signals = Column(JSON, nullable=True)
    # Array of { signal_type, description, severity }

    # Case lifecycle
    status = Column(String(30), nullable=False, default="screening", index=True)
    # Statuses: screening, pending_verification, verified, closed

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
