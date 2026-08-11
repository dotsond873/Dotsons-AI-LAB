from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for every AI model connected to Dotson's Super AI."""

    name = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Send a prompt to the AI provider and return its response."""
        pass
