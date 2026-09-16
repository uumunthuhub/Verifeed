package com.example.verifeed_android_app.core.model

import org.json.JSONObject

/**
 * A single deterministic risk indicator detected by Stage 1 screening.
 * These are rule/pattern matches — never AI verdicts.
 */
data class FraudSignal(
    val signalType: String,
    val description: String,
    val matchedText: String? = null,
    val severity: String = "medium", // low | medium | high
) {
    companion object {
        val LOW: String = "low"
        val MEDIUM: String = "medium"
        val HIGH: String = "high"

        fun fromJson(obj: JSONObject): FraudSignal =
            FraudSignal(
                signalType = obj.optString("signal_type", "unknown"),
                description = obj.optString("description", ""),
                matchedText = if (obj.isNull("matched_text")) null else obj.optString("matched_text", null),
                severity = obj.optString("severity", MEDIUM),
            )

        fun listFromJson(obj: JSONObject): List<FraudSignal> {
            val arr = obj.optJSONArray("signals") ?: return emptyList()
            return (0 until arr.length()).map { i -> fromJson(arr.getJSONObject(i)) }
        }
    }
}