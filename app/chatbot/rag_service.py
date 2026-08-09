import httpx
from app.chatbot.generator import generate
from app.chatbot.retriever import retrieve
from app.core.config import CONTACT_INFO
from app.models.chat import ChatRequest, ChatResponse


class RAGService:

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def ask(self, request: ChatRequest) -> ChatResponse:
        """Processes query through Retriever -> Context Formatter -> LLM Generator."""
        documents = retrieve(request.message, top_k=self.top_k)

        if not documents:
            fallback_answer = (
                "I couldn't find this information on the Lumeluxe website.\n\n"
                f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
            )
            return ChatResponse(answer=fallback_answer, sources_found=False)

        # Format context into distinct blocks
        context_blocks = [
            f"[Chunk {i+1}]\n{doc}" for i, doc in enumerate(documents)
        ]
        context = "\n\n".join(context_blocks)

        try:
            answer = generate(question=request.message, context=context)
            return ChatResponse(answer=answer, sources_found=True)
        except Exception as e:
            return ChatResponse(
                answer="The AI inference service is currently unavailable. Please ensure Ollama is running locally.",
                sources_found=True,
            )


# Global service instance
rag_service = RAGService()