from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=1000,
        description="User query sent from frontend widget"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Client-generated session identifier for conversation continuity. "
                     "If omitted, the server generates one and returns it.",
    )


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer or fallback response")
    sources_found: bool = Field(..., description="Flag indicating if relevant context was matched")
    session_id: str = Field(..., description="Session identifier — echo this back on the next request")