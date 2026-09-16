"""
Unit tests for the channel verification service.

Tests phone normalization, sender ID matching, short code matching,
USSD code matching, URL domain matching, and the full verify_channels
pipeline using mock Institution objects (no real DB required).
"""

from unittest.mock import MagicMock

from app.services.channel_verification import (
    ChannelVerifier,
    verify_official_channels,
)

# ---------------------------------------------------------------------------
# Helpers — mock Institution object
# ---------------------------------------------------------------------------

def make_institution(
    name: str = "Test Bank",
    sector: str = "Banking",
    website_url: str = "https://testbank.co.mw",
    official_phone_numbers: list[str] | None = None,
    official_sms_sender_ids: list[str] | None = None,
    official_short_codes: list[str] | None = None,
    official_ussd_codes: list[str] | None = None,
    official_email_domains: list[str] | None = None,
) -> MagicMock:
    inst = MagicMock()
    inst.name = name
    inst.sector = sector
    inst.website_url = website_url
    inst.official_phone_numbers = official_phone_numbers or []
    inst.official_sms_sender_ids = official_sms_sender_ids or []
    inst.official_short_codes = official_short_codes or []
    inst.official_ussd_codes = official_ussd_codes or []
    inst.official_email_domains = official_email_domains or []
    return inst


# ---------------------------------------------------------------------------
# Phone number normalisation
# ---------------------------------------------------------------------------

class TestPhoneNormalization:
    def test_zero_prefix_becomes_plus_265(self):
        assert ChannelVerifier.normalize_phone_number("0999000212") == "+265999000212"

    def test_plus_265_format_normalized(self):
        assert ChannelVerifier.normalize_phone_number("+265 999-000-212") == "+265999000212"

    def test_already_normalized_unchanged(self):
        assert ChannelVerifier.normalize_phone_number("+265991234567") == "+265991234567"

    def test_bare_digits_get_country_code(self):
        result = ChannelVerifier.normalize_phone_number("991234567")
        assert result.startswith("+265")


# ---------------------------------------------------------------------------
# Sender ID normalization
# ---------------------------------------------------------------------------

class TestSenderNormalization:
    def test_uppercases_sender(self):
        assert ChannelVerifier.normalize_sender_id("airtelmw") == "AIRTELMW"

    def test_strips_whitespace(self):
        assert ChannelVerifier.normalize_sender_id("  STDBANK  ") == "STDBANK"


# ---------------------------------------------------------------------------
# Phone number verification
# ---------------------------------------------------------------------------

class TestPhoneVerification:
    def test_matching_phone_returns_true(self):
        inst = make_institution(official_phone_numbers=["+265991234567"])
        assert ChannelVerifier.verify_phone_number("0991234567", inst) is True

    def test_non_matching_phone_returns_false(self):
        inst = make_institution(official_phone_numbers=["+265991234567"])
        assert ChannelVerifier.verify_phone_number("0991111111", inst) is False

    def test_empty_official_numbers_returns_false(self):
        inst = make_institution(official_phone_numbers=[])
        assert ChannelVerifier.verify_phone_number("0991234567", inst) is False

    def test_none_official_numbers_returns_false(self):
        inst = make_institution()
        inst.official_phone_numbers = None
        assert ChannelVerifier.verify_phone_number("0991234567", inst) is False


# ---------------------------------------------------------------------------
# Sender ID verification
# ---------------------------------------------------------------------------

class TestSenderIdVerification:
    def test_matching_sender_returns_true(self):
        inst = make_institution(official_sms_sender_ids=["AIRTELMW"])
        assert ChannelVerifier.verify_sender_id("airtelmw", inst) is True

    def test_non_matching_sender_returns_false(self):
        inst = make_institution(official_sms_sender_ids=["AIRTELMW"])
        assert ChannelVerifier.verify_sender_id("FAKESENDER", inst) is False

    def test_empty_sender_ids_returns_false(self):
        inst = make_institution(official_sms_sender_ids=[])
        assert ChannelVerifier.verify_sender_id("AIRTELMW", inst) is False


# ---------------------------------------------------------------------------
# Short code verification
# ---------------------------------------------------------------------------

class TestShortCodeVerification:
    def test_matching_short_code_returns_true(self):
        inst = make_institution(official_short_codes=["212"])
        assert ChannelVerifier.verify_short_code("212", inst) is True

    def test_non_matching_short_code_returns_false(self):
        inst = make_institution(official_short_codes=["212"])
        assert ChannelVerifier.verify_short_code("999", inst) is False


# ---------------------------------------------------------------------------
# USSD code verification
# ---------------------------------------------------------------------------

class TestUssdCodeVerification:
    def test_matching_ussd_returns_true(self):
        inst = make_institution(official_ussd_codes=["*212#"])
        assert ChannelVerifier.verify_ussd_code("*212#", inst) is True

    def test_non_matching_ussd_returns_false(self):
        inst = make_institution(official_ussd_codes=["*212#"])
        assert ChannelVerifier.verify_ussd_code("*999#", inst) is False


# ---------------------------------------------------------------------------
# URL domain verification
# ---------------------------------------------------------------------------

class TestUrlDomainVerification:
    def test_matching_domain_returns_true(self):
        inst = make_institution(official_email_domains=["standardbank.co.mw"])
        assert ChannelVerifier.verify_url_domain("https://standardbank.co.mw/verify", inst) is True

    def test_non_matching_domain_returns_false(self):
        inst = make_institution(official_email_domains=["standardbank.co.mw"])
        assert ChannelVerifier.verify_url_domain("http://bit.ly/fake", inst) is False

    def test_empty_domains_returns_false(self):
        inst = make_institution(official_email_domains=[])
        assert ChannelVerifier.verify_url_domain("https://standardbank.co.mw/", inst) is False


# ---------------------------------------------------------------------------
# Full pipeline — verify_channels
# ---------------------------------------------------------------------------

class TestVerifyChannelsPipeline:
    def _make_db_with_institution(self, institution: MagicMock) -> MagicMock:
        """Return a mock DB session whose query returns the given institution."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [institution]
        mock_db = MagicMock()
        mock_db.query.return_value = mock_query
        return mock_db

    def test_no_institution_names_returns_unverified(self):
        entities = {"institution_names": [], "sender": None, "phone_numbers": [], "urls": []}
        mock_db = MagicMock()
        result = ChannelVerifier.verify_channels(entities, mock_db)
        assert result.sender_verified is False
        assert result.channel_verified is False
        assert result.matched_institution is None

    def test_matching_sender_id_marks_sender_verified(self):
        inst = make_institution(
            name="Airtel Money",
            official_sms_sender_ids=["AIRTELMW"],
        )
        mock_db = self._make_db_with_institution(inst)
        entities = {
            "institution_names": ["Airtel Money"],
            "sender": "AIRTELMW",
            "phone_numbers": [],
            "urls": [],
            "short_codes": [],
            "ussd_codes": [],
        }
        result = ChannelVerifier.verify_channels(entities, mock_db)
        assert result.sender_verified is True
        assert result.matched_institution == "Airtel Money"

    def test_matching_phone_marks_channel_verified(self):
        inst = make_institution(
            name="Standard Bank",
            official_phone_numbers=["+265991111222"],
        )
        mock_db = self._make_db_with_institution(inst)
        entities = {
            "institution_names": ["Standard Bank"],
            "sender": None,
            "phone_numbers": ["0991111222"],
            "urls": [],
            "short_codes": [],
            "ussd_codes": [],
        }
        result = ChannelVerifier.verify_channels(entities, mock_db)
        assert result.channel_verified is True

    def test_no_matching_channels_leaves_unverified(self):
        inst = make_institution(
            name="RBM",
            official_phone_numbers=["+265888000000"],
        )
        mock_db = self._make_db_with_institution(inst)
        entities = {
            "institution_names": ["RBM"],
            "sender": None,
            "phone_numbers": ["0999999999"],  # different number
            "urls": [],
            "short_codes": [],
            "ussd_codes": [],
        }
        result = ChannelVerifier.verify_channels(entities, mock_db)
        assert result.channel_verified is False
        assert result.sender_verified is False


# ---------------------------------------------------------------------------
# verify_official_channels entry point
# ---------------------------------------------------------------------------

class TestVerifyOfficialChannelsEntryPoint:
    def test_returns_dict_with_required_keys(self):
        entities = {"institution_names": [], "sender": None, "phone_numbers": [], "urls": []}
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = verify_official_channels(entities, mock_db)
        assert "sender_verified" in result
        assert "channel_verified" in result
        assert "matched_institution" in result
        assert "matched_channels" in result
        assert "verification_details" in result

    def test_sender_verified_false_by_default_for_empty_input(self):
        entities = {"institution_names": [], "sender": None, "phone_numbers": [], "urls": []}
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = verify_official_channels(entities, mock_db)
        assert result["sender_verified"] is False
        assert result["channel_verified"] is False
