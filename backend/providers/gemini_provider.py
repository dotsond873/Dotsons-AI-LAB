import os
from google import genai

from .base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini provider for Dotson's Super AI."""

    name = "gemini"

    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.aio.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            contents=prompt,
        )

        return response.text
