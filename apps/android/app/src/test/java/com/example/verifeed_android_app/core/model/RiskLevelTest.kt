package com.example.verifeed_android_app.core.model

import org.junit.Test
import org.junit.Assert.*

/**
 * Stage 1 risk level mapping (E3).
 */
class RiskLevelTest {

    @Test
    fun mapsBackendStrings() {
        assertEquals(RiskLevel.LOW, RiskLevel.fromApiString("Low"))
        assertEquals(RiskLevel.MEDIUM, RiskLevel.fromApiString("medium"))
        assertEquals(RiskLevel.HIGH, RiskLevel.fromApiString(" HIGH "))
        assertEquals(RiskLevel.MEDIUM, RiskLevel.fromApiString("Medium"))
    }

    @Test
    fun unknownOnGarbage() {
        assertEquals(RiskLevel.UNKNOWN, RiskLevel.fromApiString("maybe"))
        assertEquals(RiskLevel.UNKNOWN, RiskLevel.fromApiString(null))
        assertEquals(RiskLevel.UNKNOWN, RiskLevel.fromApiString(""))
    }
}