"""
GeminiProvider — Google Gemini implementation of AIProvider.

Per AGENT_Final.md §15.2: Gemini SDK must not be called directly from
route handlers, repositories, or application services. All SDK usage
is encapsulated here.

Per Blueprint §77.2: models and API key are loaded from environment
variables (GEMINI_API_KEY, GEMINI_MODEL).
"""

import base64
import io
import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class GeminiProvider(AIProvider):
    """Gemini implementation using the google.genai SDK."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — AI features will be degraded.")
            self._client = None
            return

        from google import genai
        from google.genai import types

        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._types = types

    def embed(self, text: str) -> list[float] | None:
        if not self._client or not text.strip():
            return None
        try:
            config = None
            if hasattr(self._types, "EmbedContentConfig"):
                config = self._types.EmbedContentConfig(output_dimensionality=768)
            res = self._client.models.embed_content(
                model=GEMINI_EMBED_MODEL,
                contents=text,
                config=config,
            )
            if res.embeddings and len(res.embeddings) > 0:
                first = res.embeddings[0]
                values = getattr(first, "values", None) or first.values
                if values is not None:
                    return [float(v) for v in values]
            return None
        except Exception as exc:
            logger.error("Gemini embed error: %s", exc)
            return None

    def generate(self, prompt: str) -> str | None:
        if not self._client:
            return None
        try:
            res = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return res.text.strip() if res.text else None
        except Exception as exc:
            logger.error("Gemini generate error: %s", exc)
            return None

    def generate_json(self, prompt: str) -> dict | None:
        if not self._client:
            return None
        try:
            res = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            if res.text is not None:
                return json.loads(res.text)
            return None
        except Exception as exc:
            logger.error("Gemini generate_json error: %s", exc)
            return None

    def extract_from_image(self, image_data: str, prompt: str) -> str:
        if not self._client or not image_data:
            return ""
        try:
            from PIL import Image

            b64_str = image_data.split(",")[1] if "," in image_data else image_data
            img_bytes = base64.b64decode(b64_str)
            img = Image.open(io.BytesIO(img_bytes))

            res = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, img],
            )
            return res.text.strip() if res and res.text else ""
        except Exception as exc:
            logger.error("Gemini extract_from_image error: %s", exc)
            return ""
