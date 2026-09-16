from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.institution import Institution, InstitutionalAlert
from app.services.ai import get_ai_service

router = APIRouter()


class InstitutionResponse(BaseModel):
    id: int
    name: str
    sector: str
    website_url: str | None = None
    alert_count: int = 0


class InstitutionalAlertResponse(BaseModel):
    id: int
    institution_name: str
    sector: str
    title: str
    alert_text: str
    source_url: str | None = None
    published_date: str


class ScamSubmissionRequest(BaseModel):
    submitted_text: str
    contact_info: str | None = None


class SubmissionClusterResponse(BaseModel):
    id: int
    representative_text: str
    submission_count: int
    status: str
    first_seen: str
    last_seen: str


@router.get("/", response_model=list[InstitutionResponse])
def list_institutions(db: Session = Depends(get_db)):
    """List all registered verified institutions and alert counts."""
    institutions = db.query(Institution).all()
    results = []
    for inst in institutions:
        alert_count = db.query(InstitutionalAlert).filter(InstitutionalAlert.institution_id == inst.id).count()
        results.append({
            "id": inst.id,
            "name": inst.name,
            "sector": inst.sector,
            "website_url": inst.website_url,
            "alert_count": alert_count,
        })
    return results


@router.post("/submissions")
def create_submission(payload: ScamSubmissionRequest, db: Session = Depends(get_db)):
    """Submit a suspicious message/claim for fraud analysis and clustering."""
    from app.services.fraud_detector import process_user_submission
    submission = process_user_submission(db, payload.submitted_text)
    return {
        "status": "success",
        "submission_id": submission.id,
        "cluster_id": submission.cluster_id,
        "extracted_entities": submission.extracted_entities,
    }


@router.get("/clusters", response_model=list[SubmissionClusterResponse])
def list_clusters(db: Session = Depends(get_db)):
    """Fetch emerging scam report clusters."""
    from app.models.submission import SubmissionCluster
    clusters = db.query(SubmissionCluster).order_by(SubmissionCluster.submission_count.desc()).limit(10).all()
    results = []
    for c in clusters:
        results.append({
            "id": c.id,
            "representative_text": c.representative_text,
            "submission_count": c.submission_count,
            "status": c.status,
            "first_seen": str(c.first_seen),
            "last_seen": str(c.last_seen),
        })
    return results


@router.get("/alerts", response_model=list[InstitutionalAlertResponse])
def list_alerts(skip: int = 0, limit: int = 20, sector: str | None = None, db: Session = Depends(get_db)):
    """Fetch official institutional fraud alerts with optional sector filtering."""
    query = db.query(InstitutionalAlert, Institution).join(Institution)
    if sector:
        query = query.filter(Institution.sector.ilike(f"%{sector}%"))

    alerts = query.order_by(InstitutionalAlert.published_date.desc()).offset(skip).limit(limit).all()

    results = []
    for alert, inst in alerts:
        results.append({
            "id": alert.id,
            "institution_name": inst.name,
            "sector": inst.sector,
            "title": alert.title,
            "alert_text": alert.alert_text,
            "source_url": alert.source_url,
            "published_date": str(alert.published_date),
        })
    return results


SEED_INSTITUTIONS: list[dict[str, Any]] = [
    {
        "name": "Standard Bank Malawi",
        "sector": "Banking",
        "website_url": "https://www.standardbank.co.mw",
        "alerts": [
            {
                "title": "SCAM ALERT: Unauthorized Online Collateral-Free Loans",
                "alert_text": "Standard Bank wishes to inform the public that we are NOT offering any instant online collateral-free loans via WhatsApp or SMS. Any message asking for account credentials or processing fees is fraudulent.",
                "source_url": "https://www.standardbank.co.mw/security-alert",
            },
            {
                "title": "BEWARE: Phishing Emails Claiming Account Suspension",
                "alert_text": "Standard Bank will never request customer online banking passwords, OTPs, or CVVs via email or phone call. Always check the official website address before logging in.",
                "source_url": "https://www.standardbank.co.mw/phishing-notice",
            },
        ],
    },
    {
        "name": "National Bank of Malawi (NBM)",
        "sector": "Banking",
        "website_url": "https://www.natbank.co.mw",
        "alerts": [
            {
                "title": "FRAUD WARNING: Fake Mo626 Digital App Upgrades",
                "alert_text": "National Bank of Malawi warns clients against downloading Mo626 app files from third-party websites or Telegram channels. Download Mo626 ice only from Google Play Store or Apple App Store.",
                "source_url": "https://www.natbank.co.mw/security",
            }
        ],
    },
    {
        "name": "FDH Bank Plc",
        "sector": "Banking",
        "website_url": "https://www.fdh.co.mw",
        "alerts": [
            {
                "title": "ALERT: Fake Social Media FDH Kanyimbi Loan Ads",
                "alert_text": "FDH Bank advises the public that fake Facebook pages impersonating FDH Bank are soliciting fee deposits for quick loan approvals. FDH Bank does not charge upfront processing fees into personal mobile money accounts.",
                "source_url": "https://www.fdh.co.mw/notice",
            }
        ],
    },
    {
        "name": "First Capital Bank Malawi",
        "sector": "Banking",
        "website_url": "https://firstcapitalbank.co.mw",
        "alerts": [
            {
                "title": "SECURITY ALERT: Vishing Calls Asking for FirstOnline Credentials",
                "alert_text": "Fraudsters calling from local mobile numbers are posing as First Capital Bank IT staff asking customers to confirm banking passwords. Do not share credentials over phone calls.",
                "source_url": "https://firstcapitalbank.co.mw/alerts",
            }
        ],
    },
    {
        "name": "Reserve Bank of Malawi (RBM)",
        "sector": "Financial Regulatory Authority",
        "website_url": "https://www.rbm.mw",
        "alerts": [
            {
                "title": "PUBLIC WARNING: Unlicensed Investment & Pyramid Schemes",
                "alert_text": "The Reserve Bank of Malawi warns the public against investing in unlicensed digital currency and WhatsApp high-yield investment schemes promising daily percentage payouts.",
                "source_url": "https://www.rbm.mw/press-release-pyramid",
            },
            {
                "title": "CAUTION: Unlicensed Online Money Transfer Operators",
                "alert_text": "Financial entities operating without RBM authorization pose significant risk of capital loss. Verify licensed institutions on the official RBM website.",
                "source_url": "https://www.rbm.mw/licensed-entities",
            },
        ],
    },
    {
        "name": "Airtel Money Malawi",
        "sector": "Telecom & Mobile Money",
        "website_url": "https://www.airtel.mw",
        "alerts": [
            {
                "title": "BEWARE: Fake Airtel Money Promotion SMS & PIN Harvesters",
                "alert_text": "Airtel Money will NEVER call asking for your 4-digit PIN or ask you to dial *21* or transfer money to claim competition winnings. Keep your PIN private.",
                "source_url": "https://www.airtel.mw/security-tips",
            },
            {
                "title": "FRAUD ALERT: SIM Swap Fraud Prevention",
                "alert_text": "If your Airtel network signal vanishes abruptly, verify with customer service immediately to prevent unauthorized SIM replacement fraud.",
                "source_url": "https://www.airtel.mw/sim-security",
            },
        ],
    },
    {
        "name": "TNM Mpamba Mobile Money",
        "sector": "Telecom & Mobile Money",
        "website_url": "https://www.tnm.co.mw",
        "alerts": [
            {
                "title": "WARNING: Accidental Reversal SMS Scams",
                "alert_text": "Scammers send fake SMS claims of accidental Mpamba money transfers followed by phone calls demanding funds return. Always check your actual balance using *444# before transferring money.",
                "source_url": "https://www.tnm.co.mw/mpamba-safety",
            }
        ],
    },
    {
        "name": "Malawi Communications Regulatory Authority (MACRA)",
        "sector": "Telecommunications Regulatory",
        "website_url": "https://www.macra.mw",
        "alerts": [
            {
                "title": "REGULATORY NOTICE: Mandatory SIM Registration & Fake Agent Warning",
                "alert_text": "MACRA warns against unauthorized agents requesting national ID details and fee payments for SIM re-registration at unverified roadside kiosks.",
                "source_url": "https://www.macra.mw/sim-reg-notice",
            }
        ],
    },
    {
        "name": "Malawi Revenue Authority (MRA)",
        "sector": "Government & Taxation",
        "website_url": "https://www.mra.mw",
        "alerts": [
            {
                "title": "PUBLIC NOTICE: Fraudulent MRA Recruitment & Customs Clearance Scams",
                "alert_text": "MRA does not charge job application fees or accept vehicle customs duty payments into personal mobile money accounts. Official payments must strictly be made at MRA offices or partner bank accounts.",
                "source_url": "https://www.mra.mw/public-notices",
            }
        ],
    },
    {
        "name": "Electricity Supply Corporation of Malawi (ESCOM)",
        "sector": "Public Utility",
        "website_url": "https://www.escom.mw",
        "alerts": [
            {
                "title": "ALERT: Fake Prepaid Token Resellers & Social Media Discounts",
                "alert_text": "ESCOM prepaid electricity tokens can only be purchased via authorized banks, mobile money operators, or official service centers. Token resellers claiming 50% discounts on WhatsApp are fraudulent.",
                "source_url": "https://www.escom.mw/notices",
            }
        ],
    },
    {
        "name": "Lilongwe Water Board (LWB)",
        "sector": "Public Utility",
        "website_url": "https://www.lwb.mw",
        "alerts": [
            {
                "title": "CAUTION: Fake Water Meter Connection Inspection Fee Calls",
                "alert_text": "LWB field staff carry official photo identification and never collect cash payments directly at customer residential premises.",
                "source_url": "https://www.lwb.mw/alerts",
            }
        ],
    },
    {
        "name": "Anti-Corruption Bureau (ACB)",
        "sector": "Law Enforcement & Integrity",
        "website_url": "https://acb.mw",
        "alerts": [
            {
                "title": "WARNING: Impersonation of ACB Investigators",
                "alert_text": "Individuals claiming to be ACB officers demanding payments to clear suspects of corruption allegations are fraudsters. Report such calls directly to ACB hotlines.",
                "source_url": "https://acb.mw/notices",
            }
        ],
    },
    {
        "name": "Ministry of Health Malawi",
        "sector": "Government & Public Health",
        "website_url": "https://www.health.gov.mw",
        "alerts": [
            {
                "title": "PUBLIC NOTICE: Fake Nursing & Medical Trainee Recruitment Schemes",
                "alert_text": "The Ministry of Health does not charge application fees for government nursing college admissions via Airtel Money or Mpamba.",
                "source_url": "https://www.health.gov.mw/press-releases",
            }
        ],
    },
    {
        "name": "MyBucks Banking Corporation",
        "sector": "Banking",
        "website_url": "https://www.mybucks.mw",
        "alerts": [
            {
                "title": "ALERT: Unauthorized Agent Banking Fee Solicitations",
                "alert_text": "MyBucks cautions customers to conduct agency transactions exclusively with certified agents displaying official MyBucks signage.",
                "source_url": "https://www.mybucks.mw/alerts",
            }
        ],
    },
    {
        "name": "CDH Investment Bank",
        "sector": "Investment Banking",
        "website_url": "https://www.cdhbank.com",
        "alerts": [
            {
                "title": "BEWARE: Fraudulent Treasury Bill & Bond Brokerage Offers",
                "alert_text": "CDH Investment Bank executes sovereign bond trades strictly through official bank channels. Report unauthorized investment solicitation messages.",
                "source_url": "https://www.cdhbank.com/security",
            }
        ],
    },
    {
        "name": "Malawi Stock Exchange (MSE)",
        "sector": "Capital Markets",
        "website_url": "https://www.mse.co.mw",
        "alerts": [
            {
                "title": "WARNING: Unauthorized Stock Brokerage & Investment Offers",
                "alert_text": "Only MSE-licensed stockbrokers are authorized to trade on the Malawi Stock Exchange. Verify licensed brokers at mse.co.mw before investing.",
                "source_url": "https://www.mse.co.mw/notices",
            }
        ],
    },
    {
        "name": "NBS Bank Plc",
        "sector": "Banking",
        "website_url": "https://www.nbs.mw",
        "alerts": [
            {
                "title": "ALERT: Fake NBS Loan Offers on WhatsApp",
                "alert_text": "NBS Bank does not solicit loan applications via WhatsApp, Telegram, or social media. All loan applications are processed through official NBS branches or the NBS digital banking platform.",
                "source_url": "https://www.nbs.mw/security-alerts",
            }
        ],
    },
    {
        "name": "Ecobank Malawi",
        "sector": "Banking",
        "website_url": "https://www.ecobank.com/mw",
        "alerts": [
            {
                "title": "FRAUD ALERT: Fake Ecobank Mobile App Promotions",
                "alert_text": "Ecobank Malawi does not run promotional campaigns requiring customers to share OTPs, PINs, or passwords. Download the Ecobank Mobile app only from official app stores.",
                "source_url": "https://www.ecobank.com/mw/security",
            }
        ],
    },
    {
        "name": "Ministry of Finance and Economic Affairs",
        "sector": "Government & Finance",
        "website_url": "https://www.finance.gov.mw",
        "alerts": [
            {
                "title": "PUBLIC NOTICE: Fraudulent Government Contract & Tender Scams",
                "alert_text": "The Ministry of Finance does not charge fees for government tender applications. All public procurements are published via the Office of the Director of Public Procurement (ODPP).",
                "source_url": "https://www.finance.gov.mw/public-notices",
            }
        ],
    },
    {
        "name": "Ministry of Education, Science and Technology",
        "sector": "Government & Education",
        "website_url": "https://www.education.gov.mw",
        "alerts": [
            {
                "title": "WARNING: Fake University Admission Letters & Scholarship Scams",
                "alert_text": "The Ministry of Education warns against fraudulent university admission letters and scholarship offers requiring upfront payments. Verify admissions directly with the respective university.",
                "source_url": "https://www.education.gov.mw/press-releases",
            }
        ],
    },
    {
        "name": "Malawi National Examinations Board (MANEB)",
        "sector": "Government & Education",
        "website_url": "https://www.maneb.edu.mw",
        "alerts": [
            {
                "title": "ALERT: Fake MSCE & JCE Results Portals and SMS Scams",
                "alert_text": "MANEB results are only available at www.maneb.edu.mw. Any SMS or website requesting payment to access or alter exam results is fraudulent.",
                "source_url": "https://www.maneb.edu.mw/public-notices",
            }
        ],
    },
    {
        "name": "University of Malawi (UNIMA)",
        "sector": "Higher Education",
        "website_url": "https://www.unima.mw",
        "alerts": [
            {
                "title": "NOTICE: Fraudulent UNIMA Admission & Hostel Booking Scams",
                "alert_text": "The University of Malawi does not collect admission fees via mobile money to personal accounts. All payments must go through official university bank accounts.",
                "source_url": "https://www.unima.mw/notices",
            }
        ],
    },
    {
        "name": "Mzuzu University (MZUNI)",
        "sector": "Higher Education",
        "website_url": "https://www.mzuni.ac.mw",
        "alerts": [
            {
                "title": "WARNING: Fake MZUNI Online Degree Programmes",
                "alert_text": "Mzuzu University warns the public that unauthorized entities are advertising fake online degree programmes using the MZUNI name. Verify all programmes at mzuni.ac.mw.",
                "source_url": "https://www.mzuni.ac.mw/notices",
            }
        ],
    },
    {
        "name": "Lilongwe University of Agriculture and Natural Resources (LUANAR)",
        "sector": "Higher Education",
        "website_url": "https://www.luanar.ac.mw",
        "alerts": [
            {
                "title": "NOTICE: Impersonation of LUANAR Admission Officers",
                "alert_text": "LUANAR does not assign admission agents to collect fees from prospective students. All admission inquiries should be directed to the LUANAR Academic Office.",
                "source_url": "https://www.luanar.ac.mw/notices",
            }
        ],
    },
    {
        "name": "Malawi University of Business and Applied Sciences (MUBAS)",
        "sector": "Higher Education",
        "website_url": "https://www.mubas.ac.mw",
        "alerts": [
            {
                "title": "ALERT: Fake MUBAS Short Course Registration Fees",
                "alert_text": "MUBAS cautions the public against paying for short course registrations via unofficial channels. Official course fees are payable only to designated MUBAS bank accounts.",
                "source_url": "https://www.mubas.ac.mw/notices",
            }
        ],
    },
]


@router.post("/seed")
def seed_institutions(db: Session = Depends(get_db)):
    """Seed comprehensive institutional database with 25+ verified Malawian entities and alerts."""
    ai_service = get_ai_service()
    created_insts = 0
    created_alerts = 0

    for inst_data in SEED_INSTITUTIONS:
        inst = db.query(Institution).filter(Institution.name == inst_data["name"]).first()
        if not inst:
            inst = Institution(
                name=inst_data["name"],
                sector=inst_data["sector"],
                website_url=inst_data["website_url"],
            )
            db.add(inst)
            db.flush()
            created_insts += 1

        for alert_data in inst_data["alerts"]:
            existing_alert = db.query(InstitutionalAlert).filter(
                InstitutionalAlert.title == alert_data["title"]
            ).first()

            if not existing_alert:
                full_text = f"{alert_data['title']} {alert_data['alert_text']}"
                emb = ai_service.embed(full_text)

                alert = InstitutionalAlert(
                    institution_id=inst.id,
                    title=alert_data["title"],
                    alert_text=alert_data["alert_text"],
                    source_url=alert_data["source_url"],
                    embedding=emb,
                )
                db.add(alert)
                created_alerts += 1

    db.commit()
    return {
        "status": "success",
        "institutions_created": created_insts,
        "alerts_created": created_alerts,
        "total_institutions": len(SEED_INSTITUTIONS),
    }
