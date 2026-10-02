"""
Live Search Service — Real-Time Web & Breaking News Ingestion.

Per VeriFeed Architecture:
Ensures VeriFeed is not limited to static training data or local DB snapshots.
For breaking claims, wildlife escape rumors, emerging propaganda, or unindexed events,
this module searches live web feeds (Google News RSS & Web) to retrieve current
official statements, news reports, and fact-checks in real-time.
"""

import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any

logger = logging.getLogger(__name__)

PRESERVED_SHORT_TERMS = {"id", "ai", "tv", "5g", "3g", "4g", "sd", "uk", "us", "eu", "un", "mw", "qr"}
GENERIC_STOPWORDS = {
    "is", "it", "true", "that", "the", "in", "for", "a", "an", "of", "and", "or", "to",
    "currently", "recently", "now", "malawi", "malawian", "does", "do", "offer", "offering",
    "there", "this", "are", "have", "has", "check", "verify", "claim", "about", "with",
    "from", "your", "free", "more", "please", "tell", "show", "can", "will", "should", "where", "when", "why", "how"
}

# ---------------------------------------------------------------------------
# Topic category definitions
# Each category has:
#   keywords        — list[str] terms that strongly indicate this topic
#   exclusion_terms — list[str] terms whose presence in an article headline/excerpt
#                     indicate it is from a different, incompatible category
#   search_suffix   — str appended to the search query for topic-targeted expansion
# Note: values are a mix of list[str] and str, so the inner type is dict[str, Any].
# ---------------------------------------------------------------------------
TOPIC_CATEGORIES: dict[str, dict[str, Any]] = {
    "wildlife": {
        "keywords": [
            "lion", "tiger", "elephant", "leopard", "cheetah", "giraffe", "hippo",
            "crocodile", "snake", "rhino", "gorilla", "chimpanzee", "buffalo", "hyena",
            "zebra", "wildebeest", "antelope", "mongoose", "warthog", "baboon",
            "flamingo", "eagle", "hawk", "vulture", "pelican",
            "zoo", "safari", "game reserve", "national park", "wildlife", "animal",
            "escaped", "loose animal", "conservation", "poaching", "ranger",
        ],
        "exclusion_terms": [
            "reserve bank", "central bank", "interest rate", "kwacha", "forex",
            "budget", "taxation", "mra", "treasury", "parliament vote", "election",
            "stock market", "inflation", "cryptocurrency", "banking", "loan",
        ],
        "search_suffix": "wildlife nature animal",
    },
    "finance": {
        "keywords": [
            "bank", "kwacha", "mwk", "forex", "interest rate", "loan", "credit",
            "reserve bank", "rbm", "mra", "tax", "budget", "fiscal", "monetary",
            "inflation", "currency", "exchange rate", "stock", "investment", "salary",
            "pension", "insurance", "mobile money", "airtel money", "tnm mpamba",
        ],
        "exclusion_terms": [
            "lion", "elephant", "wildlife", "zoo", "safari", "national park",
            "animal", "escaped", "poaching", "conservation",
        ],
        "search_suffix": "finance economy banking",
    },
    "politics": {
        "keywords": [
            "president", "parliament", "election", "minister", "government", "party",
            "chakwera", "chilima", "mutharika", "mcp", "dpp", "utm", "vote",
            "constitution", "judiciary", "cabinet", "diplomat", "ambassador",
        ],
        "exclusion_terms": [
            "lion", "elephant", "wildlife", "zoo", "safari",
            "stock market", "cryptocurrency",
        ],
        "search_suffix": "politics government news",
    },
    "health": {
        "keywords": [
            "disease", "virus", "covid", "malaria", "cholera", "hiv", "aids",
            "vaccine", "outbreak", "epidemic", "pandemic", "hospital", "clinic",
            "doctor", "nurse", "medicine", "drug", "treatment", "health ministry",
            "who", "cdc", "moh",
        ],
        "exclusion_terms": [
            "lion", "wildlife", "zoo", "stock market", "cryptocurrency",
        ],
        "search_suffix": "health medical news",
    },
    "technology": {
        "keywords": [
            "5g", "internet", "smartphone", "app", "software", "ai", "artificial intelligence",
            "blockchain", "cryptocurrency", "bitcoin", "e-id", "digital", "cyber",
            "network", "data", "satellite", "drone", "robot", "computer",
        ],
        "exclusion_terms": [
            "lion", "wildlife", "zoo", "safari", "animal",
        ],
        "search_suffix": "technology digital news",
    },
    "crime": {
        "keywords": [
            "scam", "fraud", "theft", "robbery", "murder", "arrest", "police",
            "court", "trial", "sentence", "prison", "cybercrime", "phishing",
            "money laundering", "corruption", "bribery",
        ],
        "exclusion_terms": [
            "lion", "wildlife", "zoo",
        ],
        "search_suffix": "crime security news",
    },
    "sports": {
        "keywords": [
            "football", "soccer", "basketball", "cricket", "rugby", "athletics",
            "olympics", "world cup", "champions league", "premier league",
            "flames", "malawi national team", "match", "goal", "tournament",
        ],
        "exclusion_terms": [
            "wildlife", "zoo", "reserve bank", "taxation",
        ],
        "search_suffix": "sports news",
    },
}


def classify_query_topic(query: str) -> tuple[str, list[str], list[str]]:
    """
    Classify the query into a primary topic category.

    Returns:
        (category_name, search_suffix_terms, exclusion_terms)
        If no clear category is detected, returns ('general', [], []).
    """
    q_lower = query.lower()
    best_category = "general"
    best_score = 0

    for category, config in TOPIC_CATEGORIES.items():
        score = sum(1 for kw in config["keywords"] if kw in q_lower)
        if score > best_score:
            best_score = score
            best_category = category

    if best_category == "general" or best_score == 0:
        return "general", [], []

    config = TOPIC_CATEGORIES[best_category]
    suffix_words = str(config.get("search_suffix", "")).split()
    exclusions: list[str] = config.get("exclusion_terms", [])
    return best_category, suffix_words, exclusions

def is_article_topic_compatible(query: str, title: str, excerpt: str = "") -> bool:
    """
    Return False if the article's title/excerpt clearly belongs to a different
    topic category than the query. Returns True for general/unknown categories.
    """
    category, _suffix, exclusion_terms = classify_query_topic(query)
    if category == "general" or not exclusion_terms:
        return True  # can't determine topic — allow through

    text_to_check = f"{title} {excerpt}".lower()
    # If any exclusion term for this category appears in the article, reject it
    for excl in exclusion_terms:
        if excl in text_to_check:
            return False
    return True


def _safe_get_text(parent: ET.Element, tag: str, default: str = "") -> str:
    """Safely extract stripped text content from an XML element tag."""
    elem = parent.find(tag)
    if elem is not None and elem.text is not None:
        return elem.text.strip()
    return default


def extract_search_keywords(text: str) -> str:
    """Strip conversational phrasing to generate effective search query keywords."""
    if not text:
        return ""
    # Strip conversational prefixes
    prefix_pattern = (
        r"^(is it true that|is it true|is it real|did|has|who is|what is|can you verify|"
        r"check if|does|is there|are there|tell me if|do|can|will|should|where|when|why|how)\b"
    )
    clean = re.sub(prefix_pattern, "", text, flags=re.IGNORECASE).strip()
    
    # Retain hyphens in terms like e-id, e-passport
    raw_tokens = [w.strip(",.!?\"'") for w in clean.split()]
    significant: list[str] = []
    
    for token in raw_tokens:
        t_lower = token.lower()
        if not t_lower or t_lower in GENERIC_STOPWORDS:
            continue
        if len(t_lower) >= 3 or t_lower in PRESERVED_SHORT_TERMS or "-" in t_lower:
            significant.append(token)
            
    return " ".join(significant) if significant else clean


def is_article_relevant(query: str, title: str, excerpt: str = "") -> bool:
    """
    Verify if a retrieved news article is topically relevant to the claim query.

    Two-pass check:
    1. Topic-exclusion pass — if the article clearly belongs to a different
       category than the query (e.g. finance article for a wildlife query),
       reject it immediately.
    2. Subject-token pass — at least one meaningful keyword from the query
       must appear in the article title or excerpt.
    """
    if not query or not (title or excerpt):
        return False

    # Pass 1: cross-category exclusion
    if not is_article_topic_compatible(query, title, excerpt):
        logger.debug(
            "Topic-exclusion filter rejected article '%s' for query '%s'", title[:80], query[:80]
        )
        return False

    cleaned_query = re.sub(r"[^\w\s-]", " ", query.lower())
    tokens = [w.strip() for w in cleaned_query.split() if w.strip()]
    subject_tokens = [t for t in tokens if t not in GENERIC_STOPWORDS and (len(t) >= 2 or t in PRESERVED_SHORT_TERMS)]

    if not subject_tokens:
        return True

    text_to_check = f"{title} {excerpt}".lower()

    # Handle composite or acronym terms specifically
    query_lower = query.lower()
    if "e-id" in query_lower or "eid" in query_lower or "id" in subject_tokens:
        id_terms = ["e-id", "eid", "electronic id", "digital id", "national id", "identity", " id card", " id "]
        if any(term in text_to_check for term in id_terms):
            return True

    # Pass 2: at least one primary subject token must match
    return any(token in text_to_check for token in subject_tokens)


def search_live_web_news(query: str, limit: int = 6) -> list[dict[str, Any]]:
    """
    Fetch real-time live news coverage from live news RSS feeds.

    Query expansion is topic-aware: instead of blindly appending "Malawi",
    we classify the query topic and append category-appropriate search terms
    (e.g., "wildlife nature animal" for a lion query, "finance banking" for
    an RBM query). This ensures the RSS results match the claim's subject.

    Args:
        query: Search claim or headline keywords.
        limit: Maximum number of articles to return.

    Returns:
        List of evidence source dicts with title, outlet, url, published_date, type.
    """
    if not query or not query.strip():
        return []

    clean_query = query.strip()

    # Classify topic for context-appropriate query expansion
    topic_category, topic_suffix_words, _excl = classify_query_topic(clean_query)
    logger.info("Live search: detected topic category '%s' for query '%s'", topic_category, clean_query[:60])

    queries_to_try = [clean_query]

    # Add keyword-extracted fallback query
    kw_query = extract_search_keywords(clean_query)
    if kw_query and kw_query.lower() != clean_query.lower():
        queries_to_try.append(kw_query)
        # Topic-aware expansion: use category-specific suffix instead of generic "Malawi"
        if topic_suffix_words:
            topic_suffix = " ".join(topic_suffix_words)
            queries_to_try.append(f"{kw_query} {topic_suffix}")
        elif "malawi" not in kw_query.lower():
            # Fallback to regional targeting only when no topic suffix available
            queries_to_try.append(f"{kw_query} Malawi")

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for q_term in queries_to_try:
        if len(results) >= limit:
            break
        encoded_q = urllib.parse.quote(q_term)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=6) as response:
                xml_data = response.read()
                tree = ET.fromstring(xml_data)
                items = tree.findall(".//item")

                for item in items:
                    if len(results) >= limit:
                        break
                    raw_title = _safe_get_text(item, "title")
                    link = _safe_get_text(item, "link")
                    pub_date = _safe_get_text(item, "pubDate")
                    outlet = _safe_get_text(item, "source", default="Live News Media")

                    if link in seen_urls:
                        continue

                    # Unescape title
                    clean_title = unescape(raw_title)
                    if " - " in clean_title and outlet == "Live News Media":
                        parts = clean_title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        outlet = parts[1].strip()

                    excerpt = f"Live coverage from {outlet}: {clean_title}"
                    
                    # Verify subject relevance before accepting article
                    if not is_article_relevant(clean_query, clean_title, excerpt):
                        logger.debug("Skipping irrelevant live article: '%s' for query '%s'", clean_title, clean_query)
                        continue

                    seen_urls.add(link)
                    results.append({
                        "title": clean_title,
                        "headline": clean_title,
                        "outlet": outlet,
                        "url": link,
                        "published_date": pub_date,
                        "type": "Live Breaking News",
                        "trust_tier": 2,
                        "excerpt": excerpt,
                    })

                if results:
                    logger.info("Live search retrieved %d relevant articles for query '%s'", len(results), q_term[:50])
                    break

        except Exception as exc:
            logger.warning("Live web news search unavailable for query '%s': %s", q_term[:50], exc)

    return results


