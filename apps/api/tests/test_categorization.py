"""Unit tests for headline categorization logic."""

from app.services.ingestion import CATEGORIES, categorize_headline


def test_categories_list():
    """Verify standard category list compliance."""
    expected = [
        "Politics", "Health", "Business", "Sports",
        "Regional", "Technology", "World", "Entertainment", "Other"
    ]
    assert CATEGORIES == expected


def test_keyword_categorization_politics():
    assert categorize_headline("President signs new law passed by parliament") == "Politics"
    assert categorize_headline("Election campaign spending surges ahead of vote") == "Politics"


def test_keyword_categorization_health():
    assert categorize_headline("New vaccine candidate shows promise against virus outbreak") == "Health"
    assert categorize_headline("WHO issues warning on rising hospital admissions") == "Health"


def test_keyword_categorization_business():
    assert categorize_headline("Central bank raises interest rates as stock market falls") == "Business"
    assert categorize_headline("Tech giant reports record revenue and profit") == "Business"


def test_keyword_categorization_sports():
    assert categorize_headline("National football team wins world cup match in dramatic fashion") == "Sports"
    assert categorize_headline("NBA star scores 50 points to lead team to championship") == "Sports"


def test_keyword_categorization_technology():
    assert categorize_headline("New artificial intelligence software chip announced by startup") == "Technology"
    assert categorize_headline("Smartphone manufacturer fixes critical cyber security vulnerability") == "Technology"


def test_keyword_categorization_regional():
    assert categorize_headline("Malawi government launches new development initiative in Lilongwe") == "Regional"
    assert categorize_headline("SADC summit in South Africa focuses on regional economic growth") == "Regional"


def test_keyword_categorization_entertainment():
    assert categorize_headline("Hollywood actor wins Oscar at annual movie awards ceremony") == "Entertainment"
    assert categorize_headline("Pop star releases new album ahead of summer concert tour") == "Entertainment"


def test_keyword_categorization_world():
    assert categorize_headline("UN peace summit addresses international conflict and sanctions") == "World"
    assert categorize_headline("NATO leaders meet to discuss European treaty agreements") == "World"


def test_keyword_categorization_fallback():
    # Unmatched headline without keywords should return a valid category string
    result = categorize_headline("Unusual discovery made in quiet countryside hamlet")
    assert result in CATEGORIES
