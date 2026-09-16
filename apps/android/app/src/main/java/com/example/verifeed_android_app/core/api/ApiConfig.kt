package com.example.verifeed_android_app.core.api

/**
 * Central API configuration for the VeriFeed Android app.
 *
 * NOTE: `http://10.0.2.2:8000` is the Android Emulator → host loopback alias,
 * suitable for local development against `uv run uvicorn` on the host.
 * Production builds MUST point at an HTTPS endpoint and drop
 * `android:usesCleartextTraffic` from the manifest.
 */
object ApiConfig {
    const val DEFAULT_BASE_URL: String = "http://10.0.2.2:8000"

    val baseUrl: String = DEFAULT_BASE_URL
    val screenPath: String = "/api/v1/screen"
    val verifyPath: String = "/api/v1/verify"
    val reportScamPath: String = "/api/v1/verify/submit-scam"
    const val HTTP_TIMEOUT_SECONDS: Long = 20

    /** When true the client calls the remote Stage 1 endpoint; local engine is always run first. */
    var useRemoteStage1: Boolean = true
}