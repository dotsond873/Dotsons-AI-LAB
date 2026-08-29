import os
from openai import AsyncOpenAI

from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI provider for Dotson's Super AI."""

    name = "openai"
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return response.output_text
