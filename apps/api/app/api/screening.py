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
