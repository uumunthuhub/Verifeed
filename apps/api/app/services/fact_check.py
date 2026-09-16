import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GOOGLE_FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

async def search_google_fact_check(query: str) -> list[dict[str, Any]]:
    """
    Search the Google Fact Check Tools API for claims matching the query.
    Returns a list of structured fact-check results.
    If GOOGLE_FACT_CHECK_API_KEY is not configured or request fails, returns empty list safely.
    """
    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
    if not api_key:
        logger.info("GOOGLE_FACT_CHECK_API_KEY is not set. Skipping external Google Fact Check lookup.")
        return []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                GOOGLE_FACT_CHECK_API_URL,
                params={
                    "query": query,
                    "key": api_key,
                    "languageCode": "en",
                }
            )
            if response.status_code != 200:
                logger.warning(f"Google Fact Check API returned status code {response.status_code}")
                return []

            data = response.json()
            claims = data.get("claims", [])
            results = []

            for claim in claims:
                text = claim.get("text", "")
                claimant = claim.get("claimant", "Unknown")
                reviews = claim.get("claimReview", [])
                
                for review in reviews:
                    publisher = review.get("publisher", {}).get("name", "Fact-Checker")
                    url = review.get("url", "")
                    title = review.get("title", "")
                    rating = review.get("textualRating", "Unspecified")

                    results.append({
                        "claim_text": text,
                        "claimant": claimant,
                        "publisher": publisher,
                        "title": title,
                        "url": url,
                        "rating": rating,
                    })

            return results
    except Exception as e:
        logger.error(f"Error querying Google Fact Check API: {e}")
        return []
