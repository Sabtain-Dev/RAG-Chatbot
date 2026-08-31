# Lumeluxe RAG Chatbot

A retrieval-augmented generation (RAG) chatbot for the Lumeluxe e-commerce store. Answers customer questions about products, pricing, availability, and store policies using real data, no hallucinated answers, with a clear fallback when information isn't available.

## Stack

- **Backend:** FastAPI
- **Vector DB:** ChromaDB
- **Embeddings:** `BAAI/bge-small-en-v1.5` via `fastembed` (ONNX runtime)
- **LLM:** Groq API (`openai/gpt-oss-20b`)
- **Data source:** MongoDB Atlas (live product catalog) + frontend source (About/Privacy content)
- **Rate limiting:** `slowapi` (incoming) + custom throttle (outgoing Groq calls)

## Project Structure

```
app/
├── api/          → FastAPI routes
├── chatbot/      → RAG service, retriever, generator, prompts, memory
├── core/         → config, rate limiting
├── models/       → request/response schemas
├── rag/          → chunking, embeddings, vector DB
└── main.py       → app entry point

data/
└── cleaned/      → processed knowledge base (products, about, privacy)

scripts/          → data pipeline (scrape, clean, ingest, index) + CLI chat
tests/            → pytest suite (API + retrieval)
frontend/         → standalone demo widget
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Create `.env` in the project root:
```
MONGO_URI=your_mongodb_connection_string
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

## Data Pipeline

```bash
python scripts/ingest_from_db.py      # pull live product catalog from MongoDB
python scripts/index_documents.py     # chunk, embed, and index into ChromaDB
```

## Running

**API:**
```bash
uvicorn app.main:app --reload
```

**CLI:**
```bash
python scripts/chat.py
```

## API

```
POST /chat
{
  "message": "What is the price of Vitamin C Herbal Soap?",
  "session_id": "optional-existing-session-id"
}
```

```
POST /chat/reset
{ "session_id": "..." }
```

```
GET /health
```

## Testing

```bash
pytest -v
```

## Docker

```bash
docker build -t lumeluxe-chatbot .
docker run -p 8000:8000 --env-file .env lumeluxe-chatbot
```