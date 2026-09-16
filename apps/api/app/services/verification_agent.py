import json
import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.institution import Institution, InstitutionalAlert
from app.models.source import Source
from app.models.verification_log import VerificationLog
from app.services.ai import get_ai_service
from app.services.channel_verification import verify_official_channels
from app.services.entity_extraction import extract_entities_from_text
from app.services.evidence_ranker import EvidenceRanker
from app.services.fact_check import search_google_fact_check

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


def extract_significant_keywords(text: str) -> list[str]:
    """Extract words longer than 3 characters for fallback keyword search."""
    if not text:
        return []
    words = [w.strip(",.!?\"'").lower() for w in text.split()]
    stopwords = {"with", "from", "that", "this", "have", "offer", "offering", "your", "free", "more"}
    return [w for w in words if len(w) >= 4 and w not in stopwords]


def extract_text_from_image_data(image_data: str) -> str:
    """Extract OCR text and claims from base64 image data via the AI service."""
    return get_ai_service().extract_from_image(image_data, OCR_PROMPT)


async def verify_claim(
    db: Session,
    query: str,
    image_data: str | None = None,
    prior_screening: dict | None = None,
) -> dict[str, Any]:
    """
    Perform multi-stage RAG claim verification with dual verdict system.

    Args:
        db: SQLAlchemy session.
        query: The claim text or message to verify.
        image_data: Optional base64-encoded image for OCR extraction.
        prior_screening: Optional Stage 1 ScreeningResult dict — when provided,
            the risk level and detected signals are threaded into the evidence
            ranker and the Gemini synthesis prompt for better calibration.

    Flow per updated Architecture (§78.3):
        INPUT → EXTRACT → VERIFY IDENTITIES → EVIDENCE → RANK EVIDENCE →
        VERIFICATION ENGINE → DUAL VERDICTS → GUIDANCE
    """
    ai = get_ai_service()

    ocr_text = ""
    if image_data:
        ocr_text = extract_text_from_image_data(image_data)
        logger.info("Extracted OCR text from uploaded file: %s", ocr_text[:200])

    full_query = f"{query} {ocr_text}".strip() or "Unspecified claim"
    
    # NEW: Extract entities from message
    extracted_entities = extract_entities_from_text(full_query, use_ai=False)
    logger.info("Extracted entities: %s", extracted_entities)
    
    # NEW: Verify official channels
    channel_verification = verify_official_channels(extracted_entities, db)
    logger.info("Channel verification result: %s", channel_verification)
    
    query_vector = get_query_embedding(full_query)
    keywords = extract_significant_keywords(full_query)

    evidence_sources: list[dict[str, str]] = []
    institutional_matches: list[dict[str, str]] = []

    # 1. Institutional Fraud Alert search — vector then keyword fallback
    if query_vector:
        try:
            alerts = (
                db.query(InstitutionalAlert, Institution)
                .join(Institution)
                .order_by(InstitutionalAlert.embedding.l2_distance(query_vector))
                .limit(3)
                .all()
            )
            for alert, inst in alerts:
                institutional_matches.append({
                    "institution": inst.name,
                    "title": alert.title,
                    "alert_text": alert.alert_text,
                    "url": alert.source_url,
                    "published_date": str(alert.published_date),
                })
                evidence_sources.append({
                    "title": f"Official Alert: {alert.title}",
                    "outlet": inst.name,
                    "url": alert.source_url,
                    "type": "Official Institutional Alert",
                })
        except Exception as exc:
            logger.error("Error searching institutional alerts: %s", exc)

    if not institutional_matches and keywords:
        alert_filters = (
            [InstitutionalAlert.title.ilike(f"%{kw}%") for kw in keywords]
            + [InstitutionalAlert.alert_text.ilike(f"%{kw}%") for kw in keywords]
            + [Institution.name.ilike(f"%{kw}%") for kw in keywords]
        )
        kw_alerts = (
            db.query(InstitutionalAlert, Institution)
            .join(Institution)
            .filter(or_(*alert_filters))
            .limit(3)
            .all()
        )
        for alert, inst in kw_alerts:
            institutional_matches.append({
                "institution": inst.name,
                "title": alert.title,
                "alert_text": alert.alert_text,
                "url": alert.source_url,
            })
            evidence_sources.append({
                "title": f"Official Alert: {alert.title}",
                "outlet": inst.name,
                "url": alert.source_url,
                "type": "Official Institutional Alert",
            })

    # 2. Indexed News Article search — vector then keyword fallback
    articles_retrieved: list[dict[str, str]] = []
    if query_vector:
        try:
            matched = (
                db.query(Article, Source)
                .join(Source)
                .order_by(Article.embedding.l2_distance(query_vector))
                .limit(5)
                .all()
            )
            for art, src in matched:
                articles_retrieved.append({
                    "headline": art.headline,
                    "outlet": src.name,
                    "url": art.url,
                    "published_date": str(art.published_at) if art.published_at else "",
                })
                evidence_sources.append({
                    "title": art.headline,
                    "outlet": src.name,
                    "url": art.url,
                    "type": "News Article",
                })
        except Exception as exc:
            logger.error("Error searching article vector index: %s", exc)

    if not articles_retrieved and keywords:
        art_filters = [Article.headline.ilike(f"%{kw}%") for kw in keywords]
        kw_arts = (
            db.query(Article, Source)
            .join(Source)
            .filter(or_(*art_filters))
            .limit(5)
            .all()
        )
        for art, src in kw_arts:
            articles_retrieved.append({
                "headline": art.headline,
                "outlet": src.name,
                "url": art.url,
            })
            evidence_sources.append({
                "title": art.headline,
                "outlet": src.name,
                "url": art.url,
                "type": "News Article",
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

    # NEW: Determine dual verdicts based on evidence and channel verification
    claim_verdict = None
    message_authenticity_verdict = None
    risk_level = "Low"
    recommended_actions = []
    
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
        risk_level = "Medium"
    
    # Claim Verdict (based on evidence)
    if institutional_matches:
        claim_verdict = "False"
        risk_level = "High"
        if not any(action['priority'] == 'critical' for action in recommended_actions):
            recommended_actions.append({
                "action": "Do not act on this message - official scam alert exists",
                "priority": "critical",
                "reason": "Official institutional alerts identify this as fraudulent"
            })
    elif articles_retrieved and len(articles_retrieved) >= 2:
        claim_verdict = "True"
    elif fact_check_results:
        # Check fact check ratings
        fc_ratings = [fc.get('rating', '').lower() for fc in fact_check_results]
        if any('false' in r or 'scam' in r for r in fc_ratings):
            claim_verdict = "False"
            risk_level = "High"
        elif any('true' in r or 'accurate' in r for r in fc_ratings):
            claim_verdict = "True"
        else:
            claim_verdict = "Misleading"
            risk_level = "Medium"
    else:
        claim_verdict = "Insufficient Evidence"
    
    # Legacy single verdict for backward compatibility
    verdict = "No Coverage Found"
    if institutional_matches:
        verdict = "Confirmed Scam"
    elif claim_verdict == "True":
        verdict = "Confirmed"
    elif claim_verdict == "False":
        verdict = "Disputed / False"
    elif claim_verdict == "Misleading":
        verdict = "Unconfirmed"
    
    # Add default recommended actions if none set
    if not recommended_actions:
        if risk_level == "High":
            recommended_actions = [
                {
                    "action": "Do not send money or share personal information",
                    "priority": "critical",
                    "reason": "High-risk message detected"
                },
                {
                    "action": "Contact the institution using official channels",
                    "priority": "high",
                    "reason": "Always verify through official communication channels"
                }
            ]
        else:
            recommended_actions = [
                {
                    "action": "Verify the information independently",
                    "priority": "medium",
                    "reason": "Standard verification precaution"
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

    # 4. AI Synthesis — via the provider boundary (not direct SDK calls)
    # Use ranker confidence as starting point; Gemini may refine it
    confidence = ranking.confidence_score
    summary = "No matching news articles, institutional alerts, or fact-check records were found for this claim."

    if institutional_matches:
        confidence = 0.95
        inst_names = ", ".join(sorted({m["institution"] for m in institutional_matches}))
        alert_details = [f"{m['institution']} ('{m['title']}'): {m['alert_text']}" for m in institutional_matches]
        summary = (
            f"Official scam alerts have been issued by {inst_names}. "
            + " ".join(alert_details)
        )

    has_evidence = institutional_matches or articles_retrieved or fact_check_results or ocr_text
    if has_evidence:
        # Build prior_screening context block for Gemini prompt
        prior_context = ""
        if prior_screening:
            prior_context = f"""
STAGE 1 LOCAL SCREENING RESULT (pre-Gemini):
  risk_level: {prior_screening.get('risk_level', 'Unknown')}
  signals: {prior_screening.get('signals', [])}
  recommended_action: {prior_screening.get('recommended_action', '')}
"""

        synthesis_prompt = f"""
You are the VeriFeed AI Fact-Checking Agent. Analyze the following claim using ONLY the provided evidence context. Do not invent or assume outside facts.

CLAIM TO VERIFY:
"{full_query}"
{prior_context}
EXTRACTED ENTITIES:
{json.dumps(extracted_entities, indent=2)}

CHANNEL VERIFICATION:
{json.dumps(channel_verification, indent=2)}

RANKED EVIDENCE SOURCES (highest credibility first):
{json.dumps([{"title": s.title, "outlet": s.outlet, "type": s.source_type, "tier": s.tier_score} for s in ranking.ranked_sources[:5]], indent=2)}

RETRIEVED INSTITUTIONAL ALERTS (Official scam denials):
{json.dumps(institutional_matches, indent=2)}

RETRIEVED NEWS ARTICLES:
{json.dumps(articles_retrieved, indent=2)}

RETRIEVED FACT CHECK RATINGS:
{json.dumps(fact_check_results, indent=2)}

INSTRUCTIONS:
Select EXACTLY ONE verdict from the following allowed values:
1. "Confirmed Scam" -> ONLY if an official institutional alert/disclaimer or fact-checker explicitly identifies this as a scam.
2. "Confirmed" -> If multiple reputable news outlets report this claim as true/accurate.
3. "Unconfirmed" -> If reported by only 1 source or unverified outlets without corroboration.
4. "Disputed / False" -> Contradicted by news articles or fact-checkers.
5. "No Coverage Found" -> If no relevant evidence was retrieved.

SUMMARY SYNTHESIS REQUIREMENTS:
- Provide a clear, actionable, and informative 2-4 sentence summary.
- Synthesize the specific facts, warning details (e.g., specific phishing tactics, fake apps, or fraudulent loan promises), and official advice from the retrieved evidence.
- CRITICAL: DO NOT write generic responses like "Found 2 official alerts from Airtel Money. Please review cited sources below." Instead, summarize WHAT the alerts say and WHY the user should be cautious, eliminating extra work for the user.

Return a JSON object strictly matching this format:
{{
  "verdict": "<one of the 5 allowed verdicts>",
  "confidence_score": <float between 0.0 and 1.0>,
  "summary": "<comprehensive 2-4 sentence explanation detailing the core facts and warnings>"
}}
"""
        parsed = ai.generate_json(synthesis_prompt)
        if parsed:
            verdict = parsed.get("verdict", verdict)
            # Blend Gemini confidence with ranker confidence (ranker is calibrated,
            # Gemini may over/underestimate)
            gemini_confidence = float(parsed.get("confidence_score", confidence))
            confidence = round((ranking.confidence_score * 0.6 + gemini_confidence * 0.4), 3)
            parsed_summary = parsed.get("summary", "")
            if parsed_summary and len(parsed_summary) > 20:
                summary = parsed_summary
        else:
            logger.warning("AI synthesis returned no result — using heuristic verdict.")

    # Deduplicate evidence sources (use ranked_sources as the primary list)
    # ranked_sources is already deduplicated by the EvidenceRanker
    unique_sources = ranked_sources if ranked_sources else evidence_sources[:10]

    # 5. Persist verification log with dual verdict system
    log_entry = VerificationLog(
        query_text=full_query,
        # NEW: Dual verdict system
        claim_verdict=claim_verdict,
        message_authenticity_verdict=message_authenticity_verdict,
        # Legacy single verdict for backward compatibility
        verdict=verdict,
        confidence_score=confidence,
        risk_level=risk_level,
        # NEW: Extracted entities
        extracted_sender=extracted_entities.get('sender'),
        extracted_numbers=extracted_entities.get('phone_numbers'),
        extracted_urls=extracted_entities.get('urls'),
        extracted_institutions=extracted_entities.get('institution_names'),
        # Verification details
        summary=summary,
        evidence_sources=unique_sources,
        # NEW: Channel verification results
        sender_verified=channel_verification.get('sender_verified'),
        channel_verified=channel_verification.get('channel_verified'),
        # NEW: User guidance
        recommended_actions=recommended_actions,
        # D2: Methodology
        methodology=methodology,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "id": log_entry.id,
        "query": full_query,
        # NEW: Dual verdicts
        "claim_verdict": claim_verdict,
        "message_authenticity_verdict": message_authenticity_verdict,
        # Legacy single verdict
        "verdict": verdict,
        "confidence_score": confidence,
        "risk_level": risk_level,
        "summary": summary,
        "sources": unique_sources,
        # NEW: Extended response data
        "extracted_sender": extracted_entities.get('sender'),
        "extracted_numbers": extracted_entities.get('phone_numbers'),
        "extracted_urls": extracted_entities.get('urls'),
        "extracted_institutions": extracted_entities.get('institution_names'),
        "verification_details": channel_verification,
        "recommended_actions": recommended_actions,
        # D2: Methodology
        "methodology": methodology,
        "created_at": str(log_entry.created_at),
    }
