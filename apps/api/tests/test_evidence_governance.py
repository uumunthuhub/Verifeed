from app.services.evidence_ranker import EvidenceRanker
from app.services.fact_check import _is_approved_review
from app.services.ingestion import _host_is_allowed


def test_content_url_must_belong_to_an_approved_https_domain():
    allowed_domains = ["macra.mw"]

    assert _host_is_allowed("https://macra.mw/public-notice/", allowed_domains)
    assert _host_is_allowed("https://www.macra.mw/public-notice/", allowed_domains)
    assert not _host_is_allowed("http://macra.mw/public-notice/", allowed_domains)
    assert not _host_is_allowed("https://macra.mw.evil.example/public-notice/", allowed_domains)


def test_fact_check_review_requires_an_approved_publisher_and_https_url():
    assert _is_approved_review("Africa Check", "https://africacheck.org/fact-check")
    assert not _is_approved_review("Unknown Checker", "https://unknown.example/check")
    assert not _is_approved_review("Africa Check", "http://africacheck.org/fact-check")


def test_ranker_uses_the_registry_trust_tier_for_indexed_evidence():
    ranking = EvidenceRanker.rank([
        {
            "title": "Official notice",
            "outlet": "MACRA",
            "url": "https://macra.mw/public-notice/",
            "type": "News Article",
            "trust_tier": 1,
        }
    ])

    assert ranking.ranked_sources[0].trust_tier == 1
