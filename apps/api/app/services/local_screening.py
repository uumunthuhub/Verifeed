"""
VeriFeed Local Screening Engine — Stage 1

Provides fast, deterministic risk assessment of incoming content without
any network calls or Gemini API invocation. Results are returned in
milliseconds and are used to decide whether Stage 2 deep verification
is warranted.

Architecture (per VeriFeed_Project_Blueprint_Final.md §78.3):

  Stage 1 — Immediate local screening
    URL pattern matching, sender signals, phrase heuristics, known indicators
    → risk_level, signals, needs_deep_verify

  Stage 2 — Deep VeriFeed verification (handled by verification_agent.py)
    Content → Evidence → Gemini → Verdict

Verdict trust boundary:
  LOCAL SIGNALS ≠ VERIFIED EVIDENCE ≠ GEMINI ANALYSIS ≠ FINAL VERDICT

This module only produces Stage 1 output. It never produces a "Confirmed Scam"
or any final verdict — those require the full evidence pipeline.
"""

import re
from dataclasses import dataclass, field
from typing import ClassVar

# ---------------------------------------------------------------------------
# Signal definitions
# ---------------------------------------------------------------------------

URGENCY_PHRASES: list[str] = [
    "act now", "limited time", "expires today", "last chance", "urgent",
    "immediately", "within 24 hours", "do not delay", "respond now",
    "account suspended", "account blocked", "verify now", "click immediately",
    "claim your prize", "congratulations you have won", "you are selected",
]

MONETARY_REQUEST_PHRASES: list[str] = [
    "send money", "transfer funds", "pay a fee", "processing fee",
    "registration fee", "activation fee", "release fee", "small fee",
    "wire transfer", "western union", "send airtime", "buy voucher",
    "buy recharge card", "momo transfer", "airtel money transfer",
]

IMPERSONATION_KEYWORDS: list[str] = [
    "standard bank", "airtel money", "tnm mpamba", "national bank",
    "fdh bank", "rbm", "reserve bank", "macra", "malawi government",
    "malawi police", "escom", "water board", "mra",
]

UNSOLICITED_PRIZE_PHRASES: list[str] = [
    "you have won", "winner selected", "prize money", "lottery winner",
    "lucky winner", "free iphone", "free laptop", "cash prize",
    "claim your reward", "claim your prize",
]

# Known suspicious URL shorteners and scam-hosting patterns
SUSPICIOUS_URL_PATTERNS: list[str] = [
    r"bit\.ly/",
    r"tinyurl\.com/",
    r"t\.co/[a-zA-Z0-9]{8,}",  # non-verified t.co links
    r"rb\.gy/",
    r"is\.gd/",
    r"cutt\.ly/",
    r"shorturl\.at/",
    r"ow\.ly/",
    r"goo\.gl/",
    # Typosquat patterns for Malawian institutions
    r"airtel-mw\.",
    r"standard-bank-mw\.",
    r"tnm-mpamba\.",
    r"rbm-mw\.",
    r"macra-mw\.",
    r"malawi-gov\.",
    r"mw-gov\.",
]

# Known scam short codes and phone number patterns (Malawi)
SUSPICIOUS_SENDER_PATTERNS: list[str] = [
    r"^\+1\d{10}$",         # US numbers used in SMS phishing
    r"^\+44\d{10}$",        # UK numbers used in SMS phishing
    r"^\d{5,6}$",           # Generic short codes not in registry
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DetectedSignal:
    signal_type: str
    description: str
    matched_text: str | None = None
    severity: str = "medium"  # low | medium | high


@dataclass
class ScreeningResult:
    risk_level: str = "Low"           # Low | Medium | High
    signals: list[DetectedSignal] = field(default_factory=list)
    pattern_matches: list[str] = field(default_factory=list)
    needs_deep_verify: bool = False
    recommended_action: str = "No immediate concerns detected."
    screened_urls: list[str] = field(default_factory=list)
    detected_institutions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Screening engine
# ---------------------------------------------------------------------------

class LocalScreeningEngine:
    """
    Deterministic, zero-latency content screening.

    All methods operate on plain text. No network calls, no DB access,
    no AI inference. Designed to run in < 5ms for typical message lengths.
    """

    # Score thresholds → risk level
    MEDIUM_THRESHOLD: ClassVar[int] = 2
    HIGH_THRESHOLD: ClassVar[int] = 4

    @staticmethod
    def _text_lower(text: str) -> str:
        return text.lower()

    # --- URL screening --------------------------------------------------

    @classmethod
    def screen_urls(cls, text: str) -> tuple[list[str], list[DetectedSignal]]:
        """Extract and screen URLs from content."""
        url_pattern = re.compile(
            r"https?://[^\s<>\"{}|\\^`\[\]]+|www\.[^\s<>\"{}|\\^`\[\]]+",
            re.IGNORECASE,
        )
        found_urls = list(set(url_pattern.findall(text)))
        signals: list[DetectedSignal] = []

        for url in found_urls:
            for pattern in SUSPICIOUS_URL_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    signals.append(DetectedSignal(
                        signal_type="suspicious_url",
                        description="Suspicious or shortened URL detected: may redirect to phishing site",
                        matched_text=url,
                        severity="high",
                    ))
                    break  # one signal per URL

        return found_urls, signals

    # --- Phrase / keyword screening ------------------------------------

    @classmethod
    def screen_phrases(cls, text: str) -> list[DetectedSignal]:
        """Check for urgency, monetary requests, prizes, and impersonation."""
        tl = cls._text_lower(text)
        signals: list[DetectedSignal] = []

        for phrase in URGENCY_PHRASES:
            if phrase in tl:
                signals.append(DetectedSignal(
                    signal_type="urgency_language",
                    description="Urgency language detected — a common tactic to pressure victims",
                    matched_text=phrase,
                    severity="medium",
                ))
                break  # one urgency signal is enough

        for phrase in MONETARY_REQUEST_PHRASES:
            if phrase in tl:
                signals.append(DetectedSignal(
                    signal_type="monetary_request",
                    description="Message requests money transfer or payment — high scam indicator",
                    matched_text=phrase,
                    severity="high",
                ))
                break

        for phrase in UNSOLICITED_PRIZE_PHRASES:
            if phrase in tl:
                signals.append(DetectedSignal(
                    signal_type="unsolicited_prize",
                    description="Unsolicited prize or lottery claim — classic advance-fee scam pattern",
                    matched_text=phrase,
                    severity="high",
                ))
                break

        return signals

    # --- Institution detection ----------------------------------------

    @classmethod
    def detect_institutions(cls, text: str) -> list[str]:
        """Return known institution names mentioned in the content."""
        tl = cls._text_lower(text)
        return [inst for inst in IMPERSONATION_KEYWORDS if inst in tl]

    # --- Sender screening ---------------------------------------------

    @classmethod
    def screen_sender(cls, sender: str | None) -> list[DetectedSignal]:
        """Check sender ID / phone number against suspicious patterns."""
        if not sender:
            return []
        signals: list[DetectedSignal] = []
        for pattern in SUSPICIOUS_SENDER_PATTERNS:
            if re.match(pattern, sender.strip()):
                signals.append(DetectedSignal(
                    signal_type="suspicious_sender",
                    description="Sender number matches a pattern commonly associated with SMS phishing",
                    matched_text=sender,
                    severity="high",
                ))
                break
        return signals

    # --- Risk scoring -------------------------------------------------

    @classmethod
    def _compute_risk_level(cls, signals: list[DetectedSignal]) -> str:
        high_count = sum(1 for s in signals if s.severity == "high")
        total = len(signals)
        if high_count >= 2 or total >= cls.HIGH_THRESHOLD:
            return "High"
        if total >= cls.MEDIUM_THRESHOLD or high_count == 1:
            return "Medium"
        return "Low"

    @classmethod
    def _recommended_action(cls, risk_level: str, institutions: list[str]) -> str:
        if risk_level == "High":
            inst = institutions[0].title() if institutions else "the institution"
            return (
                f"Do not click any links or send money. "
                f"Contact {inst} directly using their official website or number."
            )
        if risk_level == "Medium":
            return "Proceed with caution. Verify this message with VeriFeed before acting."
        return "No immediate concerns detected. You can still verify with VeriFeed for peace of mind."

    # --- Main entry point --------------------------------------------

    @classmethod
    def screen(
        cls,
        content: str,
        sender: str | None = None,
    ) -> ScreeningResult:
        """
        Screen content and return a Stage 1 ScreeningResult.

        Args:
            content: The message text, URL, or notification body.
            sender: Optional sender ID or phone number.

        Returns:
            ScreeningResult with risk_level, signals, and recommendation.
            Never returns a 'Confirmed Scam' verdict — that requires Stage 2.
        """
        all_signals: list[DetectedSignal] = []

        # URL screening
        found_urls, url_signals = cls.screen_urls(content)
        all_signals.extend(url_signals)

        # Phrase screening
        phrase_signals = cls.screen_phrases(content)
        all_signals.extend(phrase_signals)

        # Sender screening
        sender_signals = cls.screen_sender(sender)
        all_signals.extend(sender_signals)

        # Institution detection
        institutions = cls.detect_institutions(content)
        if institutions and not url_signals and not phrase_signals:
            # Institution mentioned but no other signals — low concern
            all_signals.append(DetectedSignal(
                signal_type="institution_mention",
                description=f"Known institution name detected: {', '.join(i.title() for i in institutions)}",
                matched_text=", ".join(institutions),
                severity="low",
            ))

        risk_level = cls._compute_risk_level(all_signals)
        needs_deep_verify = risk_level in ("Medium", "High")

        return ScreeningResult(
            risk_level=risk_level,
            signals=all_signals,
            pattern_matches=[s.signal_type for s in all_signals],
            needs_deep_verify=needs_deep_verify,
            recommended_action=cls._recommended_action(risk_level, institutions),
            screened_urls=found_urls,
            detected_institutions=[i.title() for i in institutions],
        )


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------

def screen_content(content: str, sender: str | None = None) -> dict:
    """
    Module-level entry point for Stage 1 local screening.

    Returns a plain dict suitable for use in ScreeningResponse schema.
    """
    result = LocalScreeningEngine.screen(content, sender=sender)
    return {
        "risk_level": result.risk_level,
        "signals": [
            {
                "signal_type": s.signal_type,
                "description": s.description,
                "matched_text": s.matched_text,
                "severity": s.severity,
            }
            for s in result.signals
        ],
        "pattern_matches": result.pattern_matches,
        "needs_deep_verify": result.needs_deep_verify,
        "recommended_action": result.recommended_action,
        "screened_urls": result.screened_urls,
        "detected_institutions": result.detected_institutions,
    }
