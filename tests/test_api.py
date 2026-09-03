# tests/test_api.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200


# Mocks both retrieval and generation so this test is deterministic and
# safe in CI — it validates the API contract (schema, status codes,
# session_id round-trip), not RAG quality. Retrieval/generation quality
# is covered separately by test_retrieval.py (local) and manual testing.
@patch("app.chatbot.rag_service.generate")
@patch("app.chatbot.rag_service.retrieve")
def test_chat_returns_valid_schema(mock_retrieve, mock_generate):
    mock_retrieve.return_value = [
        {
            "document": "PRODUCT: Vitamin C Herbal Soap\nPrice: Rs.600.00",
            "distance": 0.2,
            "metadata": {"source": "product", "product_name": "Vitamin C Herbal Soap", "category": "Herbal Soap"},
        }
    ]
    mock_generate.return_value = "Vitamin C Herbal Soap is Rs.600.00 and currently in stock."

    response = client.post(
        "/chat",
        json={"session_id": "test-session", "message": "What is the price of Vitamin C Herbal Soap?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["session_id"] == "test-session"
    assert data["sources_found"] is True


def test_chat_fallback_when_no_results():
    with patch("app.chatbot.rag_service.retrieve", return_value=[]):
        response = client.post(
            "/chat",
            json={"session_id": "test-session-2", "message": "Do you ship internationally?"},
        )
        data = response.json()
        assert data["sources_found"] is False
        assert "couldn't find" in data["answer"].lower()


def test_cors_allows_vercel_preview_origin():
    response = client.options(
        "/chat",
        headers={
            "Origin": "https://lumeluxe-chatbot-git-main-abc123.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://lumeluxe-chatbot-git-main-abc123.vercel.app"


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"session_id": "x", "message": ""})
    assert response.status_code == 422  # Pydantic min_length=1 validation