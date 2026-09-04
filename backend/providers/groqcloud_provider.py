import os
from openai import AsyncOpenAI

from .base import AIProvider


class GroqCloudProvider(AIProvider):
    """GroqCloud provider for ODB SHADY 6.9."""

    name = "groqcloud"
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content