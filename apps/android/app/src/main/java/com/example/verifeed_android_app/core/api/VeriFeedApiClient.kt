package com.example.verifeed_android_app.core.api

import com.example.verifeed_android_app.core.model.ScreeningResult
import com.example.verifeed_android_app.core.model.VerificationSummary
import okhttp3.MediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.Response
import org.json.JSONObject
import java.time.Duration

/**
 * Thin OkHttp wrapper around the VeriFeed API.
 *
 * Stage 1: POST /api/v1/screen   — deterministic, no Gemini
 * Stage 2: POST /api/v1/verify   — evidence pipeline + Gemini synthesis
 *
 * All calls are blocking; callers MUST run them on [ApiExecutors] so the
 * UI thread is never stalled.
 */
class VeriFeedApiClient(
    private val baseUrl: String = ApiConfig.baseUrl,
    private val timeout: Duration = Duration.ofSeconds(ApiConfig.HTTP_TIMEOUT_SECONDS),
) {

    private val httpClient: OkHttpClient =
        OkHttpClient.Builder().callTimeout(timeout).build()

    // ------------------------------------------------------------------
    // Stage 1 — local screening via the API
    // ------------------------------------------------------------------

    /** POST /api/v1/screen. Throws on transport or HTTP errors. */
    fun screen(content: String, contentType: String = "message"): ScreeningResult {
        val body = JSONObject()
            .put("content", content)
            .put("content_type", contentType)
            .toString()

        val rawBody = executeSync("POST", ApiConfig.screenPath, body)
        return ScreeningResult.fromApiJson(rawBody)
    }

    // ------------------------------------------------------------------
    // Stage 2 — deep verification
    // ------------------------------------------------------------------

    /**
     * POST /api/v1/verify.
     *
     * @param query             Text to verify (SMS, email body, URL, claim...)
     * @param imageDataBase64   Optional base64 screenshot for OCR-based verification
     * @param fileName          Preferred file name for the screenshot
     * @param priorScreening    Optional Stage 1 result used as calibration context
     */
    fun verify(
        query: String? = null,
        imageDataBase64: String? = null,
        fileName: String? = null,
        priorScreening: ScreeningResult? = null,
    ): VerificationSummary {
        val body = JSONObject()
        if (query != null) {
            body.put("query", query)
        }
        if (imageDataBase64 != null) {
            body.put("image_data", imageDataBase64)
            body.put("file_name", fileName ?: "verifeed_screenshot")
        }
        priorScreening?.let { prior ->
            body.put(
                "prior_screening",
                JSONObject()
                    .put("risk_level", prior.riskLevel.name.capitalize())
                    .put("needs_deep_verify", prior.needsDeepVerify)
                    .put("recommended_action", prior.recommendedAction),
            )
        }

        val rawBody = executeSync("POST", ApiConfig.verifyPath, body.toString())
        return VerificationSummary.fromApiJson(rawBody)
    }

    // ------------------------------------------------------------------
    // Community reporting
    // ------------------------------------------------------------------

    /** POST /api/v1/verify/submit-scam. Returns true when the server accepted it. */
    fun reportScam(text: String): Boolean {
        val body = JSONObject().put("text", text).toString()
        val response = executeSync("POST", ApiConfig.reportScamPath, body)
        return JSONObject(response).optString("status", "") == "success"
    }

    // ------------------------------------------------------------------
    // HTTP plumbing
    // ------------------------------------------------------------------

    private fun executeSync(method: String, path: String, jsonBody: String): String {
        val request =
            Request.Builder()
                .url(baseUrl + path)
                .header("Accept", "application/json")
                .header("Content-Type", "application/json; charset=utf-8")
                .method(method, RequestBody.create(null, jsonBody))
                .build()

        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                throw IllegalStateException("VeriFeed API error ${response.code} for $path")
            }
            return response.body!!.string()
        }
    }
}