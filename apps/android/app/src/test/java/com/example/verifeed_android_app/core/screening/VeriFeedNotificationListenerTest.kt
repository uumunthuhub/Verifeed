package com.example.verifeed_android_app.core.screening

import com.example.verifeed_android_app.core.model.RiskLevel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for Stage 1 local screening logic used by VeriFeedNotificationListener.
 */
class VeriFeedNotificationListenerTest {

    private lateinit var engine: LocalScreeningEngine

    @Before
    fun setUp() {
        engine = LocalScreeningEngine()
    }

    @Test
    fun testUrgencyPhishingNotificationFlagged() {
        val notificationSnippet = "Bank alert: Urgent action required! Your account has been suspended. Click http://bit.ly/bank-security"
        val result = engine.screen(notificationSnippet)

        assertTrue(result.needsDeepVerify)
        assertTrue(result.signals.any { it.description.contains("Suspicious", ignoreCase = true) || it.description.contains("Urgency", ignoreCase = true) })
    }

    @Test
    fun testPrizeLureNotificationFlaggedAsHighRisk() {
        val notificationSnippet = "Congratulations! You have won a free gift card. Claim immediately at http://bit.ly/prize-claim"
        val result = engine.screen(notificationSnippet)

        assertEquals(RiskLevel.HIGH, result.riskLevel)
        assertTrue(result.needsDeepVerify)
        assertTrue(result.signals.any { it.description.contains("prize", ignoreCase = true) || it.description.contains("Suspicious", ignoreCase = true) })
    }

    @Test
    fun testSafeNotificationFlaggedAsLowRisk() {
        val notificationSnippet = "Meeting scheduled for tomorrow at 10 AM. See you in the conference room."
        val result = engine.screen(notificationSnippet)

        assertEquals(RiskLevel.LOW, result.riskLevel)
        assertFalse(result.needsDeepVerify)
    }
}
