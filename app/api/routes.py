from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.models.chat import ChatRequest, ChatResponse
from app.chatbot.rag_service import rag_service
from app.core.rate_limit import limiter

router = APIRouter()


class SessionRequest(BaseModel):
    session_id: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("15/minute")
def chat_endpoint(request: Request, body: ChatRequest):
    """Primary chat endpoint for the web widget. Capped at 15 req/min per IP —
    generous for a real user, tight enough to stop one visitor from
    consuming the whole shared Groq quota (30 req/min total)."""
    return rag_service.ask(body)


@router.post("/chat/reset")
@limiter.limit("10/minute")
def reset_chat(request: Request, body: SessionRequest):
    """Clears conversation memory for a session — e.g. a 'New chat' button."""
    rag_service.reset_session(body.session_id)
    return {"status": "cleared", "session_id": body.session_id}