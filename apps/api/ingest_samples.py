"""
Ingest Samples Script — Seed and Train VeriFeed Dataset.

Usage:
  python ingest_samples.py [--file path/to/dataset.json]

Feeds sample SMS messages, fake promos, phishing email texts, and official TNM/Airtel/Bank
communications directly into the VeriFeed RAG & vector embedding database.
"""

import sys
import json
import hashlib
import logging
from app.db.session import SessionLocal
from app.models.source import Source
from app.models.article import Article
from app.services.fraud_detector import process_user_submission
from app.services.ai import get_ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DATASET = [
    # Mtukula Pakhomo & Social Welfare Fraud SMS
    {
        "text": "JB FOUNDATION MTUKULA PAKHOMO PROJECT: Mwachita mwayi olandra nawo ndalama zamtukula pakhomo MK75000 imbani 0980200870, 0997998430 kuti Mmthandizidwe",
        "category": "scam_sms",
        "is_legitimate": False
    },
    {
        "text": "MTUKULA PAKHOMO PROJECT: Nambala yanu yasankhidwa kulandira ndalama za boma zokwana MK75000 kwa miyezi itatu imbani pa 0983601924",
        "category": "scam_sms",
        "is_legitimate": False
    },
     {  "text" :"Ndalama ija Mutumizire pa Number iyi 0992206119 Dzina Iremba Bright MAGWAYA",
        "category": "scam_sms",
        "is_legitimate": False
     },
    {
        "text": "MTUKULA PAKHOMO: Mwachita Mwayi Olandira ndalama Zamtukula Pakhomo Zokwana MK250000.00 imbirani MR KHRISPIN NTHAWI pa:0995849470",
        "category": "scam_sms",
        "is_legitimate": False
    },
    # Instant Collateral-Free WhatsApp Loans
    {
        "text": "Standard Bank WhatsApp Instant Loan Promo: Get MK500,000 to MK5,000,000 collateral free loan within 30 mins. Deposit MK15,000 processing fee via Airtel Money to 0991234567 to release funds.",
        "category": "fake_promo",
        "is_legitimate": False
    },
    {
        "text": "FDH KANYIMBI QUICK LOAN PROMO: Express collateral-free loan approved for your number! Send MK10,000 registration fee to agent 0888123456 to receive MK300,000 cash instantly.",
        "category": "fake_promo",
        "is_legitimate": False
    },
    
    # Fake TNM Mpamba Promotion SMS
    {
        "text": "TNM Mpamba Promotional SMS: Congratulations! Your number has been selected to win a brand new iPhone 15 Pro. Send MK5,000 registration fee to 0993206119 to claim your prize.",
        "category": "scam_sms",
        "is_legitimate": False
    },
    # Mobile Money PIN & SIM Swap Scams
    {
        "text": "Airtel Money Customer Care Notice: Your mobile money account has been temporarily locked due to suspicious login. Dial *21*0999000111# or reply with your 4-digit PIN to unlock.",
        "category": "phishing_sms",
        "is_legitimate": False
    },
    {
        "text": "TNM Mpamba Reversal Scam: I accidentally transferred MK45,000 to your Mpamba number instead of my sister. Please send back MK45,000 immediately to 0888999888.",
        "category": "scam_sms",
        "is_legitimate": False
    },

    # Official Legitimate Broadcasts (TNM / Airtel / Banks)
    {
        "text": "TNM Official Notice: Official TNM Mpamba promotions are communicated ONLY via shortcode 105 or *105#. TNM will NEVER call you asking for your secret PIN or asking you to transfer money to claim a prize.",
        "category": "official_promo",
        "is_legitimate": True
    },
    {
        "text": "SPARM ALERT: Airtel Sparm Alert simawelenga mauthenga anu, koma imakuchenjezani ndi mawu oti SPAM ALERT mukalandira uthenga wokayikitsa kuti musabeledwe",
        "category": "offficial_promo",
        "is_legitimate": True
        },
        {
        "text": "SPARM ALERT: Khalani tcheru ndi mauthenga ofuna kukubelani. Airtel imakuchenjezani ndi mawu oti SPAM ALERT mukalandira  wokayikitsa. Khalani otetezeka nthawi zonse",
        "category": "offficial_promo",
        "is_legitimate": True
        },
        {
        "text": "SPARM ALERT: Chitetezo chapamwamba! Airtel Spam Alert idzikuchenjezani ndi mawu oti SPAM ALERT ngati mwalanndila uthenga wokayikitsa #SpamAlert#KhalaniTcheru",
        "category": "offficial_promo",
        "is_legitimate": True
        },
        {
        "text": "CHENJEZO: Khalani otetezeka Pewani utsegula ma link osavomelezek. Airtel imagwiritsa ntchito +265121 poyimba foni kapena customercare_mw@mw.airtel.com potumiza email",
        "category": "offficial_promo",
        "is_legitimate": True
        },
    {
        "text": "Airtel Money Security Advisory: Airtel Money staff will NEVER call you asking for your 4-digit secret PIN or OTP. Never share your PIN with anyone, including customer service agents.",
        "category": "official_promo",
        "is_legitimate": True
    },
    {
        "text": "Standard Bank Security Disclaimer: Standard Bank does NOT offer instant loans via WhatsApp or personal mobile money accounts. All official loans are processed inside Standard Bank branches or via our official internet banking platform.",
        "category": "official_promo",
        "is_legitimate": True
    }
]

def ingest_samples(dataset=None):
    if dataset is None:
        dataset = SAMPLE_DATASET

    db = SessionLocal()
    ai_service = get_ai_service()
    ingested = 0

    try:
        default_source = db.query(Source).filter(Source.name == "VeriFeed Dataset Registry").first()
        if not default_source:
            default_source = Source(name="VeriFeed Dataset Registry", website_url="https://verifeed.mw", trust_tier=1)
            db.add(default_source)
            db.flush()


        for item in dataset:
            if isinstance(item, str):
                text = item.strip()
                is_legit = False
            elif isinstance(item, dict):
                raw_text = item.get("text")
                if isinstance(raw_text, str):
                    text = raw_text.strip()
                elif raw_text is not None and not isinstance(raw_text, bool):
                    text = str(raw_text).strip()
                else:
                    text = ""
                is_legit = bool(item.get("is_legitimate", False))
            else:
                continue

            if not text or len(text) < 5:
                continue

            if not is_legit:
                sub = process_user_submission(db, text)
                sub_id = getattr(sub, "id", None)
                cluster_id = getattr(sub, "cluster_id", None)
                logger.info(f"Ingested scam sample #{sub_id} -> Cluster #{cluster_id}: '{text[:60]}...'")
            else:
                emb = ai_service.embed(text)
                url_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
                existing_art = db.query(Article).filter(Article.url.endswith(url_hash)).first()
                if not existing_art:
                    art = Article(
                        source_id=default_source.id,
                        headline=text[:150],
                        content=text,
                        url=f"https://verifeed.mw/verified-channel/{url_hash}",
                        embedding=emb,
                    )
                    db.add(art)
                    logger.info(f"Ingested legitimate official sample: '{text[:60]}...'")

            ingested += 1

        db.commit()
        logger.info(f"Successfully ingested {ingested} dataset samples into VeriFeed.")
        return ingested
    except Exception as exc:
        db.rollback()
        logger.error(f"Error ingesting samples: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    if filepath:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        ingest_samples(data)
    else:
        ingest_samples()
