package com.example.verifeed_android_app.core.api

import com.example.verifeed_android_app.core.model.VerificationSummary
import java.io.File
import java.util.Base64

/**
 * Loads a screenshot file (typically produced by the OS Photo Picker via
 * `ActivityResultContracts.PickVisualMedia`), base64-encodes it and sends it
 * to `POST /api/v1/verify` for OCR + evidence-backed verification (E4).
 *
 * Pure-JVM implementation so the encode/verify flow is unit-testable.
 */
class ScreenshotVerifier(
    private val apiClient: VeriFeedApiClient = VeriFeedApiClient(),
) {

    /**
     * @param imageFile     A local image file (jpg/png/webp).
     * @param maxBytes      Safety cap to avoid uploading multi-GB captures (default 15 MB).
     */
    fun verifyImage(imageFile: File, maxBytes: Int = 15 * 1024 * 1024): VerificationSummary {
        val bytes = imageFile.readBytes()
        if (bytes.size > maxBytes) {
            throw IllegalStateException(
                "Screenshot is ${bytes.size / (1024 * 1024)} MB — over the $maxBytes byte limit.",
            )
        }
        val base64 = Base64.getEncoder().encodeToString(bytes)
        return apiClient.verify(
            query = null,
            imageDataBase64 = base64,
            fileName = imageFile.name,
        )
    }
}