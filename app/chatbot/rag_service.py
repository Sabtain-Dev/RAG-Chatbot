import re
from app.chatbot.generator import generate
from app.chatbot.retriever import retrieve
from app.core.config import CONTACT_INFO
from app.models.chat import ChatRequest, ChatResponse

# Fast lookup sets for conversational etiquette
GREETINGS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good evening",
    "good afternoon",
    "hi there",
    "hey there",
}
THANKS = {
    "thank you",
    "thanks",
    "thank you for the help",
    "thanks for the help",
    "thanks a lot",
    "thank you so much",
}
BYE = {
    "bye",
    "goodbye",
    "see you",
    "bye bye",
    "have a good day",
    "good night",
}

# Regex to detect and strip leading greetings and conversational filler words
PREAMBLE_REGEX = re.compile(
    r"^(hi|hello|hey|good morning|good afternoon|good evening|please|could you|can you|tell me|i want to know|i was wondering|do you know)\b[!\.,\s]*",
    re.IGNORECASE,
)


class RAGService:

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def _check_conversational_intent(self, message: str) -> str | None:
        """Fast-path check for simple etiquette to respond immediately without vector search."""
        cleaned = message.strip().lower().rstrip("!.,?")
        if cleaned in GREETINGS:
            return "Hello! Welcome to Lumeluxe. How can I assist you with our skincare and beauty products today?"
        if cleaned in THANKS:
            return "You're very welcome! Let me know if you need help with anything else."
        if cleaned in BYE:
            return "Goodbye! Have a wonderful day and thank you for visiting Lumeluxe!"
        return None

    def _clean_search_query(self, message: str) -> str:
        """Iteratively strips leading greetings and preamble fillers to isolate key product terms for ChromaDB vector search."""
        cleaned = message.strip()
        while True:
            new_cleaned = PREAMBLE_REGEX.sub("", cleaned).strip()
            if new_cleaned == cleaned or not new_cleaned:
                break
            cleaned = new_cleaned

        return cleaned if len(cleaned) > 2 else message

    def ask(self, request: ChatRequest) -> ChatResponse:
        """Processes query through Intent Check -> Query Cleaner -> ChromaDB Retrieval -> LLM Generation."""
        # 1. Fast-path conversational phrase check
        conversational_reply = self._check_conversational_intent(request.message)
        if conversational_reply:
            return ChatResponse(answer=conversational_reply, sources_found=True)

        # 2. Clean leading filler so ChromaDB distance calculation stays accurate
        search_query = self._clean_search_query(request.message)

        # 3. Retrieve relevant chunks from ChromaDB
        documents = retrieve(search_query, top_k=self.top_k)

        if not documents:
            fallback_answer = (
                "I couldn't find this information on the Lumeluxe website.\n\n"
                f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
            )
            return ChatResponse(answer=fallback_answer, sources_found=False)

        # 4. Format context into structured chunks
        context_blocks = [
            f"[Chunk {i+1}]\n{doc}" for i, doc in enumerate(documents)
        ]
        context = "\n\n".join(context_blocks)

        # 5. Pass retrieved context + original user query to Ollama
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