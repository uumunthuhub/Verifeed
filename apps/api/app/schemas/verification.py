"""
VeriFeed API Schemas — Verification

Pydantic models that define the API contract for verification requests
and responses. These are the canonical shapes for all data crossing
the FastAPI ↔ frontend boundary.

Verification architecture follows the evidence-first pipeline:
  Content → Entities → Channel Verification → Evidence → Gemini → Verdict
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
# Evidence source — used inside VerifyResponse
# ---------------------------------------------------------------------------

class EvidenceSourceSchema(BaseModel):
    """A single piece of cited evidence supporting or refuting the claim."""
    title: str
    outlet: str
    url: str | None = None
    type: str = Field(
        description="Evidence type: 'News Article', 'Official Institutional Alert', 'Fact Checker Rating'"
    )
    snippet: str | None = None


# ---------------------------------------------------------------------------
# Recommended action — used inside VerifyResponse
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

    Dual-verdict system per updated architecture:
    - claim_verdict: truth status of the underlying claim (True, False, Partly True, Misleading, Insufficient Evidence)
    - message_authenticity_verdict: whether the *channel/sender* is verified (Verified Official, Suspicious, etc.)
    - verdict: legacy single-label for backward compatibility
    """
    id: int
    query: str

    # Dual verdict system
    claim_verdict: str | None = Field(
        default=None,
        description="Claim truth verdict: True, False, Partly True, Misleading, Insufficient Evidence"
    )
    message_authenticity_verdict: str | None = Field(
        default=None,
        description="Channel authenticity: Verified Official, Likely Legitimate, Unverified, Suspicious, Confirmed Fraudulent"
    )

    # Legacy single verdict (backward compatibility)
    verdict: str = Field(
        description="Legacy: Confirmed Scam, Confirmed, Unconfirmed, Disputed / False, No Coverage Found"
    )

    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_level: str | None = Field(default=None, description="High, Medium, or Low")
    summary: str

    # Evidence
    sources: list[dict[str, Any]] = Field(default_factory=list)

    # Extracted entities
    extracted_sender: str | None = None
    extracted_numbers: list[str] | None = None
    extracted_urls: list[str] | None = None
    extracted_institutions: list[str] | None = None

    # Channel verification details
    verification_details: dict[str, Any] | None = None

    # User guidance
    recommended_actions: list[dict[str, Any]] | None = None

    # D2: Evidence pipeline methodology — how the verdict was reached
    methodology: str | None = Field(
        default=None,
        description="Human-readable explanation of evidence sources used and how the verdict was produced"
    )

    created_at: str


class ScamSubmissionResponse(BaseModel):
    """Response body for POST /api/v1/verify/submit-scam."""
    status: str
    message: str
    submission_id: int
    cluster_id: int | None = None
