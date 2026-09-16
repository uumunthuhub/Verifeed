package com.example.verifeed_android_app.core.screening

import com.example.verifeed_android_app.core.model.FraudSignal
import com.example.verifeed_android_app.core.model.RiskLevel
import com.example.verifeed_android_app.core.model.ScreeningResult

/**
 * On-device Stage 1 screening engine (E3).
 *
 * Offline-first: deterministic rules only — no network, no AI. This mirrors the
 * VeriFeed backend `app/services/local_screening.py` signal vocabulary so that
 * on-device results and server results can be compared 1:1.
 *
 * Trust boundary: a "High" result here is a signal, never a "Confirmed Scam"
 * verdict. Verification with evidence (Stage 2) is always required for that.
 */
class LocalScreeningEngine {

    // Score thresholds mirror the backend (MEDIUM_THRESHOLD=2, HIGH_THRESHOLD=4).
    private companion object {
        val MEDIUM_THRESHOLD: Int = 2
        val HIGH_THRESHOLD: Int = 4
    }

    private val urgencyPhrases: List<String> = listOf(
        "act now", "limited time", "expires today", "last chance", "urgent",
        "immediately", "within 24 hours", "do not delay", "respond now",
        "account suspended", "account blocked", "verify now", "click immediately",
        "claim your prize", "congratulations you have won", "you are selected",
    )

    private val monetaryRequestPhrases: List<String> = listOf(
        "send money", "transfer funds", "pay a fee", "processing fee",
        "registration fee", "activation fee", "release fee", "small fee",
        "wire transfer", "western union", "send airtime", "buy voucher",
        "buy recharge card", "momo transfer", "airtel money transfer",
    )

    private val impersonationKeywords: List<String> = listOf(
        "standard bank", "airtel money", "tnm mpamba", "national bank",
        "fdh bank", "rbm", "reserve bank", "macra", "malawi government",
        "malawi police", "escom", "water board", "mra",
    )

    private val unsolicitedPrizePhrases: List<String> = listOf(
        "you have won", "winner selected", "prize money", "lottery winner",
        "lucky winner", "free iphone", "free laptop", "cash prize",
        "claim your reward", "claim your prize",
    )

    // Known suspicious URL shorteners and typosquat patterns.
    private val suspiciousUrlPatterns: List<Regex> = listOf(
        Regex("""bit\.ly/""", RegexOption.IGNORE_CASE),
        Regex("""tinyurl\.com/""", RegexOption.IGNORE_CASE),
        Regex("""t\.co/[a-zA-Z0-9]{8,}""", RegexOption.IGNORE_CASE),
        Regex("""rb\.gy/""", RegexOption.IGNORE_CASE),
        Regex("""is\.gd/""", RegexOption.IGNORE_CASE),
        Regex("""cutt\.ly/""", RegexOption.IGNORE_CASE),
        Regex("""shorturl\.at/""", RegexOption.IGNORE_CASE),
        Regex("""ow\.ly/""", RegexOption.IGNORE_CASE),
        Regex("""goo\.gl/""", RegexOption.IGNORE_CASE),
        Regex("""airtel-mw\.""", RegexOption.IGNORE_CASE),
        Regex("""standard-bank-mw\.""", RegexOption.IGNORE_CASE),
        Regex("""tnm-mpamba\.""", RegexOption.IGNORE_CASE),
        Regex("""rbm-mw\.""", RegexOption.IGNORE_CASE),
        Regex("""macra-mw\.""", RegexOption.IGNORE_CASE),
        Regex("""malawi-gov\.""", RegexOption.IGNORE_CASE),
        Regex("""mw-gov\.""", RegexOption.IGNORE_CASE),
    )

    private val suspiciousSenderPatterns: List<Regex> = listOf(
        Regex("""^\+1\d{10}$"""),
        Regex("""^\+44\d{10}$"""),
        Regex("""^\d{5,6}$"""),
    )

    /** Screen a message/URL/notification body and return a local Stage 1 result. */
    fun screen(content: String, sender: String? = null): ScreeningResult {
        val signals = ArrayList<FraudSignal>()

        val urls = UrlExtractor.extractUrls(content)
        urlSignals(urls).forEach { signals.add(it) }

        phraseSignals(content.lowercase()).forEach { signals.add(it) }

        sender?.let { snd ->
            suspiciousSenderPatterns.forEach { pattern ->
                if (pattern.containsMatchIn(snd.trim())) {
                    signals.add(
                        FraudSignal(
                            signalType = "suspicious_sender",
                            description = "Sender number matches a pattern commonly associated with SMS phishing",
                            matchedText = snd,
                            severity = FraudSignal.HIGH,
                        ),
                    )
                    return@forEach // stop at first pattern match
                }
            }
        }

        val institutions = detectInstitutions(content)
        if (institutions.isNotEmpty() && urls.isEmpty() && signals.isEmpty()) {
            signals.add(
                FraudSignal(
                    signalType = "institution_mention",
                    description = "Known institution name detected: " +
                        institutions.joinToString(", ") { titleCase(it) },
                    matchedText = institutions.joinToString(", "),
                    severity = FraudSignal.LOW,
                ),
            )
        }

        val risk = computeRiskLevel(signals)
        return ScreeningResult(
            riskLevel = risk,
            signals = signals.toList(),
            patternMatches = signals.map { it.signalType },
            needsDeepVerify = risk == RiskLevel.MEDIUM || risk == RiskLevel.HIGH,
            recommendedAction = recommendedAction(risk, institutions),
            screenedUrls = urls,
            detectedInstitutions = institutions.map { titleCase(it) },
            source = ScreeningResult.Stage1Source.LOCAL,
        )
    }

/** Returns known institution names mentioned in the message (lower-cased). */
    fun detectInstitutions(text: String): List<String> {
        val tl = text.lowercase()
        return impersonationKeywords.filter { keyword -> tl.contains(keyword) }
    }

    /** Backend-equivalent display form: "standard bank" → "Standard Bank". */
    private fun titleCase(input: String): String =
        input.split(" ")
            .filter { it.isNotEmpty() }
            .map { word -> word[0].uppercase().toString() + word.drop(1) }
            .joinToString(" ")

    // ------------------------------------------------------------------
    // Internal helpers
    // ------------------------------------------------------------------

    private fun urlSignals(urls: List<String>): List<FraudSignal> {
        val result = ArrayList<FraudSignal>()
        urls.forEach { url ->
            suspiciousUrlPatterns.forEach { pattern ->
                if (pattern.containsMatchIn(url)) {
                    result.add(
                        FraudSignal(
                            signalType = "suspicious_url",
                            description = "Suspicious or shortened URL detected: may redirect to phishing site",
                            matchedText = url,
                            severity = FraudSignal.HIGH,
                        ),
                    )
                    return@forEach // one signal per URL
                }
            }
        }
        return result.toList()
    }

    private fun phraseSignals(lowerText: String): List<FraudSignal> {
        val result = ArrayList<FraudSignal>()

        urgencyPhrases.firstOrNull { phrase -> lowerText.contains(phrase) }?.let { phrase ->
            result.add(
                FraudSignal(
                    signalType = "urgency_language",
                    description = "Urgency language detected — a common tactic to pressure victims",
                    matchedText = phrase,
                    severity = FraudSignal.MEDIUM,
                ),
            )
        }

        monetaryRequestPhrases.firstOrNull { phrase -> lowerText.contains(phrase) }?.let { phrase ->
            result.add(
                FraudSignal(
                    signalType = "monetary_request",
                    description = "Message requests money transfer or payment — high scam indicator",
                    matchedText = phrase,
                    severity = FraudSignal.HIGH,
                ),
            )
        }

        unsolicitedPrizePhrases.firstOrNull { phrase -> lowerText.contains(phrase) }?.let { phrase ->
            result.add(
                FraudSignal(
                    signalType = "unsolicited_prize",
                    description = "Unsolicited prize or lottery claim — classic advance-fee scam pattern",
                    matchedText = phrase,
                    severity = FraudSignal.HIGH,
                ),
            )
        }

        return result.toList()
    }

    private fun computeRiskLevel(signals: List<FraudSignal>): RiskLevel {
        val highCount = signals.count { it.severity == FraudSignal.HIGH }
        val total = signals.size
        return when {
            highCount >= 2 || total >= HIGH_THRESHOLD -> RiskLevel.HIGH
            total >= MEDIUM_THRESHOLD || highCount == 1 -> RiskLevel.MEDIUM
            else -> RiskLevel.LOW
        }
    }

    private fun recommendedAction(riskLevel: RiskLevel, institutions: List<String>): String {
        return when (riskLevel) {
            RiskLevel.HIGH -> {
                val institution = institutions.firstOrNull()?.let { titleCase(it) } ?: "the institution"
                "Do not click any links or send money. Contact $institution directly using " +
                    "their official website or number."
            }
            RiskLevel.MEDIUM -> "Proceed with caution. Verify this message with VeriFeed before acting."
            else -> "No immediate concerns detected. You can still verify with VeriFeed for peace of mind."
        }
    }
}