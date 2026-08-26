from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Lumeluxe RAG Chatbot API",
    description="Backend API serving Lumeluxe E-Commerce Knowledge Base.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        # TODO Phase C: add your standalone demo's deployed URL once you have it
        # TODO Phase D: add "https://lumeluxe.pk" once client approves integration
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Lumeluxe Chatbot Backend Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}