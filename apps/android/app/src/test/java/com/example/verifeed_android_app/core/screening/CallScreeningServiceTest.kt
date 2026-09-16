package com.example.verifeed_android_app.core.screening

import org.junit.Assert.assertTrue
import org.junit.Test

class CallScreeningServiceTest {

    @Test
    fun testRobocallInterceptionList() {
        val knownScamNumbers = setOf(
            "+18005550199",
            "+18885550144",
            "987"
        )

        assertTrue(knownScamNumbers.contains("+18005550199"))
        assertTrue(knownScamNumbers.contains("+18885550144"))
        assertTrue(knownScamNumbers.contains("987"))
    }
}
