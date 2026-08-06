from typing import Generator
import ollama
from app.chatbot.prompts import SYSTEM_PROMPT

MODEL_NAME = "qwen2.5:3b"

def generate(question: str, context: str) -> str:
    """Non-streaming generation returning complete text string."""
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        options={
            "temperature": 0.2,
            "num_ctx": 1024,      # Reduced context window to lower CPU latency
            "num_predict": 250,   # Capped generation token length for faster output
        }
    )

    return response["message"]["content"]

def generate_stream(question: str, context: str) -> Generator[str, None, None]:
    """Streaming generator yielding tokens in real-time."""
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        options={
            "temperature": 0.2,
            "num_ctx": 1024,
            "num_predict": 250,
        },
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]