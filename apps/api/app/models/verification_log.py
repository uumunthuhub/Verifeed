import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.base import Base


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    
    # Dual verdict system as per new architecture
    claim_verdict = Column(String(50), nullable=True, index=True)  # True, False, Partly True, Misleading, Insufficient Evidence
    message_authenticity_verdict = Column(String(50), nullable=True, index=True)  # Verified Official, Likely Legitimate, Unverified, Suspicious, Likely Fraudulent, Confirmed Fraudulent
    
    # Legacy single verdict for backward compatibility
    verdict = Column(String(50), nullable=False, index=True)  # Confirmed Scam, Confirmed, Unconfirmed, Disputed, No Coverage Found
    
    confidence_score = Column(Float, default=0.0)
    risk_level = Column(String(20), nullable=True)  # High, Medium, Low
    
    # Extracted entities from message
    extracted_sender = Column(String(255), nullable=True)  # Detected sender identity
    extracted_numbers = Column(JSON, nullable=True)  # Detected phone numbers
    extracted_urls = Column(JSON, nullable=True)  # Detected URLs
    extracted_institutions = Column(JSON, nullable=True)  # Detected institution names
    
    # Verification details
    summary = Column(Text, nullable=False)
    evidence_sources = Column(JSON, nullable=True)  # Array of { title, url, outlet, excerpt, type }
    
    # Official channel verification results
    sender_verified = Column(Boolean, nullable=True)  # Whether sender matched official registry
    channel_verified = Column(Boolean, nullable=True)  # Whether number/channel matched official registry
    
    # User guidance
    recommended_actions = Column(JSON, nullable=True)  # Array of recommended user actions

    # D2: Evidence pipeline methodology — human-readable explanation of verdict reasoning
    methodology = Column(Text, nullable=True)
    # E.g. "Found 2 official institutional alerts. Retrieved 3 news articles. Verdict grounded by Gemini."

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
