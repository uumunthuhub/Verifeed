package com.example.verifeed_android_app.core.screening

import com.example.verifeed_android_app.core.model.RiskLevel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class EmailScreenerTest {

    @Test
    fun testDomainSpoofingDetection() {
        val screener = EmailScreener()
        val result = screener.screenEmail(
            senderAddress = "security@scam-domain.com",
            displayName = "PayPal Support",
            subject = "Urgent: Account Suspended",
            body = "Click http://bit.ly/verify to unlock your PayPal account immediately."
        )

        assertEquals(RiskLevel.HIGH, result.riskLevel)
        assertTrue(result.patternMatches.any { it.contains("Spoof Alert") })
        assertTrue(result.needsDeepVerify)
    }

    @Test
    fun testAuthenticEmailScreening() {
        val screener = EmailScreener()
        val result = screener.screenEmail(
            senderAddress = "service@paypal.com",
            displayName = "PayPal",
            subject = "Your receipt for transaction",
            body = "Your receipt is available in your account dashboard."
        )

        assertEquals(RiskLevel.LOW, result.riskLevel)
        assertTrue(result.signals.isEmpty())
    }
}
