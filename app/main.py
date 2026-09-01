from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.api.routes import router
from app.core.rate_limit import limiter

app = FastAPI(
    title="Lumeluxe RAG Chatbot API",
    description="Backend API serving Lumeluxe E-Commerce Knowledge Base.",
    version="1.0.0"
)

# Attaches the rate limiter to the app and returns a proper 429 response
# with a clear message instead of an unhandled exception when someone
# exceeds their per-IP limit.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://lumeluxe-chatbot-6fe84.containers.snapdeploy.app",
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