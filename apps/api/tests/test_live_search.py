"""Unit tests for live_search service."""

import xml.etree.ElementTree as ET
from app.services.live_search import (
    _safe_get_text,
    extract_search_keywords,
    is_article_relevant,
    search_live_web_news,
)


def test_safe_get_text_handles_none_text():
    """Verify _safe_get_text returns default when element text is None or missing."""
    xml_str = "<item><title/><source url='http://example.com'/><link>http://link.com</link></item>"
    item = ET.fromstring(xml_str)

    assert _safe_get_text(item, "title", "Default Title") == "Default Title"
    assert _safe_get_text(item, "source", "Live News Media") == "Live News Media"
    assert _safe_get_text(item, "link") == "http://link.com"
    assert _safe_get_text(item, "nonexistent", "Fallback") == "Fallback"


def test_extract_search_keywords_preserves_acronyms_and_hyphens():
    """Verify extract_search_keywords keeps short terms like e-id, id, ai, tv."""
    kw = extract_search_keywords("does malawi offer e Id FOR CITIZENS?")
    assert "id" in kw.lower() or "e" in kw.lower()

    kw_lion = extract_search_keywords("is there a loose escaped lion in malawi zoo?")
    assert "lion" in kw_lion.lower()
    assert "escaped" in kw_lion.lower()
    assert "zoo" in kw_lion.lower()


def test_is_article_relevant_filters_out_unrelated_news():
    """Verify is_article_relevant filters out bank scams and unrelated news for specific claims."""
    # Bank scam alert should NOT be relevant to e-ID or escaped lion queries
    query_eid = "does malawi offer e Id FOR CITIZENS?"
    bank_alert = "FRAUD WARNING: Fake Mo626 Digital App Upgrades"
    assert not is_article_relevant(query_eid, bank_alert)

    query_lion = "is there a loose/escaped lion in malawi zoo"
    unrelated_news = "US demands $15,000 deposit for visa applicants from Malawi"
    assert not is_article_relevant(query_lion, unrelated_news)

    # Subject relevant news SHOULD pass
    relevant_lion_news = "Escaped Lion Recaptured near Kasungu Game Reserve"
    assert is_article_relevant(query_lion, relevant_lion_news)


def test_search_live_web_news_returns_list():
    """Verify search_live_web_news handles valid queries without crashing."""
    results = search_live_web_news("lion escaped game reserve")
    assert isinstance(results, list)

