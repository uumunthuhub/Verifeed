"""Unit tests for the RAG verification agent services."""

from app.services.channel_verification import ChannelVerifier
from app.services.entity_extraction import extract_entities_from_text
from app.services.verification_agent import (
    VERDICT_TYPES,
    extract_significant_keywords,
)


def test_verdict_types_definition():
    """Ensure all required verdict labels are present per AGENT_Final.md and Blueprint."""
    expected_verdicts = [
        "Confirmed Scam",
        "Confirmed",
        "Unconfirmed",
        "Disputed / False",
        "No Coverage Found",
    ]
    assert VERDICT_TYPES == expected_verdicts


def test_extract_significant_keywords():
    """Verify keyword extraction filters out short words and stopwords."""
    text = "Free loan offer from Airtel Money with no collateral required"
    keywords = extract_significant_keywords(text)
    assert "airtel" in keywords
    assert "money" in keywords
    assert "collateral" in keywords
    assert "required" in keywords
    # Stopwords and short words should be excluded
    assert "with" not in keywords
    assert "from" not in keywords
    assert "free" not in keywords


def test_entity_extraction_short_codes_and_ussd():
    """Verify extraction of short codes (*212#) and official USSD patterns."""
    text = "Airtel Money official service code is 212 or dial *212# or *211# for help"
    entities = extract_entities_from_text(text)
    assert "212" in entities["short_codes"]
    assert "*212#" in entities["ussd_codes"]
    assert "airtel money" in [i.lower() for i in entities["institution_names"]]


def test_channel_verifier_phone_normalization():
    """Verify phone number normalization for official institutional comparison."""
    norm1 = ChannelVerifier.normalize_phone_number("0999000212")
    norm2 = ChannelVerifier.normalize_phone_number("+265 999-000-212")
    assert norm1 == "+265999000212"
    assert norm2 == "+265999000212"
    assert norm1 == norm2

