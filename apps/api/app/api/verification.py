from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.admin import require_ingestion_admin
from app.db.session import get_db
from app.models.institution import Institution, InstitutionalAlert
from app.models.verification_log import CanonicalVerdict, VerificationLog
from app.schemas.email import EmailVerificationRequest, EmailVerificationResponse
from app.services.ai import get_ai_service
from app.services.email_screener import EmailScreener
from app.services.fraud_detector import process_user_submission
from app.services.ingestion import get_embedding
from app.services.verification_agent import verify_claim

router = APIRouter()
email_screener_instance = EmailScreener()

class VerifyRequest(BaseModel):
    query: str | None = ""
    image_data: str | None = None
    file_name: str | None = None
    audio_data: str | None = None
    audio_name: str | None = None
    # D3: Optional Stage 1 screening context for improved evidence calibration
    prior_screening: dict | None = None

class ScamSubmissionRequest(BaseModel):
    text: str | None = ""
    image_data: str | None = None

class VerifyResponse(BaseModel):
    id: int
    query: str
    canonical_verdict: str | None = None
    verdict: str  # Legacy single verdict
    claim_verdict: str | None = None
    message_authenticity_verdict: str | None = None
    confidence_score: float
    sub_scores: dict[str, float] | None = None
    risk_level: str | None = None
    summary: str
    sources: list[dict[str, Any]] = []
    official_sources: list[dict[str, Any]] = []
    actionable_advice: str | None = None
    extracted_sender: str | None = None
    extracted_numbers: list[str] | None = None
    extracted_urls: list[str] | None = None
    extracted_institutions: list[str] | None = None
    verification_details: dict[str, Any] | None = None
    recommended_actions: list[dict[str, Any]] | None = None
    # D2: Evidence pipeline methodology
    methodology: str | None = None
    created_at: str

@router.post("/", response_model=VerifyResponse)
async def verify_claim_endpoint(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Stage 2: Full evidence-pipeline verification with Gemini AI synthesis.

    Accepts an optional `prior_screening` dict from Stage 1 local screening
    to improve confidence calibration and evidence ranking.
    """
    q = (req.query or "").strip()
    if not q and not req.image_data and not req.audio_data:
        raise HTTPException(status_code=400, detail="Must provide either text query, attached image, or audio file")
    
    result = await verify_claim(
        db,
        q,
        image_data=req.image_data,
        audio_data=req.audio_data,
        prior_screening=req.prior_screening,
    )
    return result

@router.post("/submit-scam")
async def submit_scam_endpoint(req: ScamSubmissionRequest, db: Session = Depends(get_db)):
    """
    Submit a suspicious SMS, social post, or scam message for community tracking.
    """
    extracted_text = ""
    if req.image_data:
        from app.services.verification_agent import extract_text_from_image_data
        extracted_text = extract_text_from_image_data(req.image_data)
    
    final_text = f"{(req.text or '')} {extracted_text}".strip()

    if not final_text or len(final_text) < 5:
        raise HTTPException(status_code=400, detail="Submission text (or extracted OCR text) must be at least 5 characters long")

    submission = process_user_submission(db, final_text)
    return {
        "status": "success",
        "message": "Submission recorded and clustered for fraud analysis",
        "submission_id": submission.id,
        "cluster_id": submission.cluster_id
    }


@router.post("/email", response_model=EmailVerificationResponse)
def verify_email_endpoint(req: EmailVerificationRequest, db: Session = Depends(get_db)):
    """
    Phase H: Email Phishing & Domain Spoofing Verification Endpoint.
    Analyzes sender domain mismatches, SPF/DKIM authentication, urgency lures, and links.
    """
    if not req.sender_address and not req.body_text:
        raise HTTPException(status_code=400, detail="Must provide at least sender address or email body text")

    return email_screener_instance.screen(req, db=db)

@router.get("/alerts")
def get_institutional_alerts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Fetch official institutional fraud alerts and disclaimers.
    """
    alerts = db.query(InstitutionalAlert, Institution).join(Institution).order_by(
        InstitutionalAlert.published_date.desc()
    ).offset(skip).limit(limit).all()

    results = []
    for alert, inst in alerts:
        results.append({
            "id": alert.id,
            "title": alert.title,
            "alert_text": alert.alert_text,
            "source_url": alert.source_url,
            "published_date": str(alert.published_date),
            "institution": {
                "id": inst.id,
                "name": inst.name,
                "sector": inst.sector,
                "website_url": inst.website_url
            }
        })
    return results

@router.get("/recent")
def get_recent_verifications(limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch recent public claim checks for community visibility.
    """
    logs = db.query(VerificationLog).order_by(VerificationLog.created_at.desc()).limit(limit).all()
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "query": log.query_text,
            "canonical_verdict": log.canonical_verdict,
            "claim_verdict": log.claim_verdict,
            "message_authenticity_verdict": log.message_authenticity_verdict,
            "verdict": log.verdict,
            "confidence_score": log.confidence_score,
            "risk_level": log.risk_level,
            "sub_scores": log.sub_scores,
            "official_sources": log.official_sources,
            "actionable_advice": log.actionable_advice,
            "extracted_sender": log.extracted_sender,
            "extracted_numbers": log.extracted_numbers,
            "extracted_urls": log.extracted_urls,
            "extracted_institutions": log.extracted_institutions,
            "summary": log.summary,
            "sources": log.evidence_sources,
            "sender_verified": log.sender_verified,
            "channel_verified": log.channel_verified,
            "recommended_actions": log.recommended_actions,
            "methodology": log.methodology,
            "created_at": str(log.created_at),
        })
    return results

@router.get("/clusters")
def get_emerging_clusters(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Fetch emerging unconfirmed scam patterns reported by users.
    """
    from app.models.submission import SubmissionCluster
    clusters = db.query(SubmissionCluster).order_by(
        SubmissionCluster.submission_count.desc(),
        SubmissionCluster.last_seen.desc()
    ).offset(skip).limit(limit).all()

    results = []
    for c in clusters:
        results.append({
            "id": c.id,
            "representative_text": c.representative_text,
            "submission_count": c.submission_count,
            "status": c.status,
            "first_seen": str(c.first_seen),
            "last_seen": str(c.last_seen)
        })
    return results

@router.post("/seed-alerts", dependencies=[Depends(require_ingestion_admin)])
def seed_institutional_alerts(db: Session = Depends(get_db)):
    """
    Seed initial bank and telecom institutional disclaimers and official channels for testing.
    """
    sample_institutions: list[dict[str, Any]] = [
        {
            "name": "Standard Bank",
            "sector": "Banking",
            "website_url": "https://www.standardbank.co.mw",
            "official_sms_sender_ids": ["StandardBank", "Standard Bank"],
            "official_phone_numbers": ["+265999222000", "+265888222000"],
            "official_email_domains": ["standardbank.co.mw"],
            "alerts": [
                {
                    "title": "SCAM ALERT: Unauthorized Online Loan Promotions",
                    "alert_text": "Standard Bank wishes to inform the public that we are NOT offering any instant online collateral-free loans via WhatsApp or SMS. Any message asking for account credentials or processing fees is fraudulent.",
                    "source_url": "https://www.standardbank.co.mw/security-alert"
                }
            ]
        },
        {
            "name": "Reserve Bank of Malawi (RBM)",
            "sector": "Regulatory",
            "website_url": "https://www.rbm.mw",
            "official_sms_sender_ids": ["RBM", "ReserveBank"],
            "official_email_domains": ["rbm.mw"],
            "alerts": [
                {
                    "title": "FRAUD WARNING: Fake Crypto Currency Investment Schemes",
                    "alert_text": "The Reserve Bank of Malawi warns the public against investing in unlicensed digital currency platforms promising guaranteed daily returns. RBM has not licensed any automated crypto trading bots.",
                    "source_url": "https://www.rbm.mw/press-release-crypto"
                }
            ]
        },
        {
            "name": "Airtel Money",
            "sector": "Telecom & Mobile Money",
            "website_url": "https://www.airtel.mw",
            "official_sms_sender_ids": ["AirtelMoney", "Airtel Money", "Airtel"],
            "official_short_codes": ["212"],
            "official_ussd_codes": ["*212#", "*211#"],
            "official_phone_numbers": ["+265999000212"],
            "official_email_domains": ["airtel.mw"],
            "alerts": [
                {
                    "title": "BEWARE: SIM Upgrade & Pin Request Fraud",
                    "alert_text": "Airtel Money will NEVER call you asking for your 4-digit secret PIN or asking you to dial code shortcuts to upgrade your SIM. Do not share your PIN with anyone.",
                    "source_url": "https://www.airtel.mw/security-tips"
                }
            ]
        },
        {
            "name": "TNM Mpamba",
            "sector": "Telecom & Mobile Money",
            "website_url": "https://www.tnm.mw",
            "official_sms_sender_ids": ["TNM", "Mpamba", "TNMMpamba"],
            "official_short_codes": ["105"],
            "official_ussd_codes": ["*105#", "*444#"],
            "official_phone_numbers": ["+265888800900"],
            "official_email_domains": ["tnm.mw"],
            "alerts": [
                {
                    "title": "NOTICE: Fraudulent Promotion SMS Messages",
                    "alert_text": "TNM Mpamba reminds customers that official promotions are only communicated via verified SMS short code 105 or *105#. Any SMS from a standard mobile number claiming you won cash is fraudulent.",
                    "source_url": "https://www.tnm.mw/security-notice"
                }
            ]
        }
    ]

    count = 0
    for inst_data in sample_institutions:
        existing = db.query(Institution).filter(Institution.name == inst_data["name"]).first()
        if not existing:
            inst = Institution(
                name=inst_data["name"],
                sector=inst_data["sector"],
                website_url=inst_data["website_url"],
                official_sms_sender_ids=inst_data.get("official_sms_sender_ids"),
                official_short_codes=inst_data.get("official_short_codes"),
                official_ussd_codes=inst_data.get("official_ussd_codes"),
                official_phone_numbers=inst_data.get("official_phone_numbers"),
                official_email_domains=inst_data.get("official_email_domains")
            )
            db.add(inst)
            db.flush()
        else:
            inst = existing
            # Update channels if missing
            if inst_data.get("official_sms_sender_ids"):
                inst.official_sms_sender_ids = inst_data.get("official_sms_sender_ids")  # type: ignore
            if inst_data.get("official_short_codes"):
                inst.official_short_codes = inst_data.get("official_short_codes")  # type: ignore
            if inst_data.get("official_ussd_codes"):
                inst.official_ussd_codes = inst_data.get("official_ussd_codes")  # type: ignore
            if inst_data.get("official_phone_numbers"):
                inst.official_phone_numbers = inst_data.get("official_phone_numbers")  # type: ignore
            if inst_data.get("official_email_domains"):
                inst.official_email_domains = inst_data.get("official_email_domains")  # type: ignore

        for alert_data in inst_data["alerts"]:
            existing_alert = db.query(InstitutionalAlert).filter(
                InstitutionalAlert.title == alert_data["title"]
            ).first()
            if not existing_alert:
                emb = get_embedding(alert_data["title"] + " " + alert_data["alert_text"])
                alert = InstitutionalAlert(
                    institution_id=inst.id,
                    title=alert_data["title"],
                    alert_text=alert_data["alert_text"],
                    source_url=alert_data["source_url"],
                    embedding=emb
                )
                db.add(alert)
                count += 1

    db.commit()
    return {"status": "success", "alerts_created": count}


class ReportAskMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ReportAskRequest(BaseModel):
    question: str
    history: list[ReportAskMessage] | None = None


class ReportAskResponse(BaseModel):
    answer: str
    suggested_followups: list[str]


@router.post("/{log_id}/ask", response_model=ReportAskResponse)
def ask_report_question_endpoint(log_id: int, req: ReportAskRequest, db: Session = Depends(get_db)):
    """
    Interactive Q&A on a specific Verification Report.
    Answers follow-up questions in the context of the report and VeriFeed project guidelines.
    """
    q = (req.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    log = db.query(VerificationLog).filter(VerificationLog.id == log_id).first()

    # Context building
    query_text = log.query_text if log else "Unspecified message/claim"
    verdict = getattr(log, "verdict", "Unconfirmed") if log else "Unconfirmed"
    risk_level = getattr(log, "risk_level", "Medium") if log else "Medium"
    confidence = getattr(log, "confidence_score", 0.8) if log else 0.8
    summary = getattr(log, "summary", "Verification report details") if log else "Verification report details"
    actions = getattr(log, "recommended_actions", []) if log else []
    sender = getattr(log, "extracted_sender", None) if log else None
    institutions = getattr(log, "extracted_institutions", None) if log else None
    numbers = getattr(log, "extracted_numbers", None) if log else None
    urls = getattr(log, "extracted_urls", None) if log else None

    # Format history
    history_str = ""
    if req.history:
        formatted = []
        for msg in req.history:
            role_label = "User" if msg.role == "user" else "VeriFeed AI"
            formatted.append(f"{role_label}: {msg.content}")
        history_str = "\n".join(formatted)

    ai = get_ai_service()
    prompt = f"""You are the VeriFeed AI Assistant — an interactive fraud prevention and verification expert for Malawi and global context.
The user is reviewing a specific Verification Report (Report ID #{log_id}) and asking a follow-up question.

REPORT CONTEXT:
- Message / Claim Analyzed: "{query_text}"
- Overall Verdict: {verdict}
- Risk Level: {risk_level}
- Confidence Score: {confidence}
- Verification Summary: {summary}
- Extracted Sender: {sender or 'None'}
- Detected Institutions: {institutions or 'None'}
- Phone Numbers: {numbers or 'None'}
- URLs: {urls or 'None'}
- Recommended Actions: {actions}

{f"PREVIOUS DIALOGUE:\n{history_str}\n" if history_str else ""}

USER'S FOLLOW-UP QUESTION:
"{q}"

DIRECTIVES:
1. Provide a direct, empathetic, and interactive answer grounded in the report details and general VeriFeed verification guidelines.
2. If the user asks for action steps (e.g. what to do, who to contact), list clear, practical steps (e.g., verifying with official customer support lines, not clicking unknown links, reporting scam numbers).
3. Keep the tone professional, reassuring, and clear.
4. Do not invent fake facts or external evidence not related to the institution or report context.

Response:"""

    answer = ai.generate(prompt)

    if not answer:
        # Fallback response grounded in report context if AI service is offline or degraded
        if risk_level == "High":
            answer = (
                f"Based on Report #{log_id}, this message is categorized as High Risk ({verdict}). "
                f"We strongly advise you NOT to send money, share passwords, or dial codes requested in the message. "
                f"To verify independently, contact the institution through official channels or visit a physical branch."
            )
        else:
            answer = (
                f"Regarding your question about Report #{log_id}: VeriFeed recommends exercising caution. "
                f"The analyzed content has a risk rating of {risk_level}. Always double-check sender numbers and "
                f"official domain handles before sharing personal or financial information."
            )

    # Dynamic contextual follow-up suggestions based on report risk and context
    if risk_level == "High":
        suggested = [
            "What specific red flags were found in this message?",
            "How can I report this suspicious sender to authorities?",
            "What should I do if I already clicked the link or provided details?",
        ]
    else:
        suggested = [
            "What official news sources report on this claim?",
            "How can I confirm this announcement with official channels?",
            "What are the latest verified updates regarding this topic?",
        ]

    return {
        "answer": answer,
        "suggested_followups": suggested
    }


@router.get("/{log_id}", response_model=VerifyResponse)
def get_verification_by_id(log_id: int, db: Session = Depends(get_db)):
    """
    Fetch a single verification log by its ID.
    """
    log = db.query(VerificationLog).filter(VerificationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    import json
    sources: list[dict[str, Any]] = []
    if log.evidence_sources:
        sources = json.loads(str(log.evidence_sources)) if isinstance(log.evidence_sources, str) else list(log.evidence_sources)  # type: ignore

    official_sources: list[dict[str, Any]] = []
    if getattr(log, "official_sources", None):
        raw_off = log.official_sources
        official_sources = json.loads(str(raw_off)) if isinstance(raw_off, str) else list(raw_off)  # type: ignore

    sub_scores: dict[str, float] | None = None
    if getattr(log, "sub_scores", None):
        raw_sub = log.sub_scores
        sub_scores = json.loads(str(raw_sub)) if isinstance(raw_sub, str) else dict(raw_sub)  # type: ignore

    extracted_numbers: list[str] | None = json.loads(str(log.extracted_numbers)) if isinstance(log.extracted_numbers, str) else (list(log.extracted_numbers) if log.extracted_numbers else None)  # type: ignore
    extracted_urls: list[str] | None = json.loads(str(log.extracted_urls)) if isinstance(log.extracted_urls, str) else (list(log.extracted_urls) if log.extracted_urls else None)  # type: ignore
    extracted_institutions: list[str] | None = json.loads(str(log.extracted_institutions)) if isinstance(log.extracted_institutions, str) else (list(log.extracted_institutions) if log.extracted_institutions else None)  # type: ignore
    recommended_actions: list[dict[str, Any]] | None = json.loads(str(log.recommended_actions)) if isinstance(log.recommended_actions, str) else (list(log.recommended_actions) if log.recommended_actions else None)  # type: ignore

    matched_inst = extracted_institutions[0] if extracted_institutions and len(extracted_institutions) > 0 else None
    raw_confidence = getattr(log, "confidence_score", 0.0)
    confidence_val = float(raw_confidence) if raw_confidence is not None else 0.0

    canonical = getattr(log, "canonical_verdict", None) or (
        CanonicalVerdict.from_legacy(str(log.verdict)) if log.verdict else "UNVERIFIED"
    )

    return {
        "id": log.id,  # type: ignore[arg-type]
        "query": str(log.query_text or ""),
        "canonical_verdict": canonical,
        "verdict": str(log.verdict or ""),
        "claim_verdict": getattr(log, "claim_verdict", None),
        "message_authenticity_verdict": getattr(log, "message_authenticity_verdict", None),
        "confidence_score": confidence_val,
        "sub_scores": sub_scores,
        "risk_level": getattr(log, "risk_level", None),
        "summary": getattr(log, "summary", ""),
        "sources": sources,
        "official_sources": official_sources,
        "actionable_advice": getattr(log, "actionable_advice", None),
        "extracted_sender": getattr(log, "extracted_sender", None),
        "extracted_numbers": extracted_numbers,
        "extracted_urls": extracted_urls,
        "extracted_institutions": extracted_institutions,
        "verification_details": {
            "sender_verified": bool(getattr(log, "sender_verified", False)),
            "channel_verified": bool(getattr(log, "channel_verified", False)),
            "matched_institution": matched_inst,
        },
        "recommended_actions": recommended_actions,
        "methodology": getattr(log, "methodology", None),
        "created_at": str(getattr(log, "created_at", "")),
    }
