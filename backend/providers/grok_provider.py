import os
from openai import AsyncOpenAI

from .base import AIProvider


class GrokProvider(AIProvider):
    """xAI Grok provider for Dotson's Super AI."""

    name = "grok"
    model = os.getenv("XAI_MODEL", "grok-4")
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=os.getenv("XAI_MODEL", "grok-4"),
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content
