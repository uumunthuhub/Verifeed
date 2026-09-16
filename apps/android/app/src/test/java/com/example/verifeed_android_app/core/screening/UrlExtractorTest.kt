package com.example.verifeed_android_app.core.screening

import org.junit.Test
import org.junit.Assert.*

/**
 * URL extraction (E5) — powers URL screening of pasted content.
 */
class UrlExtractorTest {

    @Test
    fun extractsFullUrls() {
        val urls = UrlExtractor.extractUrls("Visit https://example.com/claim or http://bit.ly/abc today")
        assertTrue(urls.contains("https://example.com/claim"))
        assertTrue(urls.contains("http://bit.ly/abc"))
    }

    @Test
    fun extractsWwwAndBareDomains() {
        val urls = UrlExtractor.extractUrls("Check www.airtel-mw.xyz and standard-bank-mw.com/verify now")
        assertTrue(urls.any { it.contains("airtel-mw.xyz") })
        assertTrue(urls.any { it.contains("standard-bank-mw.com/verify") })
    }

    @Test
    fun deduplicatesUrls() {
        val urls = UrlExtractor.extractUrls("Click https://tinyurl.com/abc twice: https://tinyurl.com/abc")
        assertEquals(1, urls.count { it.lowercase() == "https://tinyurl.com/abc" })
    }

    @Test
    fun ignoresPlainWordsTail() {
        // Lorem-ipsum sentences with common words must not be flagged as URLs.
        val urls = UrlExtractor.extractUrls("I went home. The bank is open. Call me please.")
        assertTrue(urls.isEmpty())
    }
}