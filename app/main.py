from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Lumeluxe RAG Chatbot API",
    description="Production-ready backend service combining ChromaDB semantic search and Ollama generation.",
    version="1.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Lumeluxe Chatbot Backend Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}