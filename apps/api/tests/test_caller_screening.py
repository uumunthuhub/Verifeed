import pytest
from app.api.screening import screen_caller_endpoint
from app.schemas.caller import CallerScreenRequest


def test_caller_screening_scam_number():
    req = CallerScreenRequest(phone_number="+18005550199")
    res = screen_caller_endpoint(req)
    assert res.risk_level == "High"
    assert res.is_known_scam_number is True
    assert res.recommended_action == "DISALLOW"
    assert res.carrier_category == "FINANCIAL_IMPERSONATOR"


def test_caller_screening_legitimate_number():
    req = CallerScreenRequest(phone_number="+14155552671")
    res = screen_caller_endpoint(req)
    assert res.risk_level == "Low"
    assert res.is_known_scam_number is False
    assert res.recommended_action == "ALLOW"
