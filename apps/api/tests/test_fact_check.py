"""Unit tests for the Google Fact Check Tools API service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.fact_check import search_google_fact_check


@pytest.mark.asyncio
async def test_search_fact_check_without_api_key(monkeypatch):
    """When API key is not set, search_google_fact_check should return empty list gracefully."""
    monkeypatch.delenv("GOOGLE_FACT_CHECK_API_KEY", raising=False)
    results = await search_google_fact_check("vaccine microchip rumor")
    assert results == []


@pytest.mark.asyncio
async def test_search_fact_check_success(monkeypatch):
    """Verify parsing of valid Google Fact Check API response."""
    monkeypatch.setenv("GOOGLE_FACT_CHECK_API_KEY", "test_key")

    mock_response_data = {
        "claims": [
            {
                "text": "The government is injecting microchips in vaccines",
                "claimant": "Social Media Posts",
                "claimReview": [
                    {
                        "publisher": {"name": "Snopes"},
                        "url": "https://www.snopes.com/fact-check/vaccine-microchip",
                        "title": "Claim about vaccine microchips is false",
                        "textualRating": "False",
                    }
                ],
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await search_google_fact_check("vaccine microchip")
        assert len(results) == 1
        assert results[0]["publisher"] == "Snopes"
        assert results[0]["rating"] == "False"
        assert results[0]["url"] == "https://www.snopes.com/fact-check/vaccine-microchip"
