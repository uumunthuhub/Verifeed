package com.example.verifeed_android_app.core.util

/**
 * Truncates a string for compact UI display.
 * (Kotlin stdlib `String.preview` is only available since Kotlin 2.1.)
 */
fun previewText(text: String, maxLength: Int): String =
    if (text.length <= maxLength) text else text.substring(0, maxLength) + "…"