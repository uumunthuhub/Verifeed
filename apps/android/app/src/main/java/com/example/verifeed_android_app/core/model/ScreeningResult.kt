package com.example.verifeed_android_app.core.model

import org.json.JSONArray
import org.json.JSONObject

/**
 * Stage 1 screening result. Produced either by the on-device engine
 * (source = LOCAL) or by the VeriFeed Stage 1 API (source = REMOTE).
 *
 * Trust boundary (per architecture): LOCAL SIGNALS ≠ VERIFIED EVIDENCE.
 * A High risk here is a *signal* that deep (Stage 2) verification is warranted —
 * it is never a "Confirmed Scam" verdict.
 */
data class ScreeningResult(
    val riskLevel: RiskLevel,
    val signals: List<FraudSignal> = emptyList(),
    val patternMatches: List<String> = emptyList(),
    val needsDeepVerify: Boolean = false,
    val recommendedAction: String = "",
    val screenedUrls: List<String> = emptyList(),
    val detectedInstitutions: List<String> = emptyList(),
    val source: Stage1Source = Stage1Source.LOCAL,
) {

    /** Whether the result came from the on-device engine or the VeriFeed API. */
    enum class Stage1Source {
        LOCAL,
        REMOTE,
    }

    companion object {

        fun fromApiJson(body: String): ScreeningResult = fromApiObject(JSONObject(body))

        fun fromApiObject(root: JSONObject): ScreeningResult =
            ScreeningResult(
                riskLevel = RiskLevel.fromApiString(root.optString("risk_level", null)),
                signals = FraudSignal.listFromJson(root),
                patternMatches = optStringList(root, "pattern_matches"),
                needsDeepVerify = root.optBoolean("needs_deep_verify", false),
                recommendedAction = root.optString("recommended_action", ""),
                screenedUrls = optStringList(root, "screened_urls"),
                detectedInstitutions = optStringList(root, "detected_institutions"),
                source = Stage1Source.REMOTE,
            )

        private fun optStringList(root: JSONObject, key: String): List<String> {
            val arr = root.optJSONArray(key) ?: return emptyList()
            return (0 until arr.length())
                .map { i -> arr.optString(i, "") }
                .filter { it.isNotEmpty() }
        }
    }
}