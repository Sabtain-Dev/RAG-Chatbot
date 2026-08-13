from fastapi import APIRouter
from pydantic import BaseModel
from app.models.chat import ChatRequest, ChatResponse
from app.chatbot.rag_service import rag_service

router = APIRouter()


class SessionRequest(BaseModel):
    session_id: str


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Primary chat endpoint for the web widget."""
    return rag_service.ask(request)


@router.post("/chat/reset")
def reset_chat(request: SessionRequest):
    """Clears conversation memory for a session — e.g. a 'New chat' button."""
    rag_service.reset_session(request.session_id)
    return {"status": "cleared", "session_id": request.session_id}