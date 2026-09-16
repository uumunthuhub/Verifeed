from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.institution import Institution, InstitutionalAlert
from app.models.verification_log import VerificationLog
from app.schemas.email import EmailVerificationRequest, EmailVerificationResponse
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
    # D3: Optional Stage 1 screening context for improved evidence calibration
    prior_screening: dict | None = None

class ScamSubmissionRequest(BaseModel):
    text: str | None = ""
    image_data: str | None = None

class VerifyResponse(BaseModel):
    id: int
    query: str
    verdict: str  # Legacy single verdict
    claim_verdict: str | None = None
    message_authenticity_verdict: str | None = None
    confidence_score: float
    risk_level: str | None = None
    summary: str
    sources: list[dict[str, Any]]
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
    if not q and not req.image_data:
        raise HTTPException(status_code=400, detail="Must provide either text query or attached file")
    
    result = await verify_claim(db, q, image_data=req.image_data, prior_screening=req.prior_screening)
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
    return logs

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

@router.post("/seed-alerts")
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

    extracted_numbers: list[str] | None = json.loads(str(log.extracted_numbers)) if isinstance(log.extracted_numbers, str) else (list(log.extracted_numbers) if log.extracted_numbers else None)  # type: ignore
    extracted_urls: list[str] | None = json.loads(str(log.extracted_urls)) if isinstance(log.extracted_urls, str) else (list(log.extracted_urls) if log.extracted_urls else None)  # type: ignore
    extracted_institutions: list[str] | None = json.loads(str(log.extracted_institutions)) if isinstance(log.extracted_institutions, str) else (list(log.extracted_institutions) if log.extracted_institutions else None)  # type: ignore
    recommended_actions: list[dict[str, Any]] | None = json.loads(str(log.recommended_actions)) if isinstance(log.recommended_actions, str) else (list(log.recommended_actions) if log.recommended_actions else None)  # type: ignore

    matched_inst = extracted_institutions[0] if extracted_institutions and len(extracted_institutions) > 0 else None
    raw_confidence = getattr(log, "confidence_score", 0.0)
    confidence_val = float(raw_confidence) if raw_confidence is not None else 0.0

    return {
        "id": log.id,  # type: ignore[arg-type]
        "query": str(log.query_text or ""),
        "verdict": str(log.verdict or ""),
        "claim_verdict": getattr(log, "claim_verdict", None),
        "message_authenticity_verdict": getattr(log, "message_authenticity_verdict", None),
        "confidence_score": confidence_val,
        "risk_level": getattr(log, "risk_level", None),
        "summary": getattr(log, "summary", ""),
        "sources": sources,
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
        "created_at": str(getattr(log, "created_at", "")),
    }
