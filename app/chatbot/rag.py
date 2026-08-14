from typing import Generator, Union
from pydantic import BaseModel, Field
from app.chatbot.retriever import retrieve
from app.chatbot.generator import generate, generate_stream
from app.core.config import CONTACT_INFO

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")

class ChatResponse(BaseModel):
    answer: str
    sources_found: bool

class RAGService:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def ask(self, request: ChatRequest) -> ChatResponse:
        docs = retrieve(request.question, top_k=self.top_k)

        if not docs:
            fallback_msg = (
                "I couldn't find this information on the Lumeluxe website.\n\n"
                f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
            )
            return ChatResponse(answer=fallback_msg, sources_found=False)

        context_blocks = [f"[Chunk {i+1}]\n{item['document']}" for i, item in enumerate(docs)]
        context = "\n\n".join(context_blocks)

        answer = generate(request.question, context)
        return ChatResponse(answer=answer, sources_found=True)

    def ask_stream(self, question: str) -> Union[Generator[str, None, None], tuple[str, bool]]:
        docs = retrieve(question, top_k=self.top_k)

        if not docs:
            fallback_msg = (
                "I couldn't find this information on the Lumeluxe website.\n\n"
                f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
            )
            return fallback_msg, False

        context_blocks = [f"[Chunk {i+1}]\n{item['document']}" for i, item in enumerate(docs)]
        context = "\n\n".join(context_blocks)

        return generate_stream(question, context), True

rag_service = RAGService()