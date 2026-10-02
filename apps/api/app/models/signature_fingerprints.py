"""
VeriFeed Signature Fingerprints Model — Phase 5

Stores perceptual hash (pHash) fingerprints for official government documents,
institutional letterheads, and known forgeries.

During verification:
  - Stage 1: When an image is uploaded, compute its pHash.
  - Stage 2: Query this table for Hamming distance <= FORGERY_THRESHOLD (10).
    * is_known_forgery=True  → fast-exit HIGH_RISK_SCAM
    * is_known_forgery=False → S_signature = 1.0 - (hamming_distance / 64)

pHash algorithm: Perceptual hash (DCT-based, 64-bit).
Hamming distance: bit-level XOR count between two 64-bit hex hashes.
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class SignatureFingerprint(Base):
    """
    A perceptual hash fingerprint for an official document or known forgery.

    Each row represents one reference image (e.g. an official RBM letterhead,
    a Ministry of Finance stamp, or a confirmed WhatsApp forgery screenshot).
    """

    __tablename__ = "signature_fingerprints"

    id = Column(Integer, primary_key=True, index=True)

    # FK to the institution that owns this official document stamp
    # Nullable — known forgeries may not map to a specific institution
    institution_id = Column(
        Integer,
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Human-readable label for this fingerprint
    document_type = Column(
        String(100),
        nullable=False,
        comment="E.g. 'RBM Official Letterhead', 'Ministry of Finance Stamp', 'Confirmed WhatsApp Forgery'",
    )

    # 64-bit perceptual hash stored as a 16-character hex string (e.g. 'a1f3c2d4b5e60781')
    # Computed by imagehash.phash(image) and cast via str(hash)
    phash_hex = Column(
        String(32),
        nullable=False,
        index=True,
        comment="64-bit pHash as hex string. Compare via Hamming distance.",
    )

    # URL of the reference document used to generate this fingerprint
    reference_source_url = Column(String(500), nullable=True)

    # True  → this hash matches a KNOWN FORGERY → fast-exit HIGH_RISK_SCAM
    # False → this hash matches an OFFICIAL DOCUMENT → S_signature bonus
    is_known_forgery = Column(Boolean, nullable=False, default=False)

    # Optional description / notes for admin reference
    notes = Column(Text, nullable=True)

    date_added = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        index=True,
    )
    added_by = Column(String(100), nullable=True, comment="Admin or pipeline that added this entry")
