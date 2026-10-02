
from pydantic import BaseModel, Field


class EmailVerificationRequest(BaseModel):
    sender_address: str = Field(..., description="Email sender address, e.g. support@paypal-secure-verify.com")
    display_name: str | None = Field(None, description="Sender display name, e.g. PayPal Security Team")
    recipient_address: str | None = Field(None, description="Recipient email address")
    subject: str = Field("", description="Email subject line")
    body_text: str = Field(..., description="Email body content (plain text or HTML)")
    headers: str | None = Field(None, description="Optional raw email headers for SPF/DKIM inspection")


class EmailVerificationResponse(BaseModel):
    risk_level: str = Field(..., description="Low, Medium, or High risk level")
    email_authenticity_verdict: str = Field(..., description="AUTHENTIC, SPOOFED_SENDER, PHISHING_EMAIL, or SUSPICIOUS")
    domain_spoof_detected: bool = Field(False, description="True if display name impersonates a known institution on an unverified domain")
    official_domain_match: str | None = Field(None, description="Matched official domain if verified, e.g. paypal.com")
    suspicious_links: list[str] = Field(default_factory=list, description="List of flagged URLs found in body")
    detected_signals: list[str] = Field(default_factory=list, description="Heuristic phishing and spoofing signals")
    claim_verdict: str = Field("UNVERIFIED", description="Stage 2 claim verdict if deep verification was run")
    message_authenticity_verdict: str = Field("SUSPICIOUS", description="Stage 2 authenticity verdict")
    recommended_actions: list[str] = Field(default_factory=list, description="Actionable safety guidance for the user")
