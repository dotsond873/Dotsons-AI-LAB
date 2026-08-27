import os
import httpx

from .base import AIProvider


class LocalProvider(AIProvider):
    """Local AI provider for ODB SHADY 6.9."""

    name = "local"

    def __init__(self):
        self.base_url = os.getenv(
            "ODB_MODEL_URL",
            "http://localhost:11434/api/chat"
        )
        self.model = os.getenv(
            "ODB_LOCAL_MODEL",
            "llama3.2"
        )

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                json=payload
            )
            response.raise_for_status()

        data = response.json()

        return data["message"]["content"]
