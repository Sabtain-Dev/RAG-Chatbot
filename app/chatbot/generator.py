from typing import Generator, List, Optional, Dict
import ollama
from app.chatbot.prompts import SYSTEM_PROMPT

MODEL_NAME = "qwen2.5:3b"


def _build_messages(question: str, context: str, history: Optional[List[Dict]] = None) -> list:
    """
    Builds a proper multi-turn message list instead of flattening history
    into one string: [system] + [prior user/assistant turns] + [current
    turn]. This lets the model resolve references like "it" or "that
    product" from real conversational structure rather than a text blob.
    Note: only the CURRENT turn carries retrieved Context — prior turns in
    history are the raw Q&A text only, so old context never leaks into or
    gets re-used for the new answer (memory != knowledge base).
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"})
    return messages


def generate(question: str, context: str, history: Optional[List[Dict]] = None) -> str:
    """Non-streaming generation returning complete text string."""
    messages = _build_messages(question, context, history)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={
            "temperature": 0.0,
            "num_ctx": 3072,       # bumped from 2048 — history turns now add tokens
            "num_predict": 350,
        }
    )

    return response["message"]["content"]


def generate_stream(question: str, context: str, history: Optional[List[Dict]] = None) -> Generator[str, None, None]:
    """Streaming generator yielding tokens in real-time. history=None keeps
    scripts/chat.py's existing calls working unchanged."""
    messages = _build_messages(question, context, history)

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={
            "temperature": 0.0,
            "num_ctx": 3072,
            "num_predict": 350,
        },
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]