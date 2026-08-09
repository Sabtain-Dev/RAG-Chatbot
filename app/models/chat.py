from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User query sent from frontend widget")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer or fallback response")
    sources_found: bool = Field(..., description="Flag indicating if relevant context was matched")