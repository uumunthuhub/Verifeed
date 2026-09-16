"""
VeriFeed API Schemas — Fraud Intelligence

Pydantic models for the fraud intelligence domain:
  FraudSignal, SubmissionRequest, SubmissionResponse, EmergingPatternResponse

These shape the API contract for scam reporting, local screening results,
and submission cluster surfacing.

Verdict trust boundary (per architecture rules):
  LOCAL SIGNALS ≠ VERIFIED EVIDENCE ≠ GEMINI ANALYSIS ≠ FINAL VERDICT
"""

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

class SubmissionRequest(BaseModel):
    """Request body for submitting a suspicious message for community tracking."""
    text: str | None = Field(default="", description="Raw message text (SMS, email body, forwarded post)")
    image_data: str | None = Field(default=None, description="Base64-encoded screenshot of the suspicious content")


class SubmissionResponse(BaseModel):
    """Response returned after a user submits a suspicious message."""
    status: str
    message: str
    submission_id: int
    cluster_id: int | None = None


# ---------------------------------------------------------------------------
# Fraud signal — Stage 1 local screening result
# ---------------------------------------------------------------------------

class FraudSignalSchema(BaseModel):
    """
    A single detected risk indicator from the local screening engine.
    These are deterministic rule/pattern matches — not AI verdicts.
    """
    signal_type: str = Field(
        description="Category of signal: 'urgency_language', 'suspicious_url', "
                    "'known_scam_number', 'impersonation_keyword', 'monetary_request', "
                    "'unsolicited_prize'"
    )
    description: str = Field(description="Human-readable explanation of the detected signal")
    matched_text: str | None = Field(default=None, description="The specific text that triggered this signal")
    severity: str = Field(
        default="medium",
        description="Signal severity: 'low', 'medium', 'high'"
    )


# ---------------------------------------------------------------------------
# Stage 1 screening response
# ---------------------------------------------------------------------------

class ScreeningRequest(BaseModel):
    """Request body for POST /api/v1/screen (Stage 1 — local, no Gemini)."""
    content: str = Field(description="The message, URL, or notification text to screen")
    content_type: str = Field(
        default="message",
        description="Type of content: 'message', 'url', 'email', 'notification'"
    )


class ScreeningResponse(BaseModel):
    """
    Response from Stage 1 local screening.

    This is intentionally lightweight — no Gemini call, near-instant response.
    The risk_level here is based on deterministic signals only.
    For a full evidence-backed verdict, the client should follow up with
    POST /api/v1/verify (Stage 2).
    """
    risk_level: str = Field(description="Overall risk estimate: 'Low', 'Medium', 'High'")
    signals: list[FraudSignalSchema] = Field(
        default_factory=list,
        description="List of specific risk signals detected"
    )
    pattern_matches: list[str] = Field(
        default_factory=list,
        description="Known scam pattern names that matched"
    )
    needs_deep_verify: bool = Field(
        description="Whether Stage 2 deep verification is recommended"
    )
    recommended_action: str = Field(
        description="Short actionable guidance (e.g. 'Verify with VeriFeed before acting')"
    )
    screened_urls: list[str] = Field(
        default_factory=list,
        description="URLs extracted and screened from the content"
    )
    detected_institutions: list[str] = Field(
        default_factory=list,
        description="Institution names detected in the content (not verified — for display only)"
    )


# ---------------------------------------------------------------------------
# Emerging pattern — surfaced from submission clustering
# ---------------------------------------------------------------------------

class EmergingPatternResponse(BaseModel):
    """
    A cluster of similar user-submitted suspicious messages.
    Labeled as 'emerging' — NOT a confirmed scam without institutional backing.
    """
    cluster_id: int
    status: str = Field(
        description="Pattern status: 'unconfirmed', 'emerging', 'confirmed_scam', 'confirmed_legitimate'"
    )
    representative_text: str
    submission_count: int
    first_seen: str
    last_seen: str | None = None
