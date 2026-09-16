import re
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.institution import Institution
from app.schemas.email import EmailVerificationRequest, EmailVerificationResponse


class EmailScreener:
    """
    Email Phishing & Domain Spoofing Screener (Phase H).
    
    Performs multi-layered verification:
    1. Display Name / Domain Spoofing Detection (e.g. "Standard Bank" <info@scam-loans.com>)
    2. URL & Link Extraction & Pattern Matching
    3. Urgent Financial / Security Lure Keywords
    4. Optional Raw Header (SPF/DKIM) Inspection
    """

    KNOWN_INSTITUTION_DOMAINS: Dict[str, str] = {
        "paypal": "paypal.com",
        "standard bank": "standardbank.co.za",
        "airtel": "airtel.in",
        "who": "who.int",
        "google": "google.com",
        "apple": "apple.com",
        "microsoft": "microsoft.com",
        "amazon": "amazon.com",
        "netflix": "netflix.com",
        "meta": "facebook.com",
    }

    SUSPICIOUS_KEYWORDS = [
        "account suspended", "urgent action required", "verify your password",
        "unauthorized login attempt", "security alert", "click here to unlock",
        "wire transfer", "gift card", "immediate verification needed",
        "invoice attached", "unpaid bill alert"
    ]

    def screen(self, payload: EmailVerificationRequest, db: Optional[Session] = None) -> EmailVerificationResponse:
        signals: List[str] = []
        suspicious_links: List[str] = []
        domain_spoof_detected = False
        official_domain_match: Optional[str] = None
        risk_score = 0

        sender_email = payload.sender_address.lower().strip()
        display_name = (payload.display_name or "").lower().strip()
        body = payload.body_text
        subject = payload.subject

        # Extract domain from sender address
        sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""

        # 1. Domain Spoofing & Impersonation Check
        for inst_key, official_domain in self.KNOWN_INSTITUTION_DOMAINS.items():
            if inst_key in display_name or inst_key in subject.lower():
                if sender_domain and not sender_domain.endswith(official_domain):
                    domain_spoof_detected = True
                    signals.append(f"Spoof Alert: Sender display name claims '{inst_key.title()}', but sender domain is '{sender_domain}' (expected '{official_domain}')")
                    risk_score += 45
                else:
                    official_domain_match = official_domain

        # 2. Extract Embedded URLs & Check for Suspicious Links
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, body)
        for url in urls:
            clean_url = url.lower()
            if any(shorter in clean_url for shorter in ["bit.ly", "tinyurl.com", "t.co", "is.gd", "rb.gy"]):
                suspicious_links.append(url)
                signals.append(f"Shortened/Obfuscated Link: {url}")
                risk_score += 20
            elif domain_spoof_detected:
                suspicious_links.append(url)

        # 3. Urgency & Security Lure Keywords
        full_text = f"{subject} {body}".lower()
        matched_keywords = [kw for kw in self.SUSPICIOUS_KEYWORDS if kw in full_text]
        if matched_keywords:
            signals.append(f"Phishing Lure Keywords: {', '.join(matched_keywords[:3])}")
            risk_score += len(matched_keywords) * 10

        # 4. Header Authentication Inspection (SPF / DKIM / DMARC)
        if payload.headers:
            headers_lower = payload.headers.lower()
            if "spf=fail" in headers_lower or "dkim=fail" in headers_lower:
                signals.append("Header Auth Failure: SPF/DKIM verification failed")
                risk_score += 30

        # Determine Risk Level & Authenticity Verdict
        if risk_score >= 50 or domain_spoof_detected:
            risk_level = "High"
            email_verdict = "SPOOFED_SENDER" if domain_spoof_detected else "PHISHING_EMAIL"
            msg_verdict = "PHISHING / SCAM LURE"
        elif risk_score >= 20:
            risk_level = "Medium"
            email_verdict = "SUSPICIOUS"
            msg_verdict = "SUSPICIOUS"
        else:
            risk_level = "Low"
            email_verdict = "AUTHENTIC"
            msg_verdict = "AUTHENTIC"

        recommended_actions = []
        if risk_level == "High":
            recommended_actions.append("Do NOT click any links or download attachments in this email.")
            recommended_actions.append(f"Verify directly through the official website: https://{official_domain_match or 'official institution site'}")
            recommended_actions.append("Mark email as Phishing / Spam in your inbox.")
        elif risk_level == "Medium":
            recommended_actions.append("Inspect the sender address carefully before taking action.")
            recommended_actions.append("Avoid clicking links; type the official website address directly into your browser.")
        else:
            recommended_actions.append("No immediate phishing or spoofing signals detected.")

        return EmailVerificationResponse(
            risk_level=risk_level,
            email_authenticity_verdict=email_verdict,
            domain_spoof_detected=domain_spoof_detected,
            official_domain_match=official_domain_match,
            suspicious_links=suspicious_links,
            detected_signals=signals,
            claim_verdict="FALSE" if risk_level == "High" else "UNVERIFIED",
            message_authenticity_verdict=msg_verdict,
            recommended_actions=recommended_actions,
        )
