package com.example.verifeed_android_app.core.screening

/**
 * Extracts candidate URLs from free text so each can be screened
 * by the Stage 1 engine (E5).
 *
 * Matches `http(s)://...` and bare `www.` links; then a light-weight pass
 * for `domain.tld` tokens such as those embedded in SMS messages.
 */
object UrlExtractor {

    private val FULL_URL = Regex(
        """https?://[\p{L}\p{N}\-_\.~%!$&'()*+,;=:@/\[\]]+|www\.[\p{L}\p{N}\-_\.~%!$&'()*+,;=:@/\[\]]+""",
        setOf(RegexOption.IGNORE_CASE, RegexOption.MULTILINE),
    )

    private val BARE_DOMAIN = Regex(
        """(?:[a-z0-9\-]+\.)+[a-z]{2,}(?::[0-9]{1,5})?(?:/[^\s"'<>]+)?""",
        setOf(RegexOption.IGNORE_CASE, RegexOption.MULTILINE),
    )

    /** Common TLDs unlikely to be plain words inside a message. */
    private val TLD_HINT = Regex(
        """\.(?:com|org|net|co|info|biz|io|xyz|app|online|site|gov|edu|mil|africa|mw|uk|us|za|ke|ng|tz)(?:/|$|\\s)""",
        setOf(RegexOption.IGNORE_CASE),
    )

    /** All unique candidate URLs found in a message, in order of appearance. */
    fun extractUrls(text: String): List<String> {
        val fullMatches = FULL_URL.findAll(text).map { it.value }.toList()
        val bareMatches =
            BARE_DOMAIN.findAll(text)
                .map { it.value }
                .filter { candidate -> TLD_HINT.containsMatchIn(candidate) }
                .toList()
                .filter { candidate -> fullMatches.none { it.equals(candidate, ignoreCase = true) } }

        return (fullMatches + bareMatches).distinctBy { it.lowercase() }
    }

    /** Shortcut used by the local engine. */
    fun hasUrl(text: String): Boolean = extractUrls(text).isNotEmpty()
}