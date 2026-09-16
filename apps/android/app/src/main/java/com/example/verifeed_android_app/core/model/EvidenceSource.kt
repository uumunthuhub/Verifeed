package com.example.verifeed_android_app.core.model

import org.json.JSONObject

/**
 * A single piece of cited evidence supporting or refuting a claim
 * (from the Stage 2 verification pipeline).
 */
data class EvidenceSource(
    val title: String,
    val outlet: String,
    val url: String? = null,
    val type: String = "News Article",
    val snippet: String? = null,
) {
    companion object {
        fun fromJson(obj: JSONObject): EvidenceSource =
            EvidenceSource(
                title = obj.optString("title", ""),
                outlet = obj.optString("outlet", obj.optString("source_name", "Unknown")),
                url = if (obj.isNull("url")) null else obj.optString("url", null),
                type = obj.optString("type", "News Article"),
                snippet = if (obj.isNull("snippet")) null else obj.optString("snippet", null),
            )
    }
}