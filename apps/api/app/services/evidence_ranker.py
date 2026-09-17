"""
VeriFeed Evidence Ranker — Phase D

Ranks and scores evidence sources by credibility before they are
passed to the Gemini synthesis prompt. This ensures the AI receives
the most authoritative evidence first and produces better-calibrated
confidence scores.

Evidence tier hierarchy (per VeriFeed_Project_Blueprint_Final.md §78.4):

  Tier 1 — Official Institutional Alerts   (score: 100)
  Tier 2 — Fact Checker Ratings            (score:  75)
  Tier 3 — Reputable News Articles         (score:  50)
  Tier 4 — Community Submission Signals    (score:  20)
  Tier 5 — Unknown / Uncategorised        (score:   5)

Confidence calibration formula:
  base = weighted average of top-3 evidence tier scores (0–1)
  recency_bonus = +0.10 if any source is < 30 days old
  alignment_bonus = +0.05 per additional corroborating source (cap: +0.15)
  final = min(base + recency_bonus + alignment_bonus, 0.99)

Methodology string:
  Human-readable explanation of how the verdict was reached — surfaced
  in the API response and rendered in VerdictFirstResult.tsx.
"""

import datetime
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Evidence source type → tier score
# ---------------------------------------------------------------------------

TIER_SCORES: dict[str, int] = {
    "Official Institutional Alert": 100,
    "Fact Checker Rating": 75,
    "News Article": 50,
    "Community Submission": 20,
    # Fallback for any unrecognised type
    "Unknown": 5,
}

# Evidence types that are considered authoritative enough to anchor verdicts
AUTHORITATIVE_TYPES = frozenset(["Official Institutional Alert", "Fact Checker Rating"])

# Known high-reputation outlet names (partial match, case-insensitive)
HIGH_REPUTATION_OUTLETS = [
    "reuters", "bbc", "associated press", "ap news", "guardian",
    "africa check", "firstcheck", "pesacheck", "dubawa",
    "reserve bank of malawi", "rbm", "malawi communications regulatory authority", "macra",
    "standard bank", "airtel", "fdh", "national bank", "tnm",
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RankedSource:
    title: str
    outlet: str
    url: str
    source_type: str
    tier_score: int
    reputation_bonus: int
    published_date: str | None
    recency_score: float
    final_score: float
    methodology_note: str


@dataclass
class RankingResult:
    ranked_sources: list[RankedSource] = field(default_factory=list)
    confidence_score: float = 0.5
    methodology: str = ""
    evidence_tier_summary: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------

class EvidenceRanker:
    """
    Scores and ranks evidence sources for the VeriFeed verification pipeline.

    Usage:
        result = EvidenceRanker.rank(evidence_sources, institutional_matches, fact_check_results)
        ranked_sources = result.ranked_sources        # for API response
        confidence = result.confidence_score          # calibrated 0.0–0.99
        methodology = result.methodology              # human-readable explanation
    """

    @staticmethod
    def _tier_score(source_type: str) -> int:
        for key, score in TIER_SCORES.items():
            if key.lower() in source_type.lower():
                return score
        return TIER_SCORES["Unknown"]

    @staticmethod
    def _reputation_bonus(outlet: str) -> int:
        """+15 if outlet is in the high-reputation list."""
        outlet_lower = outlet.lower()
        for rep_outlet in HIGH_REPUTATION_OUTLETS:
            if rep_outlet in outlet_lower:
                return 15
        return 0

    @staticmethod
    def _recency_score(published_date_str: str | None) -> float:
        """
        Returns a 0.0–1.0 recency score.
        1.0 = within 7 days, 0.7 = within 30 days, 0.3 = within 1 year, 0.0 = older/unknown.
        """
        if not published_date_str:
            return 0.0
        # Try to parse common date formats
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y"):
            try:
                dt = datetime.datetime.strptime(
                    published_date_str.strip()[:19], fmt
                ).replace(tzinfo=datetime.UTC)
                now = datetime.datetime.now(tz=datetime.UTC)
                days_old = (now - dt).days
                if days_old <= 7:
                    return 1.0
                if days_old <= 30:
                    return 0.7
                if days_old <= 365:
                    return 0.3
                return 0.05
            except ValueError:
                continue
        return 0.0

    @classmethod
    def _score_source(cls, src: dict[str, Any]) -> RankedSource:
        source_type = src.get("type", "Unknown")
        outlet = src.get("outlet", "")
        published_date = src.get("published_date") or src.get("published_at")

        tier = cls._tier_score(source_type)
        rep_bonus = cls._reputation_bonus(outlet)
        recency = cls._recency_score(str(published_date) if published_date else None)
        recency_pts = int(recency * 20)  # max +20 pts

        final = tier + rep_bonus + recency_pts

        note = f"{source_type} from {outlet or 'unknown'}"
        if recency >= 0.7:
            note += " (recent)"
        if rep_bonus:
            note += " (high-reputation source)"

        return RankedSource(
            title=src.get("title", ""),
            outlet=outlet,
            url=src.get("url", ""),
            source_type=source_type,
            tier_score=tier,
            reputation_bonus=rep_bonus,
            published_date=str(published_date) if published_date else None,
            recency_score=recency,
            final_score=final,
            methodology_note=note,
        )

    @classmethod
    def _calibrate_confidence(
        cls,
        ranked: list[RankedSource],
        institutional_count: int,
        fact_check_count: int,
        article_count: int,
    ) -> float:
        """
        Calibrate confidence score from ranked evidence.

        The more authoritative and corroborating the evidence, the higher
        the confidence. Caps at 0.99 (never 100% — model outputs are
        probabilistic and institutional confirmation may be stale).
        """
        if not ranked:
            return 0.1

        # Base: weighted average of top-3 sources (normalised to 0–1)
        top3 = ranked[:3]
        max_possible = TIER_SCORES["Official Institutional Alert"] + 15 + 20  # 135
        base = sum(s.final_score for s in top3) / (len(top3) * max_possible)

        # Authoritative anchor bonus
        if institutional_count >= 1:
            base = max(base, 0.85)  # institutional alerts anchor confidence high
        if fact_check_count >= 1:
            base = max(base, 0.70)

        # Alignment bonus: multiple corroborating sources
        total_sources = institutional_count + fact_check_count + article_count
        alignment_bonus = min((total_sources - 1) * 0.05, 0.15) if total_sources > 1 else 0.0

        # Recency bonus
        recent = any(s.recency_score >= 0.7 for s in ranked)
        recency_bonus = 0.05 if recent else 0.0

        return round(min(base + alignment_bonus + recency_bonus, 0.99), 3)

    @classmethod
    def _build_methodology(
        cls,
        ranked: list[RankedSource],
        institutional_count: int,
        fact_check_count: int,
        article_count: int,
        prior_screening_risk: str | None,
    ) -> str:
        """Build a user-friendly plain-language methodology explanation."""
        parts: list[str] = []

        if institutional_count:
            parts.append(
                f"Cross-referenced with {institutional_count} official institutional alert"
                f"{'s' if institutional_count > 1 else ''} in the VeriFeed registry."
            )
        if fact_check_count:
            parts.append(
                f"Evaluated {fact_check_count} independent fact-checker rating"
                f"{'s' if fact_check_count > 1 else ''}."
            )
        if article_count:
            parts.append(
                f"Matched against {article_count} verified news report"
                f"{'s' if article_count > 1 else ''} from trusted media outlets."
            )

        if not ranked:
            parts.append(
                "No official press releases, government disclaimers, or verified news articles were found matching this circulating claim."
            )

        if prior_screening_risk and prior_screening_risk != "Low":
            parts.append(
                f"Stage 1 threat screening flagged risk indicators ({prior_screening_risk} Risk)."
            )

        top = ranked[:2]
        if top:
            top_notes = "; ".join(s.methodology_note for s in top)
            parts.append(f"Primary sources: {top_notes}.")

        parts.append(
            "Final verdict was synthesized using grounded evidence analysis."
        )

        return " ".join(parts)

    @classmethod
    def rank(
        cls,
        evidence_sources: list[dict[str, Any]],
        institutional_count: int = 0,
        fact_check_count: int = 0,
        article_count: int = 0,
        prior_screening_risk: str | None = None,
    ) -> RankingResult:
        """
        Rank evidence sources and calibrate confidence.

        Args:
            evidence_sources: Raw evidence dicts from the pipeline.
            institutional_count: Number of institutional alert matches found.
            fact_check_count: Number of fact-checker results found.
            article_count: Number of news articles matched.
            prior_screening_risk: Optional Stage 1 risk level ('Low','Medium','High').

        Returns:
            RankingResult with ranked sources, calibrated confidence, and methodology.
        """
        if not evidence_sources:
            methodology = cls._build_methodology([], 0, 0, 0, prior_screening_risk)
            return RankingResult(
                ranked_sources=[],
                confidence_score=0.1,
                methodology=methodology,
                evidence_tier_summary={},
            )

        # Score each source
        scored = [cls._score_source(src) for src in evidence_sources]

        # Deduplicate by URL (keep highest-scoring entry)
        seen_urls: dict[str, RankedSource] = {}
        for src in scored:
            url = src.url or src.title
            if url not in seen_urls or src.final_score > seen_urls[url].final_score:
                seen_urls[url] = src

        # Sort by final_score descending
        ranked = sorted(seen_urls.values(), key=lambda s: s.final_score, reverse=True)

        # Tier summary for diagnostics
        tier_summary: dict[str, int] = {}
        for src in ranked:
            tier_summary[src.source_type] = tier_summary.get(src.source_type, 0) + 1

        confidence = cls._calibrate_confidence(
            ranked, institutional_count, fact_check_count, article_count
        )
        methodology = cls._build_methodology(
            ranked, institutional_count, fact_check_count, article_count, prior_screening_risk
        )

        return RankingResult(
            ranked_sources=ranked,
            confidence_score=confidence,
            methodology=methodology,
            evidence_tier_summary=tier_summary,
        )


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------

def rank_evidence(
    evidence_sources: list[dict[str, Any]],
    institutional_count: int = 0,
    fact_check_count: int = 0,
    article_count: int = 0,
    prior_screening_risk: str | None = None,
) -> dict[str, Any]:
    """
    Module-level entry point for evidence ranking.
    Returns a plain dict suitable for the verification pipeline.
    """
    result = EvidenceRanker.rank(
        evidence_sources,
        institutional_count=institutional_count,
        fact_check_count=fact_check_count,
        article_count=article_count,
        prior_screening_risk=prior_screening_risk,
    )
    return {
        "ranked_sources": [
            {
                "title": s.title,
                "outlet": s.outlet,
                "url": s.url,
                "type": s.source_type,
                "tier_score": s.tier_score,
                "final_score": s.final_score,
                "recency_score": s.recency_score,
                "published_date": s.published_date,
            }
            for s in result.ranked_sources
        ],
        "confidence_score": result.confidence_score,
        "methodology": result.methodology,
        "evidence_tier_summary": result.evidence_tier_summary,
    }
