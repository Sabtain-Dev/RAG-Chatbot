import threading
from collections import OrderedDict, deque
from typing import Deque, Dict, List

MAX_MESSAGES_PER_SESSION = 6

# Caps how many DISTINCT sessions are held in memory at once — without this,
# an attacker (or just a lot of real traffic) sending unlimited unique
# session_ids grows memory forever, since each new session_id was previously
# accepted with no upper bound. Chosen conservatively for a 512MB instance.
MAX_TOTAL_SESSIONS = 500


class ConversationMemory:
    """
    In-process, in-RAM conversation store keyed by session_id.
    Deliberately NOT persistent. Bounded on two axes:
    - per-session message count (deque maxlen)
    - total number of sessions held (LRU eviction via OrderedDict)
    """

    def __init__(self, max_messages: int = MAX_MESSAGES_PER_SESSION, max_sessions: int = MAX_TOTAL_SESSIONS):
        self.max_messages = max_messages
        self.max_sessions = max_sessions
        self.conversations: "OrderedDict[str, Deque[dict]]" = OrderedDict()
        self._lock = threading.Lock()

    def _touch(self, session_id: str) -> None:
        """Marks a session as recently used and creates it if new, evicting
        the oldest session first if we're at capacity."""
        if session_id in self.conversations:
            self.conversations.move_to_end(session_id)
            return

        if len(self.conversations) >= self.max_sessions:
            self.conversations.popitem(last=False)  # evict least-recently-used

        self.conversations[session_id] = deque(maxlen=self.max_messages)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._touch(session_id)
            self.conversations[session_id].append({"role": role, "content": content})

    def get_history(self, session_id: str) -> List[dict]:
        with self._lock:
            if session_id not in self.conversations:
                return []
            self.conversations.move_to_end(session_id)
            return list(self.conversations[session_id])

    def clear(self, session_id: str) -> None:
        with self._lock:
            self.conversations.pop(session_id, None)


memory = ConversationMemory()