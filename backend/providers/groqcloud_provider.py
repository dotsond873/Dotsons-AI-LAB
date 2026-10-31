import os
from openai import AsyncOpenAI

from .base import AIProvider


class GroqCloudProvider(AIProvider):
    """GroqCloud provider for ODB SHADY 6.9."""

    name = "groqcloud"
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def __init__(self):
        self.client = None
        key = os.getenv("GROQ_API_KEY")
        if key:
            self.client = AsyncOpenAI(
                api_key=key,
                timeout=60.0,
                max_retries=1,
                base_url="https://api.groq.com/openai/v1",
            )

    async def generate(self, prompt: str) -> str:
        if self.client is None:
            raise RuntimeError("Set GROQ_API_KEY in the server environment to enable chat.")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The chat provider returned an empty reply. Please try again.")
        return content
