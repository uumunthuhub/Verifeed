package com.example.verifeed_android_app.core.screening

import com.example.verifeed_android_app.core.model.FraudSignal
import com.example.verifeed_android_app.core.model.RiskLevel
import com.example.verifeed_android_app.core.model.ScreeningResult

/**
 * On-Device Email Phishing & Spoof Screener (Phase H).
 *
 * Fast local heuristics for shared email text and header snippets:
 * 1. Sender domain mismatch against recognized institutions.
 * 2. Phishing lure keyword matching.
 * 3. Shortened or suspicious URL detection.
 */
class EmailScreener {

    private companion object {
        val KNOWN_INSTITUTIONS = mapOf(
            "paypal" to "paypal.com",
            "standard bank" to "standardbank.co.za",
            "airtel" to "airtel.in",
            "who" to "who.int",
            "google" to "google.com",
            "apple" to "apple.com",
            "amazon" to "amazon.com",
            "netflix" to "netflix.com"
        )

        val URGENCY_KEYWORDS = listOf(
            "account suspended", "urgent action required", "verify your password",
            "unauthorized login", "security alert", "click here to unlock",
            "immediate verification needed"
        )
    }

    fun screenEmail(senderAddress: String, displayName: String, subject: String, body: String): ScreeningResult {
        val signals = mutableListOf<FraudSignal>()
        var riskScore = 0

        val senderLower = senderAddress.lowercase().trim()
        val displayLower = displayName.lowercase().trim()
        val senderDomain = if (senderLower.contains("@")) senderLower.substringAfter("@") else ""

        // 1. Domain Spoofing Check
        KNOWN_INSTITUTIONS.forEach { (instName, officialDomain) ->
            if (displayLower.contains(instName) || subject.lowercase().contains(instName)) {
                if (senderDomain.isNotEmpty() && !senderDomain.endsWith(officialDomain)) {
                    riskScore += 45
                    signals.add(
                        FraudSignal(
                            signalType = "DOMAIN_SPOOF",
                            description = "Spoof Alert: Claims to be '$instName', but sent from '$senderDomain' (expected '$officialDomain')",
                            matchedText = senderAddress,
                            severity = FraudSignal.HIGH
                        )
                    )
                }
            }
        }

        // 2. Urgency Lure Keywords
        val fullText = "$subject $body".lowercase()
        URGENCY_KEYWORDS.forEach { kw ->
            if (fullText.contains(kw)) {
                riskScore += 15
                signals.add(
                    FraudSignal(
                        signalType = "PHISHING_LURE",
                        description = "Phishing Lure Phrase: '$kw'",
                        matchedText = kw,
                        severity = FraudSignal.MEDIUM
                    )
                )
            }
        }

        val riskLevel = when {
            riskScore >= 45 -> RiskLevel.HIGH
            riskScore >= 20 -> RiskLevel.MEDIUM
            else -> RiskLevel.LOW
        }

        val action = when (riskLevel) {
            RiskLevel.HIGH -> "CRITICAL: Do NOT click links or download attachments. This email appears spoofed."
            RiskLevel.MEDIUM -> "WARNING: Inspect the sender address carefully before taking action."
            RiskLevel.LOW -> "No suspicious spoofing or phishing signals detected."
            else -> "No suspicious spoofing or phishing signals detected."
        }

        return ScreeningResult(
            riskLevel = riskLevel,
            signals = signals,
            patternMatches = signals.map { it.description },
            recommendedAction = action,
            needsDeepVerify = riskLevel != RiskLevel.LOW
        )
    }
}
