from typing import Generator, List, Optional, Dict
from groq import Groq
from app.chatbot.prompts import SYSTEM_PROMPT
from app.core.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


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