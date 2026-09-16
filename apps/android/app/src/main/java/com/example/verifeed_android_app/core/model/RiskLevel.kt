package com.example.verifeed_android_app.core.model

/**
 * Stage 1 risk classification, mirroring the VeriFeed backend
 * (`app/services/local_screening.py` returns "Low" | "Medium" | "High").
 *
 * Verdict trust boundary: this is a LOCAL SIGNAL — never a final verdict.
 */
enum class RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    UNKNOWN;

    companion object {
        /** Maps the backend's case-insensitive string form to a RiskLevel. */
        fun fromApiString(value: String?): RiskLevel =
            when (value?.trim()?.lowercase()) {
                "low" -> LOW
                "medium" -> MEDIUM
                "high" -> HIGH
                else -> UNKNOWN
            }
    }
}