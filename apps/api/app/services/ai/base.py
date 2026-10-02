"""
Abstract AI provider interface — per AGENT_Final.md §15.2.

All Gemini SDK calls must flow through this boundary so providers
can be swapped without touching verification, ingestion, or fraud logic.
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract interface for all AI providers used by VeriFeed."""

    @abstractmethod
    def embed(self, text: str) -> list[float] | None:
        """Generate a dense vector embedding for the given text.
        Returns None if embedding cannot be produced.
        """
        ...

    @abstractmethod
    def generate(self, prompt: str) -> str | None:
        """Generate a plain-text response for the given prompt.
        Returns None on error.
        """
        ...

    @abstractmethod
    def generate_json(self, prompt: str) -> dict | None:
        """Generate a structured JSON response for the given prompt.
        Returns None on error.
        """
        ...

    @abstractmethod
    def extract_from_image(self, image_data: str, prompt: str = "Extract text and claims from this image") -> str:
        """Extract text/claims from a base64-encoded image using multimodal AI.
        Returns empty string on error.
        """
        ...

    @abstractmethod
    def extract_from_audio(self, audio_data: str, prompt: str = "Transcribe and extract claims from this audio") -> str:
        """Extract transcription, claims, tone, and language from a base64-encoded audio file/voice note.
        Returns empty string on error.
        """
        ...

    @abstractmethod
    def analyze_image_authenticity(self, image_data: str) -> dict:
        """Analyze image for synthetic AI generation, digital manipulation, or stock photo recycling.
        Returns dictionary with analysis results.
        """
        ...

