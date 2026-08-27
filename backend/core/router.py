class ODBRouter:
    """
    Capability router for ODB SHADY 6.9.

    This router does NOT choose between paid AI providers.
    It decides what kind of capability the request needs.
    """

    def route(self, message: str) -> str:
        message_lower = message.lower()

        serious_words = [
            "suicide",
            "kill myself",
            "overdose",
            "emergency",
            "heart attack",
            "stroke",
            "bleeding",
            "abuse",
            "grief",
            "died",
            "death",
            "funeral",
            "depressed",
            "panic attack",
        ]

        if any(term in message_lower for term in serious_words):
            return "serious"

        if any(
            term in message_lower
            for term in ["image", "picture", "photo", "draw", "generate a scene"]
        ):
            return "image"

        if any(
            term in message_lower
            for term in ["search", "research", "find", "latest", "look up", "news"]
        ):
            return "web"

        if any(
            term in message_lower
            for term in ["voice", "speak", "say this", "read this aloud", "audio"]
        ):
            return "voice"

        if any(
            term in message_lower
            for term in ["admin", "users", "subscription", "billing", "payment"]
        ):
            return "admin"

        return "chat"


router = ODBRouter()
