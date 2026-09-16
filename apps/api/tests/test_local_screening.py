"""
Unit tests for the Stage 1 local screening engine.

Tests cover:
- URL screening (shortened URLs, typosquat patterns)
- Phrase screening (urgency, monetary requests, unsolicited prizes)
- Institution detection
- Sender screening
- Risk level computation
- Full screen() pipeline
- screen_content() entry point
- ScreeningResponse via FastAPI TestClient
"""

from fastapi.testclient import TestClient

from app.main import app
from app.services.local_screening import (
    LocalScreeningEngine,
    ScreeningResult,
    screen_content,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# URL screening
# ---------------------------------------------------------------------------

class TestUrlScreening:
    def test_detects_bitly_url(self):
        text = "Claim your prize at http://bit.ly/win-now"
        urls, signals = LocalScreeningEngine.screen_urls(text)
        assert "http://bit.ly/win-now" in urls
        assert any(s.signal_type == "suspicious_url" for s in signals)

    def test_detects_tinyurl(self):
        text = "Visit https://tinyurl.com/fakeclaim for details"
        _, signals = LocalScreeningEngine.screen_urls(text)
        assert any(s.signal_type == "suspicious_url" for s in signals)

    def test_detects_airtel_typosquat(self):
        text = "Go to https://airtel-mw.promo/bonus to activate"
        _, signals = LocalScreeningEngine.screen_urls(text)
        assert any(s.signal_type == "suspicious_url" for s in signals)

    def test_clean_url_no_signal(self):
        text = "Visit https://airtelmalawi.com for official services"
        _, signals = LocalScreeningEngine.screen_urls(text)
        assert len(signals) == 0

    def test_no_url_returns_empty(self):
        text = "This message has no links whatsoever."
        urls, signals = LocalScreeningEngine.screen_urls(text)
        assert urls == []
        assert signals == []

    def test_suspicious_url_severity_is_high(self):
        text = "Click http://bit.ly/scam-link now"
        _, signals = LocalScreeningEngine.screen_urls(text)
        assert all(s.severity == "high" for s in signals)


# ---------------------------------------------------------------------------
# Phrase screening
# ---------------------------------------------------------------------------

class TestPhraseScreening:
    def test_detects_urgency_language(self):
        text = "Act now! This offer expires today. Do not delay."
        signals = LocalScreeningEngine.screen_phrases(text)
        assert any(s.signal_type == "urgency_language" for s in signals)

    def test_detects_monetary_request(self):
        text = "Please send money via Airtel Money transfer to activate."
        signals = LocalScreeningEngine.screen_phrases(text)
        assert any(s.signal_type == "monetary_request" for s in signals)

    def test_detects_unsolicited_prize(self):
        text = "Congratulations! You have won MK500,000. Claim your prize now."
        signals = LocalScreeningEngine.screen_phrases(text)
        assert any(s.signal_type == "unsolicited_prize" for s in signals)

    def test_clean_message_no_signals(self):
        text = "Your Airtel recharge of MK1,000 was successful. Thank you."
        signals = LocalScreeningEngine.screen_phrases(text)
        assert len(signals) == 0

    def test_monetary_request_severity_is_high(self):
        text = "Transfer funds to this account to proceed."
        signals = LocalScreeningEngine.screen_phrases(text)
        monetary = [s for s in signals if s.signal_type == "monetary_request"]
        assert all(s.severity == "high" for s in monetary)


# ---------------------------------------------------------------------------
# Institution detection
# ---------------------------------------------------------------------------

class TestInstitutionDetection:
    def test_detects_airtel_money(self):
        text = "Airtel Money is calling you."
        institutions = LocalScreeningEngine.detect_institutions(text)
        assert "airtel money" in institutions

    def test_detects_standard_bank(self):
        text = "Standard Bank has credited your account."
        institutions = LocalScreeningEngine.detect_institutions(text)
        assert "standard bank" in institutions

    def test_detects_rbm(self):
        text = "RBM has approved your emergency fund."
        institutions = LocalScreeningEngine.detect_institutions(text)
        assert "rbm" in institutions

    def test_no_institution_returns_empty(self):
        text = "Your order has been dispatched."
        institutions = LocalScreeningEngine.detect_institutions(text)
        assert institutions == []


# ---------------------------------------------------------------------------
# Sender screening
# ---------------------------------------------------------------------------

class TestSenderScreening:
    def test_none_sender_returns_empty(self):
        signals = LocalScreeningEngine.screen_sender(None)
        assert signals == []

    def test_us_number_flagged(self):
        signals = LocalScreeningEngine.screen_sender("+12025551234")
        assert any(s.signal_type == "suspicious_sender" for s in signals)

    def test_local_malawi_number_not_flagged(self):
        # +265 9-digit number is not in the suspicious pattern list
        signals = LocalScreeningEngine.screen_sender("+265991234567")
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# Risk level computation
# ---------------------------------------------------------------------------

class TestRiskLevelComputation:
    def test_no_signals_is_low(self):
        assert LocalScreeningEngine._compute_risk_level([]) == "Low"

    def test_one_high_signal_is_medium(self):
        from app.services.local_screening import DetectedSignal
        signals = [DetectedSignal("suspicious_url", "desc", severity="high")]
        assert LocalScreeningEngine._compute_risk_level(signals) == "Medium"

    def test_two_high_signals_is_high(self):
        from app.services.local_screening import DetectedSignal
        signals = [
            DetectedSignal("suspicious_url", "desc", severity="high"),
            DetectedSignal("monetary_request", "desc", severity="high"),
        ]
        assert LocalScreeningEngine._compute_risk_level(signals) == "High"

    def test_four_any_signals_is_high(self):
        from app.services.local_screening import DetectedSignal
        signals = [DetectedSignal("urgency_language", "d", severity="medium")] * 4
        assert LocalScreeningEngine._compute_risk_level(signals) == "High"


# ---------------------------------------------------------------------------
# Full screen() pipeline
# ---------------------------------------------------------------------------

class TestScreenPipeline:
    def test_high_risk_scam_message(self):
        text = (
            "URGENT: Standard Bank has suspended your account. "
            "Send money via Airtel Money transfer to reactivate. "
            "Click http://bit.ly/stdbank-verify immediately."
        )
        result = LocalScreeningEngine.screen(text)
        assert isinstance(result, ScreeningResult)
        assert result.risk_level == "High"
        assert result.needs_deep_verify is True
        assert len(result.signals) > 0

    def test_clean_message_is_low_risk(self):
        text = "Your electricity bill of MK8,500 is due on 30 September 2026."
        result = LocalScreeningEngine.screen(text)
        assert result.risk_level == "Low"
        assert result.needs_deep_verify is False

    def test_prize_message_flags_correctly(self):
        text = "Congratulations! You have won a free iPhone. Claim your prize now!"
        result = LocalScreeningEngine.screen(text)
        assert result.risk_level in ("Medium", "High")
        assert result.needs_deep_verify is True

    def test_result_contains_all_required_fields(self):
        result = LocalScreeningEngine.screen("Some message content")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "signals")
        assert hasattr(result, "pattern_matches")
        assert hasattr(result, "needs_deep_verify")
        assert hasattr(result, "recommended_action")
        assert hasattr(result, "screened_urls")
        assert hasattr(result, "detected_institutions")


# ---------------------------------------------------------------------------
# screen_content() entry point
# ---------------------------------------------------------------------------

class TestScreenContentEntryPoint:
    def test_returns_dict_with_required_keys(self):
        result = screen_content("Some message text")
        assert "risk_level" in result
        assert "signals" in result
        assert "pattern_matches" in result
        assert "needs_deep_verify" in result
        assert "recommended_action" in result
        assert "screened_urls" in result
        assert "detected_institutions" in result

    def test_high_risk_message_flagged(self):
        text = "Act now! Transfer MK50,000 to 0999123456. Click http://bit.ly/fake"
        result = screen_content(text)
        assert result["risk_level"] in ("Medium", "High")
        assert result["needs_deep_verify"] is True


# ---------------------------------------------------------------------------
# API endpoint — POST /api/v1/screen
# ---------------------------------------------------------------------------

class TestScreeningEndpoint:
    def test_endpoint_returns_200_for_valid_request(self):
        response = client.post(
            "/api/v1/screen/",
            json={"content": "Hello, your account has been credited.", "content_type": "message"},
        )
        assert response.status_code == 200

    def test_endpoint_response_has_required_fields(self):
        response = client.post(
            "/api/v1/screen/",
            json={"content": "Test message", "content_type": "message"},
        )
        data = response.json()
        assert "risk_level" in data
        assert "signals" in data
        assert "needs_deep_verify" in data
        assert "recommended_action" in data

    def test_endpoint_flags_suspicious_message(self):
        response = client.post(
            "/api/v1/screen/",
            json={
                "content": "URGENT: Send money now! Click http://bit.ly/scam to claim prize.",
                "content_type": "message",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ("Medium", "High")
        assert data["needs_deep_verify"] is True

    def test_endpoint_returns_low_risk_for_clean_content(self):
        response = client.post(
            "/api/v1/screen/",
            json={"content": "Your appointment is confirmed for tomorrow at 10am.", "content_type": "message"},
        )
        data = response.json()
        assert data["risk_level"] == "Low"
        assert data["needs_deep_verify"] is False

    def test_endpoint_signals_list_has_correct_structure(self):
        response = client.post(
            "/api/v1/screen/",
            json={"content": "Act now! Transfer funds immediately.", "content_type": "message"},
        )
        data = response.json()
        if data["signals"]:
            signal = data["signals"][0]
            assert "signal_type" in signal
            assert "description" in signal
            assert "severity" in signal
