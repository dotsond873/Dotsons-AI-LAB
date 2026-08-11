from datetime import datetime
from typing import Dict, List


class MemoryEngine:
    """
    Basic in-memory storage for Dotson Super AI.

    This is the first version of the memory system.
    Later versions can connect to a database and long-term memory.
    """

    def __init__(self):
        self.conversations: Dict[str, List[dict]] = {}

    def add_message(self, session_id: str, role: str, content: str) -> dict:
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        memory_item = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.conversations[session_id].append(memory_item)
        return memory_item

    def get_history(self, session_id: str) -> List[dict]:
        return self.conversations.get(session_id, [])

    def clear_history(self, session_id: str) -> bool:
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True

        return False


memory = MemoryEngine()
