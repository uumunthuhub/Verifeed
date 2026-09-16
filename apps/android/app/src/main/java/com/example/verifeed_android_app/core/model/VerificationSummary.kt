package com.example.verifeed_android_app.core.model

import org.json.JSONArray
import org.json.JSONObject

/**
 * Stage 2 (deep) verification result — the full evidence-backed verdict
 * returned by `POST /api/v1/verify`.
 *
 * Dual-verdict system:
 * - claimVerdict: truth status of the underlying claim
 * - messageAuthenticityVerdict: channel/sender authenticity
 */
data class VerificationSummary(
    val id: Int,
    val query: String,
    val verdict: String,
    val claimVerdict: String? = null,
    val messageAuthenticityVerdict: String? = null,
    val confidenceScore: Double = 0.0,
    val riskLevel: String? = null,
    val summary: String = "",
    val sources: List<EvidenceSource> = emptyList(),
    val extractedSender: String? = null,
    val extractedNumbers: List<String> = emptyList(),
    val extractedUrls: List<String> = emptyList(),
    val extractedInstitutions: List<String> = emptyList(),
    val recommendedActions: List<String> = emptyList(),
    val methodology: String? = null,
    val createdAt: String = "",
) {
    companion object {

        fun fromApiJson(body: String): VerificationSummary =
            fromApiObject(JSONObject(body))

        fun fromApiObject(root: JSONObject): VerificationSummary =
            VerificationSummary(
                id = root.optInt("id", 0),
                query = root.optString("query", ""),
                verdict = root.optString("verdict", "No Coverage Found"),
                claimVerdict = root.optNullableString("claim_verdict"),
                messageAuthenticityVerdict = root.optNullableString("message_authenticity_verdict"),
                confidenceScore = root.optDouble("confidence_score", 0.0),
                riskLevel = root.optNullableString("risk_level"),
                summary = root.optString("summary", ""),
                sources = parseSources(root),
                extractedSender = root.optNullableString("extracted_sender"),
                extractedNumbers = optStringList(root, "extracted_numbers"),
                extractedUrls = optStringList(root, "extracted_urls"),
                extractedInstitutions = optStringList(root, "extracted_institutions"),
                recommendedActions = parseRecommendedActions(root),
                methodology = root.optNullableString("methodology"),
                createdAt = root.optString("created_at", ""),
            )

        private fun parseSources(root: JSONObject): List<EvidenceSource> {
            val arr = root.optJSONArray("sources") ?: return emptyList()
            return (0 until arr.length()).map { i -> EvidenceSource.fromJson(arr.getJSONObject(i)) }
        }

        private fun parseRecommendedActions(root: JSONObject): List<String> {
            val arr = root.optJSONArray("recommended_actions") ?: return emptyList()
            return (0 until arr.length()).map { i ->
                val item = arr.get(i)
                when (item) {
                    is JSONObject -> item.optString("action", "")
                    is String -> item
                    else -> ""
                }
            }.filter { it.isNotEmpty() }
        }

        private fun optStringList(root: JSONObject, key: String): List<String> {
            val arr = root.optJSONArray(key) ?: return emptyList()
            return (0 until arr.length())
                .map { i -> arr.optString(i, "") }
                .filter { it.isNotEmpty() }
        }
    }
}

/** Small extension helpers for org.json in a Kotlin-friendly shape. */
private fun JSONObject.optNullableString(key: String): String? =
    if (isNull(key)) null else optString(key, null)