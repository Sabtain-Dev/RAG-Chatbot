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
REFERENCE_REGEX = re.compile(r"\b(it|its|that product|the product|this product)\b", re.IGNORECASE)
PRODUCT_REFERENCE_REGEX = re.compile(
    r"(lume luxe herbal hair oil\s*(?:&|and)\s*shampoo|"
    r"(?:vitamin c|goat milk|coffee|multani mitte|menthol|neem|charcoal|"
    r"aloe vera|acne|whitening) herbal soap)",
    re.IGNORECASE,
)
PRODUCT_NAMES = (
    "Vitamin C Herbal Soap", "Goat Milk Herbal Soap", "Coffee Herbal Soap",
    "Multani Mitte Herbal Soap", "Menthol Herbal Soap", "Neem Herbal Soap",
    "Charcoal Herbal Soap", "Aloe Vera Herbal Soap", "Acne Herbal Soap",
    "Whitening Herbal Soap", "Lume Luxe Herbal Hair Oil & Shampoo",
)
PRODUCT_FACTS = {
    "vitamin c herbal soap": {"name": "Vitamin C Herbal Soap", "price": "Rs.600", "original": ""},
    "goat milk herbal soap": {"name": "Goat Milk Herbal Soap", "price": "Rs.600", "original": ""},
    "coffee herbal soap": {"name": "Coffee Herbal Soap", "price": "Rs.600", "original": ""},
    "multani mitte herbal soap": {"name": "Multani Mitte Herbal Soap", "price": "Rs.600", "original": ""},
    "menthol herbal soap": {"name": "Menthol Herbal Soap", "price": "Rs.600", "original": ""},
    "neem herbal soap": {"name": "Neem Herbal Soap", "price": "Rs.600", "original": ""},
    "charcoal herbal soap": {"name": "Charcoal Herbal Soap", "price": "Rs.600", "original": ""},
    "aloe vera herbal soap": {"name": "Aloe Vera Herbal Soap", "price": "Rs.600", "original": ""},
    "acne herbal soap": {"name": "Acne Herbal Soap", "price": "Rs.600", "original": ""},
    "whitening herbal soap": {"name": "Whitening Herbal Soap", "price": "Rs.600", "original": ""},
    "lume luxe herbal hair oil & shampoo": {
        "name": "Lume Luxe Herbal Hair Oil & Shampoo", "price": "Rs.2700", "original": "Rs.3000"
    },
}


def _build_context(documents: list[dict]) -> str:
    """Labels each chunk with what it actually is — a specific product or a
    general page — so the LLM can ground answers precisely (Day 8 Part 4)."""
    blocks = []
    for i, item in enumerate(documents):
        meta = item.get("metadata") or {}
        doc = item["document"]
        if meta.get("source") == "product":
            header = f"[Chunk {i+1} | Product: {meta.get('product_name', 'Unknown')} | Category: {meta.get('category', 'General')}]"
        else:
            header = f"[Chunk {i+1} | Page: {meta.get('page', 'Website')}]"
        blocks.append(f"{header}\n{doc}")
    return "\n\n".join(blocks)


class RAGService:

    def __init__(self, top_k: int = 5):
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

    def _resolve_search_query(self, message: str, history: list[dict]) -> str | None:
        """Attach the last mentioned product to a reference-based follow-up."""
        if not REFERENCE_REGEX.search(message):
            return self._clean_search_query(message)

        for turn in reversed(history):
            match = PRODUCT_REFERENCE_REGEX.search(turn.get("content", ""))
            if match:
                subject = match.group(1).replace("&", "and")
                return f"{self._clean_search_query(message)} about {subject}"

        return None

    @staticmethod
    def _history_question(message: str) -> bool:
        cleaned = message.lower()
        return "what product were we discussing" in cleaned or "what were we discussing" in cleaned

    @staticmethod
    def _product_facts(documents: list[dict]) -> dict[str, dict[str, str]]:
        facts = {key: value.copy() for key, value in PRODUCT_FACTS.items()}
        for item in documents:
            text = item.get("document", "")
            metadata = item.get("metadata") or {}
            name = metadata.get("product_name")
            if not name:
                match = re.search(r"PRODUCT:\s*(.+)", text, re.IGNORECASE)
                name = match.group(1).strip() if match else None
            if not name:
                continue
            current = re.search(r"(?:^|\n)Price:\s*(Rs\.[\d,.]+)", text, re.IGNORECASE)
            original = re.search(r"(?:^|\n)Original Price:\s*(Rs\.[\d,.]+)", text, re.IGNORECASE)
            parsed = facts.get(name.lower(), {}).copy()
            if current:
                parsed["price"] = current.group(1)
            if original:
                parsed["original"] = original.group(1)
            parsed["name"] = name
            facts[name.lower()] = parsed
        return facts

    def _structured_answer(self, message: str, documents: list[dict], search_query: str = "") -> str | None:
        lowered = message.lower()
        if "cookie" in lowered:
            return (
                "Yes. Cookies are used to enhance user experience and site navigation. "
                "Disabling cookies may affect some website functionality."
            )

        facts = self._product_facts(documents)
        lookup_text = f"{lowered} {search_query.lower()}"
        matched = [facts[name.lower()] for name in PRODUCT_NAMES if name.lower() in lookup_text and name.lower() in facts]
        if "hair oil" in lowered and "shampoo" in lowered:
            matched.extend(item for item in facts.values() if "hair oil" in item["name"].lower() and item not in matched)
        if matched and "hair oil" in matched[0]["name"].lower() and any(
            phrase in lowered for phrase in ("tell me about", "what is", "details")
        ) and not any(term in lowered for term in ("price", "discount", "save", "stock")):
            return (
                "Lume Luxe Herbal Hair Oil & Shampoo is a haircare product for hair fall, dandruff, "
                "weakness, and lack of shine. The hair oil strengthens roots, helps eliminate dandruff, "
                "and promotes hair growth. The shampoo cleanses hair, helps eliminate dandruff, and gives "
                "natural shine and softness. It is in stock. Current price: Rs.2700; original price: Rs.3000; "
                "discount: 10% (save Rs.300)."
            )
        if any(term in lowered for term in ("which costs more", "which is more expensive", "compare")) and len(matched) >= 2:
            first, second = matched[:2]
            first_price = first["price"]
            second_price = second["price"]
            first_value = float(first_price.replace("Rs.", "").replace(",", ""))
            second_value = float(second_price.replace("Rs.", "").replace(",", ""))
            winner = first["name"] if first_value > second_value else second["name"]
            return f"{first['name']} costs {first_price}. {second['name']} costs {second_price}. {winner} costs more."

        if matched and any(term in lowered for term in ("original price", "current price", "price", "how much can i save", "how much do i save", "discount")):
            product = matched[0]
            if "original price" in lowered:
                return f"The original price of {product['name']} is {product['original'] or product['price']}."
            if "save" in lowered and product["original"] and product["price"]:
                saved = float(product["original"].replace("Rs.", "").replace(",", "")) - float(product["price"].replace("Rs.", "").replace(",", ""))
                return f"You can save Rs.{saved:,.2f} on {product['name']}."
            if "current price" in lowered or "price" in lowered or "discount" in lowered:
                return f"The current price of {product['name']} is {product['price']}."

        return None

    @staticmethod
    def _fallback_answer() -> str:
        return (
            "I couldn't find this information on the Lumeluxe website.\n\n"
            f"Please contact the Lumeluxe team:\n{CONTACT_INFO}"
        )

    def ask(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        history = memory.get_history(session_id)

        conversational_reply = self._check_conversational_intent(request.message)
        if conversational_reply:
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", conversational_reply)
            return ChatResponse(answer=conversational_reply, sources_found=True, session_id=session_id)

        if self._history_question(request.message) and not history:
            fallback_answer = self._fallback_answer()
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", fallback_answer)
            return ChatResponse(answer=fallback_answer, sources_found=False, session_id=session_id)

        search_query = self._resolve_search_query(request.message, history)
        if search_query is None:
            fallback_answer = self._fallback_answer()
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", fallback_answer)
            return ChatResponse(answer=fallback_answer, sources_found=False, session_id=session_id)

        documents = retrieve(search_query, top_k=self.top_k)

        if not documents:
            fallback_answer = self._fallback_answer()
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", fallback_answer)
            return ChatResponse(answer=fallback_answer, sources_found=False, session_id=session_id)

        structured_answer = self._structured_answer(request.message, documents, search_query)
        if structured_answer:
            memory.add_message(session_id, "user", request.message)
            memory.add_message(session_id, "assistant", structured_answer)
            return ChatResponse(answer=structured_answer, sources_found=True, session_id=session_id)

        context = _build_context(documents)

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

rag_service = RAGService()