from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.chatbot.rag_service import rag_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Primary chat endpoint for the web widget."""
    return rag_service.ask(request)