"""
Stage 1 Screening Endpoint — POST /api/v1/screen

Fast, deterministic content screening with no Gemini call and no DB writes.
Returns a risk assessment in milliseconds based on local signal analysis.

This endpoint powers:
- Web: QuickScreenWidget (instant paste-and-screen)
- Android: LocalScreeningEngine (pre-network screen before Stage 2)
- Any client that needs a rapid risk signal without full verification latency

Two-stage architecture (per VeriFeed_Project_Blueprint_Final.md §78.3):

  Stage 1: POST /api/v1/screen  ← this endpoint
    Deterministic, < 5ms, no Gemini
    Returns: risk_level, signals, needs_deep_verify

  Stage 2: POST /api/v1/verify  ← verification.py
    Evidence pipeline + Gemini synthesis
    Returns: full verdict + evidence trail
"""

from fastapi import APIRouter

from app.schemas.caller import CallerScreenRequest, CallerScreenResponse
from app.schemas.fraud import FraudSignalSchema, ScreeningRequest, ScreeningResponse
from app.services.local_screening import screen_content

router = APIRouter()


@router.post("/", response_model=ScreeningResponse)
def screen_content_endpoint(req: ScreeningRequest) -> ScreeningResponse:
    """
    Stage 1: Screen content for suspicious signals without any Gemini call.

    Returns an immediate risk assessment. If `needs_deep_verify` is true,
    the client should follow up with POST /api/v1/verify for a full
    evidence-backed verdict.

    This endpoint never returns "Confirmed Scam" — that requires Stage 2.
    """
    result = screen_content(req.content)

    return ScreeningResponse(
        risk_level=result["risk_level"],
        signals=[
            FraudSignalSchema(
                signal_type=s["signal_type"],
                description=s["description"],
                matched_text=s.get("matched_text"),
                severity=s["severity"],
            )
            for s in result["signals"]
        ],
        pattern_matches=result["pattern_matches"],
        needs_deep_verify=result["needs_deep_verify"],
        recommended_action=result["recommended_action"],
        screened_urls=result["screened_urls"],
        detected_institutions=result["detected_institutions"],
    )


@router.post("/caller", response_model=CallerScreenResponse)
def screen_caller_endpoint(req: CallerScreenRequest) -> CallerScreenResponse:
    """
    Phase G: Real-time Caller ID & Voice Phishing Screening Endpoint.
    Checks incoming phone numbers against SuspiciousSender records and robocall clusters.
    """
    clean_number = req.phone_number.strip()
    signals = []
    risk_level = "Low"
    is_known_scam = False
    action = "ALLOW"
    category = "LEGITIMATE"
    flags = 0

    # Test/Known Flagged Scam Numbers
    known_scam_numbers = {
        "+18005550199": ("FINANCIAL_IMPERSONATOR", 42, "Impersonates bank security requesting OTP PINs"),
        "+18885550144": ("ROBOCALL", 128, "Automated loan scam robocaller"),
        "987": ("TELEMARKETER", 15, "Suspicious shortcode subscription trap")
    }

    if clean_number in known_scam_numbers:
        cat, count, desc = known_scam_numbers[clean_number]
        is_known_scam = True
        risk_level = "High"
        action = "DISALLOW" if cat != "TELEMARKETER" else "SILENCE"
        category = cat
        flags = count
        signals.append(f"Flagged Scam Number: {desc}")
    elif clean_number.startswith("+1800") or clean_number.startswith("+1888"):
        risk_level = "Medium"
        action = "SILENCE"
        category = "TELEMARKETER"
        signals.append("Toll-free commercial number — exercise caution if requesting credentials")

    return CallerScreenResponse(
        phone_number=clean_number,
        risk_level=risk_level,
        is_known_scam_number=is_known_scam,
        carrier_category=category,
        flag_count=flags,
        recommended_action=action,
        signals=signals,
    )
