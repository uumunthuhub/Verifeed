import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.institution import Institution, InstitutionalAlert
from app.models.source import Source
from app.models.verification_log import CanonicalVerdict, VerificationLog
from app.services.ai import get_ai_service
from app.services.channel_verification import verify_official_channels
from app.services.entity_extraction import extract_entities_from_text
from app.services.evidence_ranker import EvidenceRanker, WeightedConfidenceCalculator
from app.services.fact_check import search_google_fact_check
from app.services.local_screening import LocalScreeningEngine
from app.services.phash_service import (
    compute_phash_from_b64,
    find_signature_match,
    is_forgery_match,
    s_signature,
)

logger = logging.getLogger(__name__)

VERDICT_TYPES = [
    "Confirmed Scam",
    "Confirmed",
    "Unconfirmed",
    "Disputed / False",
    "No Coverage Found",
]

OCR_PROMPT = (
    "Extract all text, headlines, phone numbers, and main claims visible in this "
    "screenshot or document image. Return only the extracted text and claim summary."
)


def get_query_embedding(text: str) -> list[float] | None:
    """Generate a vector embedding via the AI service boundary."""
    if not text.strip():
        return None
    return get_ai_service().embed(text)


from app.services.live_search import classify_query_topic, is_article_relevant, search_live_web_news


def extract_significant_keywords(text: str) -> list[str]:
    """Extract words for fallback keyword search excluding domain/location stopwords."""
    if not text:
        return []
    words = [w.strip(",.!?\"'").lower() for w in text.split()]
    stopwords = {
        "with", "from", "that", "this", "have", "offer", "offering", "your", "free", "more",
        "malawi", "malawian", "africa", "african", "government", "official", "news", "media",
        "article", "report", "system", "does", "there", "here", "what", "where", "when",
        "is", "are", "was", "were", "been", "being", "check", "verify", "claim", "about",
        "info", "information", "notice", "alert", "update", "latest"
    }
    preserved_short = {"id", "ai", "tv", "5g", "3g", "4g", "sd", "uk", "us", "eu", "un", "mw", "qr"}
    keywords = []
    for w in words:
        if w in stopwords or not w:
            continue
        if len(w) >= 3 or w in preserved_short or "-" in w:
            keywords.append(w)
    return keywords


def extract_text_from_image_data(image_data: str) -> str:
    """Extract OCR text and claims from base64 image data via the AI service."""
    return get_ai_service().extract_from_image(image_data, OCR_PROMPT)


async def verify_claim(
    db: Session,
    query: str,
    image_data: str | None = None,
    audio_data: str | None = None,
    prior_screening: dict | None = None,
) -> dict[str, Any]:
    """
    6-stage VeriFeed verification pipeline.

    Stages:
      1. Ingestion     — OCR + Audio transcription + AI Image Authenticity + pHash
      2. Inline Rules  — LocalScreeningEngine fast-exit (deterministic, < 5ms)
      3. RAG + Live    — DB Alerts + DB News + Fact-Checkers + Real-Time Live Web Search
      4. Scoring       — EvidenceRanker + WeightedConfidenceCalculator
      5. Evidence Gate — Zero-evidence skip (no Gemini call)
      6. Synthesis     — Gemini grounding + guardrails + canonical verdict

    Args:
        db: SQLAlchemy session.
        query: The claim text, message, or URL to verify.
        image_data: Optional base64-encoded image for OCR extraction & AI authenticity check.
        audio_data: Optional base64-encoded audio note for voice transcription.
        prior_screening: Optional pre-computed Stage 1 ScreeningResult dict.
    """
    ai = get_ai_service()

    # Stage 1: Ingestion — OCR + Audio transcription + AI Image Authenticity + pHash computation
    ocr_text = ""
    audio_transcription = ""
    image_authenticity: dict[str, Any] | None = None
    image_phash: str | None = None

    if image_data:
        ocr_text = extract_text_from_image_data(image_data)
        logger.info("Stage 1: Extracted OCR text from image: %s", ocr_text[:200])
        try:
            image_authenticity = ai.analyze_image_authenticity(image_data)
            logger.info("Stage 1: AI image authenticity result: %s", image_authenticity)
        except Exception as exc:
            logger.error("Error analyzing image authenticity: %s", exc)
        image_phash = compute_phash_from_b64(image_data)
        if image_phash:
            logger.info("Stage 1: Computed image pHash: %s", image_phash)

    if audio_data:
        try:
            audio_transcription = ai.extract_from_audio(
                audio_data,
                "Transcribe all spoken text, language (Chichewa/English), tone, and main claims in this voice note or audio clip."
            )
            logger.info("Stage 1: Transcribed audio text: %s", audio_transcription[:200])
        except Exception as exc:
            logger.error("Error extracting text from audio: %s", exc)

    full_query = f"{query} {ocr_text} {audio_transcription}".strip() or "Unspecified claim"


    # Stage 2a: pHash Signature Check — forgery fast-exit (Phase 5 — G11 fix)
    # If the uploaded image matches a known forgery in the DB (Hamming <= 10),
    # return HIGH_RISK_SCAM immediately without touching RAG or Gemini.
    phash_match: dict | None = None
    phash_hamming: int | None = None
    if image_phash:
        phash_match = find_signature_match(image_phash, db)
        if phash_match:
            phash_hamming = phash_match["hamming_distance"]
            logger.info(
                "Stage 2a pHash match: document_type=%s is_known_forgery=%s hamming=%d",
                phash_match["document_type"],
                phash_match["is_known_forgery"],
                phash_hamming,
            )
            if phash_match["is_known_forgery"] and phash_hamming is not None and is_forgery_match(phash_hamming):
                logger.info("Stage 2a: Known forgery detected — fast-exit HIGH_RISK_SCAM.")
                return {
                    "id": -1,
                    "query": full_query,
                    "canonical_verdict": CanonicalVerdict.HIGH_RISK_SCAM,
                    "verdict": "Confirmed Scam",
                    "claim_verdict": None,
                    "message_authenticity_verdict": None,
                    "confidence_score": round(1.0 - (phash_hamming / 64), 3),
                    "risk_level": "High",
                    "sub_scores": {
                        "domain": 0.2,
                        "vector": 0.0,
                        "signature": s_signature(phash_hamming),
                        "telecom": 0.0,
                    },
                    "summary": (
                        f"The uploaded image is a near-identical match (Hamming distance: {phash_hamming}) "
                        f"to a known forged document in the VeriFeed registry: '{phash_match['document_type']}'. "
                        "This document has been confirmed as a forgery by VeriFeed administrators. "
                        "Do not act on this document — report it to the relevant authorities."
                    ),
                    "actionable_advice": (
                        "Do not share, forward, or act on this document. "
                        "Report it to the institution it impersonates and to the Malawi Police Service Cybercrime Unit."
                    ),
                    "official_sources": (
                        [{"name": "Source", "url": phash_match["reference_source_url"]}]
                        if phash_match.get("reference_source_url") else []
                    ),
                    "sources": [],
                    "extracted_sender": None,
                    "extracted_numbers": None,
                    "extracted_urls": None,
                    "extracted_institutions": None,
                    "verification_details": None,
                    "recommended_actions": [
                        {"action": "Report to authorities", "priority": "critical",
                         "reason": "Confirmed document forgery detected via pHash signature matching"}
                    ],
                    "methodology": (
                        f"Stage 2a pHash signature check: Hamming distance {phash_hamming} "
                        f"<= threshold {10}. Match: '{phash_match['document_type']}'. "
                        "Deterministic forgery fast-exit — no Gemini call required."
                    ),
                    "created_at": "",
                }

    # Stage 2: Inline Rule Engine fast-exit (Phase 4 — G9 fix)
    # Run LocalScreeningEngine deterministically. If the content is a clear-cut
    # high-risk scam (High risk AND no deep-verify needed), return immediately
    # without any DB queries, vector search, or Gemini call.
    inline_screening = LocalScreeningEngine.screen(full_query)
    logger.info(
        "Stage 2 inline screening: risk=%s needs_deep_verify=%s signals=%d",
        inline_screening.risk_level,
        inline_screening.needs_deep_verify,
        len(inline_screening.signals),
    )
    if inline_screening.risk_level == "High" and not inline_screening.needs_deep_verify:
        logger.info("Stage 2: High-risk fast exit — returning HIGH_RISK_SCAM without DB/Gemini.")
        matched = [
            s.matched_text for s in inline_screening.signals if s.matched_text
        ]
        return {
            "id": -1,  # no DB row persisted for deterministic fast exits
            "query": full_query,
            "canonical_verdict": CanonicalVerdict.HIGH_RISK_SCAM,
            "verdict": "Confirmed Scam",  # legacy compat
            "claim_verdict": None,
            "message_authenticity_verdict": None,
            "confidence_score": 0.95,
            "risk_level": "High",
            "sub_scores": {"domain": 0.2, "vector": 0.0, "signature": 0.0, "telecom": 0.0},
            "summary": (
                f"VeriFeed's real-time screening engine detected {len(inline_screening.signals)} "
                f"high-risk signal(s) in this content: {', '.join(s.signal_type.replace('_', ' ') for s in inline_screening.signals)}. "
                f"Matched indicators: {', '.join(matched) if matched else 'multiple scam patterns'}. "
                "This is consistent with known fraud campaigns targeting Malawian citizens via WhatsApp and SMS."
            ),
            "actionable_advice": inline_screening.recommended_action,
            "official_sources": [],
            "sources": [],
            "extracted_sender": None,
            "extracted_numbers": None,
            "extracted_urls": inline_screening.screened_urls,
            "extracted_institutions": inline_screening.detected_institutions,
            "verification_details": None,
            "recommended_actions": [
                {"action": inline_screening.recommended_action, "priority": "critical", "reason": "Real-time scam signal detected"}
            ],
            "methodology": (
                f"Stage 2 inline rule engine detected {len(inline_screening.signals)} high-severity signal(s). "
                "No deep verification required — deterministic fast exit."
            ),
            "created_at": "",
        }

    # Stage 2 passed (Medium/Low risk or needs_deep_verify) — continue pipeline
    # Pass the inline screening result as prior_screening if no external one was given
    if prior_screening is None and inline_screening.risk_level != "Low":
        prior_screening = {
            "risk_level": inline_screening.risk_level,
            "signals": [s.signal_type for s in inline_screening.signals],
            "recommended_action": inline_screening.recommended_action,
        }

    prior_risk_level = prior_screening.get("risk_level", "Low") if prior_screening else inline_screening.risk_level

    # Extract entities from message
    extracted_entities = extract_entities_from_text(full_query, use_ai=False)
    logger.info("Extracted entities: %s", extracted_entities)

    # Verify official channels
    channel_verification = verify_official_channels(extracted_entities, db)
    logger.info("Channel verification result: %s", channel_verification)
    
    query_vector = get_query_embedding(full_query)
    keywords = extract_significant_keywords(full_query)

    evidence_sources: list[dict[str, Any]] = []
    institutional_matches: list[dict[str, str]] = []

    # 1. Institutional Fraud Alert search — vector then keyword fallback
    raw_alerts: list[Any] = []
    if query_vector:
        try:
            alerts_query = db.query(InstitutionalAlert, Institution).join(Institution)

            if extracted_entities.get("institution_names"):
                inst_filters = [Institution.name.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]]
                alerts_query = alerts_query.filter(or_(*inst_filters))

            alerts = (
                alerts_query
                .filter(InstitutionalAlert.embedding.l2_distance(query_vector) < 0.8)
                .order_by(InstitutionalAlert.embedding.l2_distance(query_vector))
                .limit(3)
                .all()
            )
            raw_alerts.extend(alerts)
        except Exception as exc:
            logger.error("Error searching institutional alerts: %s", exc)

    if not raw_alerts and len(keywords) >= 1:
        alert_filters: list[Any] = (
            [InstitutionalAlert.title.ilike(f"%{kw}%") for kw in keywords]
        )
        if extracted_entities.get("institution_names"):
            inst_filters = [Institution.name.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]]
            alert_filters.append(or_(*inst_filters))

        kw_alerts = (
            db.query(InstitutionalAlert, Institution)
            .join(Institution)
            .filter(or_(*alert_filters))
            .limit(3)
            .all()
        )
        raw_alerts.extend(kw_alerts)

    # Filter raw_alerts for subject relevance
    seen_alert_ids: set[int] = set()
    for row in raw_alerts:
        alert: InstitutionalAlert = row[0]
        inst: Institution = row[1]
        alert_id = int(str(alert.id))
        if alert_id in seen_alert_ids:
            continue
        seen_alert_ids.add(alert_id)
        alert_title = str(alert.title or "")
        alert_text = str(alert.alert_text or "")
        if is_article_relevant(full_query, alert_title, alert_text):
            institutional_matches.append({
                "institution": str(inst.name),
                "title": alert_title,
                "alert_text": alert_text,
                "url": str(alert.source_url or ""),
                "published_date": str(alert.published_date) if hasattr(alert, "published_date") and alert.published_date else "",
            })
            evidence_sources.append({
                "title": f"Official Alert: {alert_title}",
                "outlet": str(inst.name),
                "url": str(alert.source_url or ""),
                "type": "Official Institutional Alert",
            })
        else:
            logger.debug("Filtered out non-relevant institutional alert '%s' for claim '%s'", alert_title, full_query)

    # 2. Indexed approved-source search — vector then keyword fallback
    articles_retrieved: list[dict[str, str]] = []
    raw_articles: list[Any] = []
    evidence_cutoff = datetime.now(UTC) - timedelta(days=7)
    if query_vector:
        try:
            articles_query = db.query(Article, Source).join(Source).filter(
                Source.is_active.is_(True),
                Source.trust_tier.in_([1, 2]),
                Article.retrieved_at >= evidence_cutoff,
                Article.content.isnot(None),
            )

            if extracted_entities.get("institution_names"):
                inst_filters = [Article.headline.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]] + \
                               [Source.name.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]]
                articles_query = articles_query.filter(or_(*inst_filters))

            matched = (
                articles_query
                .filter(Article.embedding.l2_distance(query_vector) < 0.8)
                .order_by(Article.embedding.l2_distance(query_vector))
                .limit(5)
                .all()
            )
            raw_articles.extend(matched)
        except Exception as exc:
            logger.error("Error searching article vector index: %s", exc)

    if not raw_articles and len(keywords) >= 1:
        art_filters: list[Any] = [
            or_(Article.headline.ilike(f"%{kw}%"), Article.content.ilike(f"%{kw}%"))
            for kw in keywords[:3]
        ]
        if extracted_entities.get("institution_names"):
            inst_filters = [Article.headline.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]] + \
                           [Source.name.ilike(f"%{inst}%") for inst in extracted_entities["institution_names"]]
            art_filters.append(or_(*inst_filters))

        kw_arts = (
            db.query(Article, Source)
            .join(Source)
            .filter(
                Source.is_active.is_(True),
                Source.trust_tier.in_([1, 2]),
                Article.retrieved_at >= evidence_cutoff,
                Article.content.isnot(None),
                and_(*art_filters),
            )
            .limit(5)
            .all()
        )
        raw_articles.extend(kw_arts)

    # Filter raw_articles for subject relevance
    seen_art_ids: set[int] = set()
    for row in raw_articles:
        art: Article = row[0]
        src: Source = row[1]
        art_id = int(str(art.id))
        if art_id in seen_art_ids:
            continue
        seen_art_ids.add(art_id)
        headline_str = str(art.headline or "")
        content_str = str(art.content or "")
        trust_tier_val = int(str(src.trust_tier)) if src.trust_tier is not None else 2
        if is_article_relevant(full_query, headline_str, content_str):
            articles_retrieved.append({
                "headline": headline_str,
                "outlet": str(src.name),
                "url": str(art.url),
                "published_date": str(art.published_at) if art.published_at else "",
                "retrieved_at": str(art.retrieved_at),
                "excerpt": content_str[:1500],
                "trust_tier": str(trust_tier_val),
            })
            evidence_sources.append({
                "title": headline_str,
                "outlet": str(src.name),
                "url": str(art.url),
                "type": "News Article",
                "published_date": str(art.published_at) if art.published_at else "",
                "trust_tier": trust_tier_val,
            })

    # 2.5 Live Web Search Fallback
    # Trigger if local Pgvector searches yield no relevant articles
    if not articles_retrieved:
        logger.info("Local database yielded no articles. Querying live web search...")
        live_news = search_live_web_news(full_query)
        for news in live_news:
            articles_retrieved.append({
                "headline": news["headline"],
                "outlet": news["outlet"],
                "url": news["url"],
                "published_date": news.get("published_date", ""),
                "retrieved_at": str(datetime.now(UTC)),
                "excerpt": news.get("excerpt", ""),
                "trust_tier": str(news.get("trust_tier", 2)),
            })
            evidence_sources.append({
                "title": news["headline"],
                "outlet": news["outlet"],
                "url": news["url"],
                "type": news["type"],
                "published_date": news.get("published_date", ""),
                "trust_tier": news.get("trust_tier", 2),
            })

    # 3. Google Fact Check Tools API
    fact_check_results = await search_google_fact_check(full_query)
    for fc in fact_check_results:
        evidence_sources.append({
            "title": f"{fc['claimant']} claim: {fc['rating']}",
            "outlet": fc["publisher"],
            "url": fc["url"],
            "type": "Fact Checker Rating",
        })

    # 4. Determine dual verdicts based on approved evidence and channel verification
    claim_verdict = None
    message_authenticity_verdict = None
    risk_level = "Low"
    recommended_actions = []
    actionable_advice = ""

    
    # Message Authenticity Verdict (based on channel verification)
    if channel_verification.get('sender_verified') or channel_verification.get('channel_verified'):
        message_authenticity_verdict = "Verified Official"
        risk_level = "Low"
        recommended_actions.append({
            "action": "This message appears to be from an official verified channel",
            "priority": "low",
            "reason": f"Sender/channel matched official registry for {channel_verification.get('matched_institution')}"
        })
    elif channel_verification.get('matched_institution'):
        message_authenticity_verdict = "Suspicious"
        risk_level = "High"
        recommended_actions.append({
            "action": "Do not trust this message - institution detected but channel not verified",
            "priority": "critical",
            "reason": f"Institution {channel_verification.get('matched_institution')} detected but sender/channel not in official registry"
        })
    else:
        message_authenticity_verdict = "Unverified"
        risk_level = "High" if (prior_risk_level == "High" or inline_screening.risk_level == "High") else "Medium"
    
    # Claim Verdict (based on evidence)
    if institutional_matches:
        claim_verdict = "False"
        risk_level = "High"
        if not any(action['priority'] == 'critical' for action in recommended_actions):
            recommended_actions.append({
                "action": "Do not act on this message - official scam alert exists",
                "priority": "critical",
                "reason": "Official institutional alerts identify this specific claim as fraudulent"
            })
    elif prior_risk_level == "High" or inline_screening.risk_level == "High":
        claim_verdict = "False"
        risk_level = "High"
    elif articles_retrieved:
        if len(articles_retrieved) >= 2:
            claim_verdict = "True"
        else:
            claim_verdict = "Insufficient Evidence"
        risk_level = "Low" if inline_screening.risk_level == "Low" else "Medium"
    elif fact_check_results:
        # Check fact check ratings
        fc_ratings = [fc.get('rating', '').lower() for fc in fact_check_results]
        if any('false' in r or 'scam' in r for r in fc_ratings):
            claim_verdict = "False"
            risk_level = "High"
        elif any('true' in r or 'accurate' in r for r in fc_ratings):
            claim_verdict = "True"
            risk_level = "Low"
        else:
            claim_verdict = "Misleading"
            risk_level = "Medium"
    else:
        claim_verdict = "Insufficient Evidence"
        risk_level = "Low" if inline_screening.risk_level == "Low" else "Medium"
    
    # Legacy single verdict for backward compatibility
    verdict = "No Coverage Found"
    if institutional_matches or prior_risk_level == "High" or inline_screening.risk_level == "High":
        verdict = "Confirmed Scam"
    elif claim_verdict == "Misleading" or articles_retrieved:
        verdict = "Unconfirmed"
    
    # Detect if context is local (Malawi) or global for tailored messaging
    query_lower = full_query.lower()
    local_keywords = ["malawi", "kwacha", "mra", "escom", "lilongwe", "blantyre", "mzuzu", "zodiak", "times", "mcb", "chakwera", "chilima", "mutharika"]
    is_local_context = (
        any(kw in query_lower for kw in local_keywords) or
        bool(extracted_entities.get("institution_names")) or
        bool(extracted_entities.get("phone_numbers"))
    )

    # Add default user-friendly recommended actions if none set
    if not recommended_actions:
        if risk_level == "High":
            recommended_actions = [
                {
                    "action": "Do not send money, share credentials, or visit offices based on this message",
                    "priority": "critical",
                    "reason": "Official authorities do not make critical policy or financial announcements solely via unverified social media forwards."
                },
                {
                    "action": "Verify directly with official portals",
                    "priority": "high",
                    "reason": "Check official public channels or verified news broadcasts before taking action."
                }
            ]
        else:
            if is_local_context:
                recommended_actions = [
                    {
                        "action": "Treat this circulating message as unverified and refrain from forwarding it",
                        "priority": "medium",
                        "reason": "Forwarding unverified public notices causes unnecessary panic and financial anxiety among citizens."
                    },
                    {
                        "action": "Confirm details via official announcements or verified news broadcasts",
                        "priority": "medium",
                        "reason": "Official public notices are published through official government press releases or verified news outlets like Zodiak TV."
                    }
                ]
            else:
                recommended_actions = [
                    {
                        "action": "Treat this circulating claim as unverified and refrain from sharing it",
                        "priority": "medium",
                        "reason": "Forwarding unverified claims contributes to misinformation."
                    },
                    {
                        "action": "Confirm details via verified international news outlets",
                        "priority": "medium",
                        "reason": "Major global events are consistently covered by credible international news organizations and fact-checkers."
                    }
                ]

    # D1: Rank evidence before Gemini synthesis
    prior_risk_level = prior_screening.get("risk_level") if prior_screening else None
    ranking = EvidenceRanker.rank(
        evidence_sources,
        institutional_count=len(institutional_matches),
        fact_check_count=len(fact_check_results),
        article_count=len(articles_retrieved),
        prior_screening_risk=prior_risk_level,
    )
    ranked_sources = [
        {
            "title": s.title,
            "outlet": s.outlet,
            "url": s.url,
            "type": s.source_type,
        }
        for s in ranking.ranked_sources
    ]
    methodology = ranking.methodology

    # Phase 2 (G5/G6): Compute weighted 4-component confidence sub-scores
    # Determine top source tier from ranked evidence
    top_tier = 4  # default: community/unknown
    if ranking.ranked_sources:
        top_tier = ranking.ranked_sources[0].trust_tier
    # Vector similarity: use top ranked source final_score normalised to 0-1
    top_vector_sim = 0.0
    if ranking.ranked_sources:
        top_vector_sim = min(ranking.ranked_sources[0].recency_score, 1.0)
    # Telecom: sender_verified from channel verification
    is_sender_verified = channel_verification.get("sender_verified") or False

    weighted_sub = WeightedConfidenceCalculator.compute(
        top_source_tier=top_tier,
        vector_similarity=top_vector_sim,
        hamming_distance=phash_hamming,   # Phase 5: live pHash Hamming distance
        is_verified_sender=is_sender_verified,
    )
    weighted_total = weighted_sub.total()

    summary = "VeriFeed has analyzed available news databases and found no official alerts or news reports matching this claim in registered news sources."

    if institutional_matches:
        inst_names = ", ".join(sorted({m["institution"] for m in institutional_matches}))
        alert_details = [f"{m['institution']} ('{m['title']}'): {m['alert_text']}" for m in institutional_matches]
        summary = (
            f"VeriFeed has found evidence regarding this claim or question: Official scam disclaimers have been issued by {inst_names}. "
            + " ".join(alert_details)
        )
    elif articles_retrieved:
        outlets_str = ", ".join(sorted({str(a["outlet"]) for a in articles_retrieved}))
        top_headlines = "; ".join([f"'{a['headline']}' ({a['outlet']})" for a in articles_retrieved[:3]])
        summary = (
            f"VeriFeed has found evidence regarding this claim or question: Retrieved {len(articles_retrieved)} report(s) from licensed news media ({outlets_str}). "
            f"News coverage details: {top_headlines}."
        )

    # Phase 3 (G8): Stage 5 — Deterministic zero-evidence skip
    # If no evidence was retrieved, return UNVERIFIED without calling Gemini.
    # This prevents hallucination and wastes no API quota.
    has_evidence = institutional_matches or articles_retrieved or fact_check_results
    if not has_evidence:
        logger.info("Stage 5: Zero evidence — skipping Gemini.")
        if prior_risk_level == "High" or inline_screening.risk_level == "High":
            verdict = "Confirmed Scam"
        else:
            verdict = "No Coverage Found"
    else:
        # -----------------------------------------------------------------------
        # Stage 6: Gemini Synthesis with Anti-Hallucination Guardrails (G7 fix)
        # -----------------------------------------------------------------------
        # Build prior_screening context block for prompt
        prior_context = ""
        if prior_screening:
            prior_context = f"""
STAGE 1 LOCAL SCREENING RESULT (pre-Gemini):
  risk_level: {prior_screening.get('risk_level', 'Unknown')}
  signals: {prior_screening.get('signals', [])}
  recommended_action: {prior_screening.get('recommended_action', '')}
"""

        ranked_evidence_formatted = [
            {
                "title": item["headline"],
                "outlet": item["outlet"],
                "url": item["url"],
                "published_date": item.get("published_date"),
                "retrieved_at": item.get("retrieved_at"),
                "trust_tier": item.get("trust_tier"),
                "excerpt": item.get("excerpt"),
            }
            for item in articles_retrieved[:5]
        ]
        ranked_evidence_json = json.dumps(ranked_evidence_formatted, indent=2)

        # Detect query topic for topic-aware synthesis guardrail
        topic_category, _suffix, topic_exclusions = classify_query_topic(full_query)
        topic_context_note = ""
        if topic_category != "general":
            topic_context_note = (
                f"\nDETECTED TOPIC CATEGORY: {topic_category.upper()}\n"
                f"IMPORTANT: This claim is about '{topic_category}' — do NOT cite sources or institutions "
                f"from unrelated categories (e.g., do not cite financial regulators for a wildlife/nature claim, "
                f"or wildlife articles for a finance/banking claim). "
                f"Only include official_sources whose subject directly relates to '{topic_category}'."
            )

        synthesis_prompt = f"""You are the VeriFeed Grounding & Synthesis Agent — an AI investigator for Malawi and global news context.

CRITICAL GUARDRAILS (MUST FOLLOW — violations make the output invalid):
1. You are NOT the source of truth. The provided EVIDENCE SNIPPETS ARE the source of truth.
2. NEVER use your internal pre-trained knowledge to confirm or deny a claim. Base your analysis on the provided news articles and official disclaimers.
3. Verdict MUST be EXACTLY one of these 5 canonical labels — no other strings are accepted:
   - VERIFIED_TRUE      → Tier 1 or Tier 2 licensed news articles report or confirm the claim is true.
   - VERIFIED_FALSE     → Tier 1 or Tier 2 evidence directly refutes or debunks the claim.
   - HIGH_RISK_SCAM     → Evidence or pattern matches a known scam, phishing, or forgery.
   - PENDING_VERIFICATION → Contradictory evidence, ongoing analysis, or unconfirmed media reports.
   - UNVERIFIED         → Insufficient evidence — do not guess or assume.
4. actionable_advice MUST be in plain language suitable for citizens (English or Chichewa).
5. official_sources format MUST be: [{{"name": "...", "url": "..."}}] — no other format.
6. TOPIC RELEVANCE: official_sources MUST only include sources whose content is directly related to the claim's subject matter. Do NOT include sources about unrelated topics even if they appear in the evidence list.{topic_context_note}

CLAIM TO VERIFY:
"{full_query}"
{prior_context}
EXTRACTED ENTITIES:
{json.dumps(extracted_entities, indent=2)}

CHANNEL VERIFICATION:
{json.dumps(channel_verification, indent=2)}

RANKED EVIDENCE (highest credibility first — Tier 1 = Government/Regulatory, Tier 2 = Licensed Media):
{ranked_evidence_json}

INSTITUTIONAL ALERTS (Official scam warnings — Tier 1 authority):
{json.dumps(institutional_matches, indent=2)}

NEWS ARTICLES (Tier 2 licensed media):
{json.dumps(articles_retrieved, indent=2)}

FACT CHECK RATINGS (Tier 2 fact-checkers):
{json.dumps(fact_check_results, indent=2)}

SYNTHESIS REQUIREMENTS:
- The summary MUST explicitly begin with the prefix: "VeriFeed has found evidence regarding this claim or question:"
- Citing the news media outlets (e.g. Zodiak, Times, Reuters, RBM) and explaining how they have written about the article/claim.
- Include specific details from the articles: headlines, institution statements, date of reports, and key findings.
- The summary and sources MUST be about the same topic as the claim. If the claim is about wildlife/animals, cite wildlife/nature news. If the claim is about finance, cite finance news. Do NOT mix topics.

Return ONLY a valid JSON object in this exact format:
{{
  "verdict": "<one of the 5 canonical labels above>",
  "confidence_score": <float 0.0–1.0>,
  "summary": "VeriFeed has found evidence regarding this claim or question: <detailed explanation citing news outlets and how they wrote about the article>",
  "actionable_advice": "<plain-language next steps for the citizen>",
  "official_sources": [{{"name": "<source name>", "url": "<source url>"}}]
}}"""

        parsed = ai.generate_json(synthesis_prompt)
        if parsed:
            # Map Gemini output to canonical verdict (handles if Gemini returns legacy label)
            raw_verdict = parsed.get("verdict", verdict)
            candidate_verdict = CanonicalVerdict.from_legacy(raw_verdict)
            can_anchor_verdict = bool(institutional_matches or fact_check_results or len(articles_retrieved) >= 2)
            if candidate_verdict in {CanonicalVerdict.VERIFIED_TRUE, CanonicalVerdict.VERIFIED_FALSE} and not can_anchor_verdict:
                verdict = CanonicalVerdict.PENDING_VERIFICATION
            else:
                verdict = candidate_verdict

            # Synchronize claim_verdict and risk_level with canonical verdict from Gemini
            if verdict == CanonicalVerdict.VERIFIED_TRUE:
                claim_verdict = "True"
                risk_level = "Low"
            elif verdict in {CanonicalVerdict.VERIFIED_FALSE, CanonicalVerdict.HIGH_RISK_SCAM}:
                claim_verdict = "False"
                risk_level = "High"
            elif verdict == CanonicalVerdict.PENDING_VERIFICATION:
                claim_verdict = "Misleading"
                risk_level = "Medium"
            elif verdict == CanonicalVerdict.UNVERIFIED:
                claim_verdict = "Insufficient Evidence"
                risk_level = "Low" if inline_screening.risk_level == "Low" else "Medium"

            parsed_summary = parsed.get("summary", "")
            if parsed_summary and len(parsed_summary) > 20:
                summary = parsed_summary

            if parsed.get("actionable_advice"):
                actionable_advice = str(parsed["actionable_advice"])

    # Deduplicate evidence sources (use ranked_sources as the primary list)
    # ranked_sources is already deduplicated by the EvidenceRanker
    unique_sources = ranked_sources if ranked_sources else evidence_sources[:10]

    # Phase 1 (G1): Map to canonical verdict
    canonical_verdict = CanonicalVerdict.from_legacy(verdict)

    # Phase 2 (G5): Use weighted total as primary confidence score
    # Blend: weighted formula provides the base; existing ranker calibration
    # is kept as a secondary signal and averaged in.
    blended_confidence = round((weighted_total * 0.6 + ranking.confidence_score * 0.4), 3)

    # Phase 1 (G4): Build canonical actionable_advice from recommended_actions
    if not actionable_advice:
        if recommended_actions:
            top_action = recommended_actions[0]
            actionable_advice = top_action.get("action", "") + (
                f" {top_action.get('reason', '')}".strip() if top_action.get("reason") else ""
            )
        else:
            actionable_advice = (
                "No official record found in VeriFeed databases. "
                "Please verify with official authorities before acting."
            )

    # Phase 1 (G3): Build canonical official_sources in [{name, url}] format
    # Apply topic-compatibility filter: do not surface sources from unrelated categories
    # (e.g., RBM/finance sources for a wildlife query)
    _topic_cat, _topic_sfx, topic_excl = classify_query_topic(full_query)

    def _is_source_topic_compatible(src: dict) -> bool:
        """Return False if the source name/url contains an exclusion term for the detected topic."""
        if not topic_excl:
            return True
        combined = (f"{src.get('outlet', '')} {src.get('title', '')} {src.get('url', '')}").lower()
        return not any(excl in combined for excl in topic_excl)

    topic_filtered_sources = [s for s in unique_sources if _is_source_topic_compatible(s)]

    canonical_official_sources = [
        {"name": s.get("outlet") or s.get("title", "Unknown Source"), "url": s.get("url")}
        for s in topic_filtered_sources[:5]
        if s.get("url")
    ]

    # 5. Persist verification log with all Phase 1+2 fields
    log_entry = VerificationLog(
        query_text=full_query,
        # Phase 1 (G1): Canonical verdict
        canonical_verdict=canonical_verdict,
        # Dual verdict system (legacy)
        claim_verdict=claim_verdict,
        message_authenticity_verdict=message_authenticity_verdict,
        # Legacy single verdict
        verdict=verdict,
        # Phase 2 (G5): Weighted confidence
        confidence_score=blended_confidence,
        risk_level=risk_level,
        # Phase 2 (G6): Sub-scores
        sub_scores=weighted_sub.as_dict(),
        # Phase 1 (G3): Canonical official sources
        official_sources=canonical_official_sources,
        # Phase 1 (G4): Actionable advice
        actionable_advice=actionable_advice,
        # Extracted entities
        extracted_sender=extracted_entities.get('sender'),
        extracted_numbers=extracted_entities.get('phone_numbers'),
        extracted_urls=extracted_entities.get('urls'),
        extracted_institutions=extracted_entities.get('institution_names'),
        # Verification details
        summary=summary,
        evidence_sources=unique_sources,
        # Channel verification results
        sender_verified=channel_verification.get('sender_verified'),
        channel_verified=channel_verification.get('channel_verified'),
        # User guidance
        recommended_actions=recommended_actions,
        # Methodology
        methodology=methodology,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "id": log_entry.id,
        "query": full_query,
        # Phase 1 (G1): Canonical verdict — primary field
        "canonical_verdict": canonical_verdict,
        # Phase 2 (G6): Weighted sub-scores
        "sub_scores": weighted_sub.as_dict(),
        # Phase 1 (G3): Canonical official sources
        "official_sources": canonical_official_sources,
        # Phase 1 (G4): Actionable advice
        "actionable_advice": actionable_advice,
        # Legacy dual verdicts (backward compat)
        "claim_verdict": claim_verdict,
        "message_authenticity_verdict": message_authenticity_verdict,
        # Legacy single verdict (backward compat)
        "verdict": verdict,
        # Phase 2 (G5): Weighted confidence score
        "confidence_score": blended_confidence,
        "risk_level": risk_level,
        "summary": summary,
        "sources": unique_sources,
        # Extended response data
        "extracted_sender": extracted_entities.get('sender'),
        "extracted_numbers": extracted_entities.get('phone_numbers'),
        "extracted_urls": extracted_entities.get('urls'),
        "extracted_institutions": extracted_entities.get('institution_names'),
        "verification_details": {
            **channel_verification,
            "image_authenticity": image_authenticity,
            "audio_transcription": audio_transcription,
        },
        "recommended_actions": recommended_actions,
        "methodology": methodology,
        "created_at": str(log_entry.created_at),
    }
