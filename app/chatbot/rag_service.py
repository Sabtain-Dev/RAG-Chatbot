import re
import uuid
from app.chatbot.generator import generate
from app.chatbot.retriever import retrieve
from app.chatbot.memory import memory
from app.core.config import CONTACT_INFO
from app.models.chat import ChatRequest, ChatResponse

GREETINGS = {
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "hi there", "hey there",
}
THANKS = {
    "thank you", "thanks", "thank you for the help", "thanks for the help",
    "thanks a lot", "thank you so much",
}
BYE = {
    "bye", "goodbye", "see you", "bye bye", "have a good day", "good night",
}

PREAMBLE_REGEX = re.compile(
    r"^(hi|hello|hey|good morning|good afternoon|good evening|please|could you|can you|tell me|i want to know|i was wondering|do you know)\b[!\.,\s]*",
    re.IGNORECASE,
)


class RAGService:

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def _check_conversational_intent(self, message: str) -> str | None:
        cleaned = message.strip().lower().rstrip("!.,?")
        if cleaned in GREETINGS:
            return "Hello! Welcome to Lumeluxe. How can I assist you with our skincare and beauty products today?"
        if cleaned in THANKS:
            return "You're very welcome! Let me know if you need help with anything else."
        if cleaned in BYE:
            return "Goodbye! Have a wonderful day and thank you for visiting Lumeluxe!"
        return None

    def _clean_search_query(self, message: str) -> str:
        cleaned = message.strip()
        while True:
            new_cleaned = PREAMBLE_REGEX.sub("", cleaned).strip()
            if new_cleaned == cleaned or not new_cleaned:
                break
            cleaned = new_cleaned
        return cleaned if len(cleaned) > 2 else message

    def ask(self, request: ChatRequest) -> ChatResponse:
        """Processes query through Intent Check -> History -> Retrieval -> Generation."""
        session_id = request.session_id or str(uuid.uuid4())
        history = memory.get_history(session_id)

        # 1. Fast-path conversational phrase check — still logged to memory
        #    so a later "as I said, ..." follow-up has continuity.
        conversational_reply = self._check_conversational_intent(request.message)
        if conversational_reply:
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", conversational_reply)
            return ChatResponse(answer=conversational_reply, sources_found=True, session_id=session_id)

        # 2. Clean leading filler so ChromaDB distance calculation stays accurate.
        #    NOTE: only the search query is cleaned — the ORIGINAL message is
        #    what gets stored in history and sent to the generator, so the
        #    LLM still sees the user's natural phrasing for pronoun resolution.
        search_query = self._clean_search_query(request.message)

        # 3. Retrieve relevant chunks from ChromaDB
        documents = retrieve(search_query, top_k=self.top_k)

        if not documents:
            fallback_answer = (
                "I couldn't find this information on the Lumeluxe website.\n\n"
                f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
            )
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", fallback_answer)
            return ChatResponse(answer=fallback_answer, sources_found=False, session_id=session_id)

        # 4. Format context into structured chunks
        context_blocks = [f"[Chunk {i+1}]\n{doc}" for i, doc in enumerate(documents)]
        context = "\n\n".join(context_blocks)

        # 5. Pass retrieved context + conversation history + original query to Ollama
        try:
            answer = generate(question=request.message, context=context, history=history)
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", answer)
            return ChatResponse(answer=answer, sources_found=True, session_id=session_id)
        except Exception:
            error_answer = "The AI inference service is currently unavailable. Please ensure Ollama is running locally."
            return ChatResponse(answer=error_answer, sources_found=True, session_id=session_id)

    def reset_session(self, session_id: str) -> None:
        memory.clear(session_id)


# Global service instance
rag_service = RAGService()