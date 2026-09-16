package com.example.verifeed_android_app.core.screening

import com.example.verifeed_android_app.core.model.RiskLevel
import org.junit.Test
import org.junit.Assert.*

/**
 * On-device Stage 1 engine (E3) — mirrors the backend heuristic behaviour.
 */
class LocalScreeningEngineTest {

    private val engine: LocalScreeningEngine = LocalScreeningEngine()

    @Test
    fun harmlessMessageIsLowRisk() {
        val result = engine.screen("Hi mom, dinner at 7pm as usual. Love you.")
        assertEquals(RiskLevel.LOW, result.riskLevel)
        assertFalse(result.needsDeepVerify)
    }

    @Test
    fun prizePlusShortenedUrlIsHighRisk() {
        val result = engine.screen("Congratulations! You won a FREE iPhone. Click http://bit.ly/claim")
        assertEquals(RiskLevel.HIGH, result.riskLevel)
        assertTrue(result.needsDeepVerify)
        assertTrue(result.patternMatches.contains("suspicious_url"))
    }

    @Test
    fun monetaryRequestIsMediumRisk() {
        val result = engine.screen("Kindly send money now to release your prize funds.")
        assertEquals(RiskLevel.MEDIUM, result.riskLevel)
        assertTrue(result.patternMatches.contains("monetary_request"))
    }

    @Test
    fun institutionMentionAloneIsLowRisk() {
        val result = engine.screen("Standard Bank is offering free loans via SMS")
        assertEquals(RiskLevel.LOW, result.riskLevel)
        assertTrue(result.detectedInstitutions.contains("Standard Bank"))
    }

    @Test
    fun suspiciousSenderNumberIsFlagged() {
        val result = engine.screen("You have an undelivered parcel from courier", sender = "+447700900123")
        assertEquals(RiskLevel.MEDIUM, result.riskLevel)
        assertTrue(result.patternMatches.contains("suspicious_sender"))
    }

    @Test
    fun legitimacyPreservedForPlainUrls() {
        val result = engine.screen("Read our policy at https://reservebank.mw/notices")
        assertEquals(RiskLevel.LOW, result.riskLevel)
        // The legit institutional domain is still listed as a mention candidate.
    }
}