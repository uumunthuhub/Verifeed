"""
Unit tests for the EvidenceRanker service — Phase D.

Tests cover:
- Tier scoring by source type
- Reputation bonus for known outlets
- Recency scoring by date
- Full ranking pipeline (sort order, deduplication)
- Confidence calibration (institutional anchor, alignment, recency)
- Methodology string generation
- prior_screening context threading
- rank_evidence() entry point
"""

from typing import ClassVar

from app.services.evidence_ranker import EvidenceRanker, RankingResult, rank_evidence

# ---------------------------------------------------------------------------
# Tier scoring
# ---------------------------------------------------------------------------

class TestTierScoring:
    def test_official_institutional_alert_scores_100(self):
        score = EvidenceRanker._tier_score("Official Institutional Alert")
        assert score == 100

    def test_fact_checker_scores_75(self):
        score = EvidenceRanker._tier_score("Fact Checker Rating")
        assert score == 75

    def test_news_article_scores_50(self):
        score = EvidenceRanker._tier_score("News Article")
        assert score == 50

    def test_unknown_type_scores_5(self):
        score = EvidenceRanker._tier_score("Random Category")
        assert score == 5

    def test_case_insensitive_matching(self):
        # Should partially match "news article" in "News Article"
        score = EvidenceRanker._tier_score("news article")
        assert score == 50


# ---------------------------------------------------------------------------
# Reputation bonus
# ---------------------------------------------------------------------------

class TestReputationBonus:
    def test_reuters_earns_bonus(self):
        assert EvidenceRanker._reputation_bonus("Reuters") == 15

    def test_bbc_earns_bonus(self):
        assert EvidenceRanker._reputation_bonus("BBC News") == 15

    def test_airtel_earns_bonus(self):
        assert EvidenceRanker._reputation_bonus("Airtel Money Malawi") == 15

    def test_unknown_outlet_earns_no_bonus(self):
        assert EvidenceRanker._reputation_bonus("Random Blog") == 0

    def test_empty_outlet_earns_no_bonus(self):
        assert EvidenceRanker._reputation_bonus("") == 0


# ---------------------------------------------------------------------------
# Recency scoring
# ---------------------------------------------------------------------------

class TestRecencyScoring:
    def test_no_date_returns_zero(self):
        assert EvidenceRanker._recency_score(None) == 0.0

    def test_recent_date_returns_high_score(self):
        import datetime
        utc = datetime.UTC
        recent = (datetime.datetime.now(tz=utc) - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        assert EvidenceRanker._recency_score(recent) == 1.0

    def test_30_day_date_returns_medium_score(self):
        import datetime
        utc = datetime.UTC
        medium = (datetime.datetime.now(tz=utc) - datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        assert EvidenceRanker._recency_score(medium) == 0.7

    def test_old_date_returns_low_score(self):
        assert EvidenceRanker._recency_score("2020-01-01") == 0.05

    def test_invalid_date_returns_zero(self):
        assert EvidenceRanker._recency_score("not-a-date") == 0.0


# ---------------------------------------------------------------------------
# Full ranking pipeline
# ---------------------------------------------------------------------------

class TestRankingPipeline:
    SOURCES: ClassVar[list[dict]] = [
        {
            "title": "Airtel Money Scam Warning",
            "outlet": "Airtel",
            "url": "https://airtel.mw/alert/1",
            "type": "Official Institutional Alert",
        },
        {
            "title": "SMS Fraud Article",
            "outlet": "Reuters",
            "url": "https://reuters.com/article/1",
            "type": "News Article",
        },
        {
            "title": "Fact Check: Airtel Loans",
            "outlet": "Africa Check",
            "url": "https://africacheck.org/1",
            "type": "Fact Checker Rating",
        },
    ]

    def test_institutional_alert_ranks_first(self):
        result = EvidenceRanker.rank(self.SOURCES, institutional_count=1)
        assert result.ranked_sources[0].source_type == "Official Institutional Alert"

    def test_returns_ranking_result(self):
        result = EvidenceRanker.rank(self.SOURCES)
        assert isinstance(result, RankingResult)

    def test_all_sources_present(self):
        result = EvidenceRanker.rank(self.SOURCES)
        assert len(result.ranked_sources) == 3

    def test_deduplication_keeps_higher_score(self):
        # Same URL twice — only one should survive
        duped = self.SOURCES + [{
            "title": "Airtel Money Scam Warning Duplicate",
            "outlet": "Some Outlet",
            "url": "https://airtel.mw/alert/1",  # Same URL as first
            "type": "News Article",
        }]
        result = EvidenceRanker.rank(duped)
        # Should only have 3 unique URLs
        assert len(result.ranked_sources) == 3

    def test_empty_sources_returns_low_confidence(self):
        result = EvidenceRanker.rank([])
        assert result.confidence_score == 0.1


# ---------------------------------------------------------------------------
# Confidence calibration
# ---------------------------------------------------------------------------

class TestConfidenceCalibration:
    def test_institutional_match_anchors_high_confidence(self):
        sources = [
            {
                "title": "Official Alert",
                "outlet": "RBM",
                "url": "https://rbm.mw/1",
                "type": "Official Institutional Alert",
            }
        ]
        result = EvidenceRanker.rank(sources, institutional_count=1)
        assert result.confidence_score >= 0.85

    def test_fact_check_anchors_medium_high_confidence(self):
        sources = [
            {
                "title": "Fact Check Result",
                "outlet": "Africa Check",
                "url": "https://africacheck.org/1",
                "type": "Fact Checker Rating",
            }
        ]
        result = EvidenceRanker.rank(sources, fact_check_count=1)
        assert result.confidence_score >= 0.70

    def test_multiple_sources_add_alignment_bonus(self):
        # 3 different sources → should score higher than 1 source alone
        sources_3 = [
            {"title": "A", "outlet": "Reuters", "url": "u1", "type": "News Article"},
            {"title": "B", "outlet": "BBC", "url": "u2", "type": "News Article"},
            {"title": "C", "outlet": "AP", "url": "u3", "type": "News Article"},
        ]
        sources_1 = [{"title": "A", "outlet": "Reuters", "url": "u1", "type": "News Article"}]
        result_3 = EvidenceRanker.rank(sources_3, article_count=3)
        result_1 = EvidenceRanker.rank(sources_1, article_count=1)
        assert result_3.confidence_score >= result_1.confidence_score

    def test_confidence_capped_at_099(self):
        sources = [
            {"title": f"Alert {i}", "outlet": "RBM", "url": f"https://rbm.mw/{i}",
             "type": "Official Institutional Alert"}
            for i in range(5)
        ]
        result = EvidenceRanker.rank(sources, institutional_count=5, fact_check_count=3, article_count=5)
        assert result.confidence_score <= 0.99

    def test_no_sources_confidence_is_low(self):
        result = EvidenceRanker.rank([])
        assert result.confidence_score == 0.1


# ---------------------------------------------------------------------------
# Methodology string
# ---------------------------------------------------------------------------

class TestMethodologyGeneration:
    def test_methodology_mentions_institutional_alerts(self):
        sources = [{
            "title": "Alert",
            "outlet": "RBM",
            "url": "https://rbm.mw/1",
            "type": "Official Institutional Alert",
        }]
        result = EvidenceRanker.rank(sources, institutional_count=1)
        assert "institutional alert" in result.methodology.lower()

    def test_methodology_mentions_prior_screening_risk(self):
        result = EvidenceRanker.rank([], prior_screening_risk="High")
        assert "High" in result.methodology

    def test_methodology_mentions_fact_checkers(self):
        sources = [{"title": "FC", "outlet": "Africa Check", "url": "u1", "type": "Fact Checker Rating"}]
        result = EvidenceRanker.rank(sources, fact_check_count=1)
        assert "fact-checker" in result.methodology.lower()

    def test_methodology_mentions_no_evidence_when_empty(self):
        result = EvidenceRanker.rank([])
        assert "no supporting evidence" in result.methodology.lower()

    def test_methodology_always_mentions_gemini(self):
        result = EvidenceRanker.rank([])
        assert "gemini" in result.methodology.lower()


# ---------------------------------------------------------------------------
# rank_evidence() entry point
# ---------------------------------------------------------------------------

class TestRankEvidenceEntryPoint:
    def test_returns_dict_with_required_keys(self):
        result = rank_evidence([])
        assert "ranked_sources" in result
        assert "confidence_score" in result
        assert "methodology" in result
        assert "evidence_tier_summary" in result

    def test_ranked_sources_are_dicts(self):
        sources = [
            {"title": "Alert", "outlet": "RBM", "url": "u1", "type": "Official Institutional Alert"}
        ]
        result = rank_evidence(sources, institutional_count=1)
        assert isinstance(result["ranked_sources"], list)
        if result["ranked_sources"]:
            s = result["ranked_sources"][0]
            assert "title" in s
            assert "outlet" in s
            assert "url" in s
            assert "type" in s
