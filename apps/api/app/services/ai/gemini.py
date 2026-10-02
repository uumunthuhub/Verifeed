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
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
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
        config = None
        if hasattr(self._types, "EmbedContentConfig"):
            config = self._types.EmbedContentConfig(output_dimensionality=768)

        # Fallback candidates for embedding model names
        candidates = [GEMINI_EMBED_MODEL, "gemini-embedding-001", "text-embedding-004", "embedding-001"]
        # De-duplicate while preserving order
        unique_candidates = list(dict.fromkeys(candidates))

        for model_name in unique_candidates:
            try:
                res = self._client.models.embed_content(
                    model=model_name,
                    contents=text,
                    config=config,
                )
                if res.embeddings and len(res.embeddings) > 0:
                    first = res.embeddings[0]
                    values = getattr(first, "values", None) or first.values
                    if values is not None:
                        return [float(v) for v in values]
            except Exception as exc:
                logger.debug("Gemini embed failed with model '%s': %s", model_name, exc)
                continue

        logger.warning("Gemini embed unavailable across all candidate models.")
        return None

    def generate(self, prompt: str) -> str | None:
        if not self._client:
            return None
        import time
        for attempt in range(3):
            try:
                res = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                return res.text.strip() if res.text else None
            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    wait_sec = (attempt + 1) * 3
                    logger.warning("Gemini 429 rate limit in generate. Waiting %ds before retry %d/3...", wait_sec, attempt + 1)
                    time.sleep(wait_sec)
                else:
                    logger.error("Gemini generate error: %s", exc)
                    break
        return None

    def generate_json(self, prompt: str) -> dict | None:
        if not self._client:
            return None
        import time
        for attempt in range(3):
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
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    wait_sec = (attempt + 1) * 3
                    logger.warning("Gemini 429 rate limit in generate_json. Waiting %ds before retry %d/3...", wait_sec, attempt + 1)
                    time.sleep(wait_sec)
                else:
                    logger.error("Gemini generate_json error: %s", exc)
                    break
        return None

    def extract_from_image(self, image_data: str, prompt: str = "Extract text and claims from this image") -> str:
        if not self._client or not image_data:
            return ""
        import time
        from PIL import Image

        b64_str = image_data.split(",")[1] if "," in image_data else image_data
        img_bytes = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(img_bytes))

        for attempt in range(3):
            try:
                res = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[prompt, img],
                )
                return res.text.strip() if res and res.text else ""
            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    wait_sec = (attempt + 1) * 3
                    logger.warning("Gemini 429 rate limit hit. Waiting %ds before retry %d/3...", wait_sec, attempt + 1)
                    time.sleep(wait_sec)
                else:
                    logger.error("Gemini extract_from_image error: %s", exc)
                    break
        return ""

    def extract_from_audio(self, audio_data: str, prompt: str = "Transcribe and extract claims from this audio") -> str:
        if not self._client or not audio_data:
            return ""
        try:
            b64_str = audio_data.split(",")[1] if "," in audio_data else audio_data
            audio_bytes = base64.b64decode(b64_str)

            mime_type = "audio/mp3"
            if "data:audio/wav" in audio_data:
                mime_type = "audio/wav"
            elif "data:audio/ogg" in audio_data:
                mime_type = "audio/ogg"
            elif "data:audio/m4a" in audio_data:
                mime_type = "audio/m4a"
            elif "data:audio/aac" in audio_data:
                mime_type = "audio/aac"

            part = self._types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            res = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, part],
            )
            return res.text.strip() if res and res.text else ""
        except Exception as exc:
            logger.error("Gemini extract_from_audio error: %s", exc)
            return ""

    def analyze_image_authenticity(self, image_data: str) -> dict:
        if not self._client or not image_data:
            return {"is_ai_generated": False, "confidence": 0.0, "reason": "No image data"}
        try:
            from PIL import Image

            b64_str = image_data.split(",")[1] if "," in image_data else image_data
            img_bytes = base64.b64decode(b64_str)
            img = Image.open(io.BytesIO(img_bytes))

            prompt = """Analyze this image for signs of synthetic AI generation (Midjourney, DALL-E, Stable Diffusion, anatomical distortion, synthetic lighting, digital painting artifacts) OR stock photo recycling misattribution.

Return ONLY a JSON object:
{
  "is_ai_generated": true,
  "confidence": 0.9,
  "verdict_label": "AI Generated Image",
  "detected_artifacts": ["Unnatural textures", "Anatomical inconsistencies"],
  "analysis_explanation": "Detailed visual analysis explanation..."
}"""
            res = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, img],
                config=self._types.GenerateContentConfig(response_mime_type="application/json"),
            )
            if res and res.text:
                return json.loads(res.text)
            return {"is_ai_generated": False, "confidence": 0.0, "reason": "No response"}
        except Exception as exc:
            logger.error("Gemini analyze_image_authenticity error: %s", exc)
            return {"is_ai_generated": False, "confidence": 0.0, "reason": str(exc)}

