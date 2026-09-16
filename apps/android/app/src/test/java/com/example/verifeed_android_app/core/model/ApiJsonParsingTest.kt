package com.example.verifeed_android_app.core.model

import org.junit.Test
import org.junit.Assert.*

/**
 * API contract parsing — Stage 1 screening and Stage 2 verification
 * responses must deserialize into the typed models (E3/E2).
 */
class ApiJsonParsingTest {

    @Test
    fun parsesScreeningResponse() {
        val body = """
            {
              "risk_level": "High",
              "signals": [
                {
                  "signal_type": "suspicious_url",
                  "description": "Suspicious or shortened URL detected",
                  "matched_text": "http://bit.ly/claim",
                  "severity": "high"
                }
              ],
              "pattern_matches": ["suspicious_url"],
              "needs_deep_verify": true,
              "recommended_action": "Do not click any links or send money.",
              "screened_urls": ["http://bit.ly/claim"],
              "detected_institutions": []
            }
            """

        val result = ScreeningResult.fromApiJson(body)

        assertEquals(RiskLevel.HIGH, result.riskLevel)
        assertEquals(ScreeningResult.Stage1Source.REMOTE, result.source)
        assertEquals(1, result.signals.size)
        assertEquals("suspicious_url", result.signals[0].signalType)
        assertTrue(result.needsDeepVerify)
        assertEquals(1, result.screenedUrls.size)
    }

    @Test
    fun parsesLowRiskScreeningResponse() {
        val body = """{"risk_level":"Low","signals":[],"pattern_matches":[],"needs_deep_verify":false,"recommended_action":"No immediate concerns detected.","screened_urls":[],"detected_institutions":[]}"""
        val result = ScreeningResult.fromApiJson(body)
        assertEquals(RiskLevel.LOW, result.riskLevel)
        assertFalse(result.needsDeepVerify)
    }

    @Test
    fun parsesVerificationResponseWithDualVerdict() {
        val body = """
            {
              "id": 42,
              "query": "Standard Bank offering free loans via SMS",
              "verdict": "Confirmed Scam",
              "claim_verdict": "False",
              "message_authenticity_verdict": "Confirmed Fraudulent",
              "confidence_score": 0.87,
              "risk_level": "High",
              "summary": "This is a known advance-fee scam.",
              "sources": [
                {
                  "title": "RBM warns of fake loan SMS",
                  "outlet": "Reserve Bank of Malawi",
                  "url": "https://rbm.mw/alert",
                  "type": "Official Institutional Alert",
                  "snippet": "Do not respond to unsolicited loan offers."
                }
              ],
              "extracted_sender": "+447700900123",
              "extracted_numbers": ["+447700900123"],
              "extracted_urls": [],
              "extracted_institutions": ["Standard Bank"],
              "recommended_actions": [
                {"action": "Do not send money", "priority": "critical"} ],
              "methodology": "Matched 1 institutional alert",
              "created_at": "2026-09-15T10:00:00Z"
            }
            """

        val result = VerificationSummary.fromApiJson(body)

        assertEquals(42, result.id)
        assertEquals("Confirmed Fraudulent", result.messageAuthenticityVerdict)
        assertEquals("False", result.claimVerdict)
        assertTrue(Math.abs(0.87 - result.confidenceScore) < 0.001)
        assertEquals(1, result.sources.size)
        assertEquals("Official Institutional Alert", result.sources[0].type)
        assertEquals(1, result.recommendedActions.size)
        assertEquals("Do not send money", result.recommendedActions[0])
        assertTrue(result.methodology!!.contains("institutional alert"))
    }
}