import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False, index=True)  # Banking, Telecom, Regulator, Government
    website_url = Column(String(500), nullable=False)
    
    # Official communication channels
    official_phone_numbers = Column(JSON, nullable=True)  # List of verified phone numbers
    official_sms_sender_ids = Column(JSON, nullable=True)  # List of verified SMS sender IDs
    official_short_codes = Column(JSON, nullable=True)  # List of verified short codes (e.g., 212, *212#)
    official_ussd_codes = Column(JSON, nullable=True)  # List of verified USSD codes
    official_email_domains = Column(JSON, nullable=True)  # List of official email domains
    verified_social_accounts = Column(JSON, nullable=True)  # List of verified social accounts with platforms
    customer_care_channels = Column(JSON, nullable=True)  # Official customer care contact info
    fraud_reporting_channels = Column(JSON, nullable=True)  # Official fraud reporting contact info
    legitimate_message_templates = Column(JSON, nullable=True)  # Known legitimate message patterns
    
    # Metadata
    verified_social = Column(String(500), nullable=True)  # Deprecated: use verified_social_accounts
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    alerts = relationship("InstitutionalAlert", back_populates="institution", cascade="all, delete-orphan")

class InstitutionalAlert(Base):
    __tablename__ = "institutional_alerts"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    title = Column(String(500), nullable=False)
    alert_text = Column(Text, nullable=False)
    source_url = Column(String(500), nullable=False)
    published_date = Column(DateTime, default=datetime.datetime.utcnow)
    embedding = Column(Vector(768), nullable=True)  # Gemini 768-dim vector

    institution = relationship("Institution", back_populates="alerts")
