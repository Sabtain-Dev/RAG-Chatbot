from fastapi import FastAPI

app = FastAPI(
    title="LumeLuxe RAG Chatbot API",
    description="Custom e-commerce RAG backend using FastAPI, ChromaDB, and Ollama",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "LumeLuxe RAG Chatbot Backend",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"health": "ok"}