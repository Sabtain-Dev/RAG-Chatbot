import time
import threading
from collections import deque
from typing import Generator, List, Optional, Dict
from groq import Groq
from app.chatbot.prompts import SYSTEM_PROMPT
from app.core.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


class GroqRateLimiter:
    """
    Throttles OUTGOING calls to Groq to stay under its 30 requests/minute
    limit — this is what actually prevents "1000 users at once" from
    breaking the chatbot: instead of all requests hitting Groq
    simultaneously and getting rejected, they queue briefly and go out at
    a safe, steady rate. Set to 25/min, leaving headroom under Groq's cap.
    """

    def __init__(self, max_calls: int = 25, period_seconds: float = 60.0):
        self.max_calls = max_calls
        self.period = period_seconds
        self.call_times: deque = deque()
        self._lock = threading.Lock()

    def wait_for_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self.call_times and now - self.call_times[0] > self.period:
                self.call_times.popleft()

            if len(self.call_times) >= self.max_calls:
                sleep_time = self.period - (now - self.call_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                now = time.monotonic()
                while self.call_times and now - self.call_times[0] > self.period:
                    self.call_times.popleft()

            self.call_times.append(time.monotonic())


_rate_limiter = GroqRateLimiter()


def _build_messages(question: str, context: str, history: Optional[List[Dict]] = None) -> list:
    """Same structure as before — [system] + prior turns + current turn with
    retrieved Context. Swapping the LLM provider doesn't change this logic
    at all, only how the messages get sent below."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"})
    return messages


def generate(question: str, context: str, history: Optional[List[Dict]] = None) -> str:
    """Non-streaming generation returning complete text string."""
    messages = _build_messages(question, context, history)

    _rate_limiter.wait_for_slot()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=350,
    )

    return response.choices[0].message.content


def generate_stream(question: str, context: str, history: Optional[List[Dict]] = None) -> Generator[str, None, None]:
    """Streaming generator yielding tokens in real-time."""
    messages = _build_messages(question, context, history)

    _rate_limiter.wait_for_slot()
    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=350,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta