"""
VeriFeed API Schemas — Verification

Pydantic models defining the API contract for verification requests
and responses. These are the canonical shapes for all data crossing
the FastAPI ↔ frontend boundary.

Phase 1 changes (G1, G3, G4 fixes):
  - OfficialSource: canonical {name, url} format (replaces {title, outlet, url, type})
  - SubScores: 4-component weighted confidence sub-scores
  - VerifyResponse: adds canonical_verdict, official_sources, actionable_advice, sub_scores
"""

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class VerifyRequest(BaseModel):
    """Request body for POST /api/v1/verify."""
    query: str | None = Field(default="", description="Claim text, message, or URL to verify")
    image_data: str | None = Field(default=None, description="Base64-encoded image for OCR extraction")
    file_name: str | None = Field(default=None, description="Original filename of the uploaded file")


class ScamSubmissionRequest(BaseModel):
    """Request body for POST /api/v1/verify/submit-scam."""
    text: str | None = Field(default="", description="Raw text of the suspicious message")
    image_data: str | None = Field(default=None, description="Base64-encoded screenshot")


# ---------------------------------------------------------------------------
# OfficialSource — canonical format (G3 fix)
# Replaces the old {title, outlet, url, type} format.
# ---------------------------------------------------------------------------

class OfficialSource(BaseModel):
    """
    A single official grounding source supporting or refuting the claim.

    Format per system_documentation.md: {name, url}
    Rendered in the UI as a clickable link: <a href={url}>{name}</a>
    """
    name: str = Field(description="Human-readable source name, e.g. 'Reserve Bank of Malawi'")
    url: str | None = Field(default=None, description="Direct URL to the source document or page")


# ---------------------------------------------------------------------------
# SubScores — 4-component weighted confidence (G6 fix)
# ---------------------------------------------------------------------------

class SubScores(BaseModel):
    """
    4-component weighted confidence sub-scores.

    S_total = 0.35*domain + 0.35*vector + 0.20*signature + 0.10*telecom
    """
    domain: float = Field(
        ge=0.0, le=1.0,
        description="Source domain trust score: Tier1=1.0, Tier2=0.85, Tier3=0.5, Tier4=0.2"
    )
    vector: float = Field(
        ge=0.0, le=1.0,
        description="Vector cosine similarity score of top evidence match"
    )
    signature: float = Field(
        ge=0.0, le=1.0,
        description="pHash stamp/signature forensic score: 1.0 - (hamming_distance/64)"
    )
    telecom: float = Field(
        ge=0.0, le=1.0,
        description="Telecom sender ID registry score: 1.0=officially registered, 0.0=unverified"
    )


# ---------------------------------------------------------------------------
# Recommended action — kept for legacy pipeline compatibility
# ---------------------------------------------------------------------------

class RecommendedAction(BaseModel):
    """A user-facing action recommended based on the verification result."""
    action: str
    priority: str = Field(description="One of: 'critical', 'high', 'medium', 'low'")
    reason: str | None = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class VerifyResponse(BaseModel):
    """
    Response body for POST /api/v1/verify.

    Phase 1 additions:
      canonical_verdict: one of the 5 canonical labels (G1 fix)
      official_sources: [{name, url}] format (G3 fix)
      actionable_advice: plain-language guidance for citizens (G4 fix)
      sub_scores: 4-component weighted sub-scores (G6 fix)
    """
    id: int
    query: str

    # -----------------------------------------------------------------------
    # Canonical verdict — primary field for all new UI and API consumers (G1)
    # -----------------------------------------------------------------------
    canonical_verdict: str | None = Field(
        default=None,
        description=(
            "Canonical verdict: one of VERIFIED_TRUE | VERIFIED_FALSE | "
            "HIGH_RISK_SCAM | PENDING_VERIFICATION | UNVERIFIED"
        ),
    )

    # Legacy dual-verdict system (kept for backward compat)
    claim_verdict: str | None = Field(
        default=None,
        description="Legacy claim truth verdict"
    )
    message_authenticity_verdict: str | None = Field(
        default=None,
        description="Legacy channel authenticity verdict"
    )

    # Legacy single verdict (backward compat — do not use in new frontend code)
    verdict: str = Field(
        description="Legacy: Confirmed Scam / Confirmed / Unconfirmed / Disputed / No Coverage Found"
    )

    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_level: str | None = Field(default=None, description="High, Medium, or Low")
    summary: str

    # -----------------------------------------------------------------------
    # Weighted sub-scores (G6 fix) — shown in Forensic Inspector UI
    # -----------------------------------------------------------------------
    sub_scores: SubScores | None = Field(
        default=None,
        description="4-component weighted confidence sub-scores"
    )

    # -----------------------------------------------------------------------
    # Official grounding sources in canonical format (G3 fix)
    # -----------------------------------------------------------------------
    official_sources: list[OfficialSource] = Field(
        default_factory=list,
        description="Tier 1 & Tier 2 official sources in canonical [{name, url}] format"
    )

    # Legacy sources field (backward compat — do not use in new frontend code)
    sources: list[dict[str, Any]] = Field(default_factory=list)

    # -----------------------------------------------------------------------
    # Actionable advice — must be displayed prominently in UI (G4 fix)
    # -----------------------------------------------------------------------
    actionable_advice: str | None = Field(
        default=None,
        description="Plain-language guidance for Malawian citizens on what to do next"
    )

    # Extracted entities
    extracted_sender: str | None = None
    extracted_numbers: list[str] | None = None
    extracted_urls: list[str] | None = None
    extracted_institutions: list[str] | None = None

    # Channel verification details
    verification_details: dict[str, Any] | None = None

    # User guidance (legacy)
    recommended_actions: list[dict[str, Any]] | None = None

    # Evidence pipeline methodology
    methodology: str | None = Field(
        default=None,
        description="Human-readable explanation of how the verdict was produced"
    )

    created_at: str


class ScamSubmissionResponse(BaseModel):
    """Response body for POST /api/v1/verify/submit-scam."""
    status: str
    message: str
    submission_id: int
    cluster_id: int | None = None
