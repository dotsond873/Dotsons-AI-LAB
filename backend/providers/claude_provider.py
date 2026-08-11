import os
from anthropic import AsyncAnthropic

from .base import AIProvider


class ClaudeProvider(AIProvider):
    """Claude provider for Dotson's Super AI."""

    name = "claude"

    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.content[0].text
