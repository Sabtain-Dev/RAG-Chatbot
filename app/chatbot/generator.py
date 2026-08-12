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
            "temperature": 0.0,   # Set to 0.0 to prevent price hallucination
            "num_ctx": 2048,      # Expanded context window to handle multi-chunk responses
            "num_predict": 350,   # Increased output token length
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
            "temperature": 0.0,
            "num_ctx": 2048,
            "num_predict": 350,
        },
        stream=True
    )

    for chunk in stream:
        yield chunk["message"]["content"]