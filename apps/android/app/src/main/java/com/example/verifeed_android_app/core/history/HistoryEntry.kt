package com.example.verifeed_android_app.core.history

import org.json.JSONObject

/**
 * A single entry in the local investigation history (E7).
 *
 * Currently a local-only cache; syncing with the backend is deferred until
 * authentication lands (Phase F). Kept serializable to JSON so the store
 * can later be swapped for Room DB without touching callers.
 */
data class HistoryEntry(
    val id: String,
    val query: String,
    val createdAtEpochMillis: Long,
    val riskLevel: String? = null,
    val verdict: String? = null,
    val claimVerdict: String? = null,
    val messageAuthenticityVerdict: String? = null,
    val confidenceScore: Double? = null,
    val summary: String? = null,
) {
    companion object {

        fun fromScreening(query: String, riskLevel: String): HistoryEntry =
            HistoryEntry(
                id = java.util.UUID.randomUUID().toString(),
                query = query,
                createdAtEpochMillis = System.currentTimeMillis(),
                riskLevel = riskLevel,
            )

        fun fromVerification(query: String, verification: com.example.verifeed_android_app.core.model.VerificationSummary): HistoryEntry =
            HistoryEntry(
                id = java.util.UUID.randomUUID().toString(),
                query = query,
                createdAtEpochMillis = System.currentTimeMillis(),
                riskLevel = verification.riskLevel,
                verdict = verification.verdict,
                claimVerdict = verification.claimVerdict,
                messageAuthenticityVerdict = verification.messageAuthenticityVerdict,
                confidenceScore = verification.confidenceScore,
                summary = verification.summary,
            )

        fun toJson(entry: HistoryEntry): JSONObject =
            JSONObject()
                .put("id", entry.id)
                .put("query", entry.query)
                .put("created_at", entry.createdAtEpochMillis)
                .putOpt("risk_level", entry.riskLevel)
                .putOpt("verdict", entry.verdict)
                .putOpt("claim_verdict", entry.claimVerdict)
                .putOpt("message_authenticity_verdict", entry.messageAuthenticityVerdict)
                .putOpt("confidence", entry.confidenceScore)
                .putOpt("summary", entry.summary)

        fun fromJson(obj: JSONObject): HistoryEntry =
            HistoryEntry(
                id = obj.optString("id", java.util.UUID.randomUUID().toString()),
                query = obj.optString("query", ""),
                createdAtEpochMillis = obj.optLong("created_at", System.currentTimeMillis()),
                riskLevel = if (obj.isNull("risk_level")) null else obj.optString("risk_level", null),
                verdict = if (obj.isNull("verdict")) null else obj.optString("verdict", null),
                claimVerdict = if (obj.isNull("claim_verdict")) null else obj.optString("claim_verdict", null),
                messageAuthenticityVerdict =
                    if (obj.isNull("message_authenticity_verdict")) null
                    else obj.optString("message_authenticity_verdict", null),
                confidenceScore =
                    if (obj.isNull("confidence")) null else obj.optDouble("confidence", 0.0),
                summary = if (obj.isNull("summary")) null else obj.optString("summary", null),
            )
    }
}