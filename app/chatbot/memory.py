from collections import defaultdict, deque
from typing import Deque, Dict, List

# Caps how many messages (not characters) are kept per session. 6 messages =
# 3 user/assistant exchanges. This is a hard ceiling, not a tuning knob you
# need to touch — it exists so a long-running conversation doesn't silently
# blow past num_ctx and get silently truncated/degraded by Ollama.
MAX_MESSAGES_PER_SESSION = 6


class ConversationMemory:
    """
    In-process, in-RAM conversation store keyed by session_id.
    Deliberately NOT persistent — see Day 7 Part 11. Each session's deque
    auto-evicts its oldest message once MAX_MESSAGES_PER_SESSION is hit, so
    memory usage per session is bounded regardless of conversation length.
    """

    def __init__(self, max_messages: int = MAX_MESSAGES_PER_SESSION):
        self.max_messages = max_messages
        self.conversations: Dict[str, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=self.max_messages)
        )

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.conversations[session_id].append({"role": role, "content": content})

    def get_history(self, session_id: str) -> List[dict]:
        return list(self.conversations.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self.conversations.pop(session_id, None)


# Global instance — shared by RAGService for the life of the FastAPI process.
memory = ConversationMemory()