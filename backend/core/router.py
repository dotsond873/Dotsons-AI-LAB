class ModelRouter:
    """
    Routes requests to the appropriate AI capability.
    This will expand as Dotson Super AI gains additional models and tools.
    """

    def route(self, message: str) -> str:
        message_lower = message.lower()

        if any(word in message_lower for word in ["code", "python", "javascript", "program"]):
            return "coding"

        if any(word in message_lower for word in ["research", "search", "find", "latest"]):
            return "research"

        if any(word in message_lower for word in ["image", "picture", "photo", "draw"]):
            return "image"

        if any(word in message_lower for word in ["plan", "steps", "strategy"]):
            return "planning"

        return "general"


router = ModelRouter()
