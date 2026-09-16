"""
AIService facade — the single entry point for AI functionality across VeriFeed.

Per AGENT_Final.md §15.2 and Blueprint §77.2:
All application code should depend on this service, not on provider-specific SDKs.
The provider is selected via the AI_PROVIDER environment variable.
"""

import os
from functools import lru_cache

from app.services.ai.base import AIProvider


@lru_cache(maxsize=1)
def get_ai_service() -> AIProvider:
    """Return the configured AI provider (singleton, cached on first call)."""
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    if provider == "gemini":
        from app.services.ai.gemini import GeminiProvider
        return GeminiProvider()
    raise ValueError(f"Unknown AI_PROVIDER: {provider!r}. Supported: 'gemini'")


# Re-export the abstract type for type annotations
AIService = AIProvider
