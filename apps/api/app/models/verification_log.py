from typing import Any
import datetime
from typing import ClassVar

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.base import Base

# ---------------------------------------------------------------------------
# Canonical 5-label verdict system (G1 fix)
# All new code must use these constants — legacy string literals are kept
# only for backward-compat reads of old DB rows.
# ---------------------------------------------------------------------------

class CanonicalVerdict:
    VERIFIED_TRUE = "VERIFIED_TRUE"
    VERIFIED_FALSE = "VERIFIED_FALSE"
    HIGH_RISK_SCAM = "HIGH_RISK_SCAM"
    FORGED_DOCUMENT = "FORGED_DOCUMENT"
    IN_REVIEW = "IN_REVIEW"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    UNVERIFIED = "UNVERIFIED"

    ALL = frozenset([
        VERIFIED_TRUE,
        VERIFIED_FALSE,
        HIGH_RISK_SCAM,
        FORGED_DOCUMENT,
        IN_REVIEW,
        PENDING_VERIFICATION,
        UNVERIFIED,
    ])

    # Legacy → Canonical mapping (G1 fix: backward compat reads from old rows)
    LEGACY_MAP: ClassVar[dict[str, str]] = {
        "Confirmed": VERIFIED_TRUE,
        "Confirmed Scam": HIGH_RISK_SCAM,
        "Disputed": PENDING_VERIFICATION,
        "Disputed / False": VERIFIED_FALSE,
        "Unconfirmed": PENDING_VERIFICATION,
        "No Coverage Found": UNVERIFIED,
        # Dual-verdict legacy claim labels
        "True": VERIFIED_TRUE,
        "False": VERIFIED_FALSE,
        "Partly True": PENDING_VERIFICATION,
        "Misleading": PENDING_VERIFICATION,
        "Insufficient Evidence": UNVERIFIED,
    }

    @classmethod
    def from_legacy(cls, legacy: Any) -> str:
        """Map a legacy verdict string to its canonical equivalent."""
        if not legacy:
            return cls.UNVERIFIED
        val = str(legacy).strip()
        if val in cls.ALL:
            return val
        return cls.LEGACY_MAP.get(val, cls.UNVERIFIED)


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)

    # -----------------------------------------------------------------------
    # Canonical verdict (Phase 1 — G1 fix)
    # -----------------------------------------------------------------------
    canonical_verdict = Column(
        String(50),
        nullable=True,
        index=True,
        comment="One of: VERIFIED_TRUE, VERIFIED_FALSE, HIGH_RISK_SCAM, PENDING_VERIFICATION, UNVERIFIED",
    )

    # Dual verdict system (kept for backward compatibility)
    claim_verdict = Column(String(50), nullable=True, index=True)
    message_authenticity_verdict = Column(String(50), nullable=True, index=True)

    # Legacy single verdict (backward compat — do not use in new code)
    verdict = Column(String(50), nullable=False, index=True)

    confidence_score = Column(Float, default=0.0)
    risk_level = Column(String(20), nullable=True)  # High, Medium, Low

    # -----------------------------------------------------------------------
    # Weighted sub-scores (Phase 2 — G6 fix)
    # Stored as JSON: {"domain": 0.0, "vector": 0.0, "signature": 0.0, "telecom": 0.0}
    # -----------------------------------------------------------------------
    sub_scores = Column(JSON, nullable=True)

    # Extracted entities from message
    extracted_sender = Column(String(255), nullable=True)
    extracted_numbers = Column(JSON, nullable=True)
    extracted_urls = Column(JSON, nullable=True)
    extracted_institutions = Column(JSON, nullable=True)

    # Verification details
    summary = Column(Text, nullable=False)
    evidence_sources = Column(JSON, nullable=True)

    # -----------------------------------------------------------------------
    # Official sources in canonical format (Phase 1 — G3 fix)
    # Stored as JSON: [{"name": "...", "url": "..."}]
    # -----------------------------------------------------------------------
    official_sources = Column(JSON, nullable=True)

    # Official channel verification results
    sender_verified = Column(Boolean, nullable=True)
    channel_verified = Column(Boolean, nullable=True)

    # User guidance
    recommended_actions = Column(JSON, nullable=True)

    # -----------------------------------------------------------------------
    # Actionable advice — plain-language guidance for citizens (Phase 1 — G4 fix)
    # -----------------------------------------------------------------------
    actionable_advice = Column(Text, nullable=True)

    # Evidence pipeline methodology — human-readable verdict explanation
    methodology = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        index=True,
    )
