# RAG Chatbot: Architecture

## Overview
Production-oriented RAG chatbot for Lumeluxe e-commerce customer support.

## Architecture

```text
User
  |
  v
Chat Widget (Vercel)
  |
 HTTPS
  v
FastAPI Backend (Docker / SnapDeploy)
  |
  +------------------+
  |                  |
  v                  v
ChromaDB           Groq API
Vector Store         LLM
  ^
  |
MongoDB Atlas
Live Product Catalog
```

## Components
- Frontend: responsive HTML/CSS/JavaScript chat widget.
- Backend: FastAPI with `/chat`, `/chat/reset`, and `/health`.
- Retrieval: `BAAI/bge-small-en-v1.5` through FastEmbed/ONNX and ChromaDB.
- LLM: Groq API using `openai/gpt-oss-20b`.
- Product source: MongoDB Atlas live catalog.
- Static source: processed About Us and Privacy Policy content.
- Memory: session-based conversation context.
- Protection: CORS, message limits, per-IP rate limiting, outbound LLM throttling.

## RAG Flow

```text
User Question
     |
     v
FastAPI /chat
     |
     v
Retrieve Relevant Documents
     |
     v
Grounded Prompt
     |
     v
Groq LLM
     |
     v
Grounded Answer / Fallback
```

## Grounding Rule
The chatbot must not fabricate unavailable information. If the knowledge base cannot support an answer, it should explicitly state that the information cannot be verified and provide the approved Lumeluxe contact route where appropriate.

## Security
- Secrets supplied through environment variables.
- No credentials committed to Git.
- Only required MongoDB product data is ingested.
- Customer PII is not ingested.
- CORS is restricted to approved origins.
- Chat endpoints are rate limited.

## Deployment
Backend is containerized and deployed on SnapDeploy; the static frontend is deployed on Vercel.

## Future Improvements
- Query rewriting.
- Automated knowledge-base refresh.
- Persistent always-on hosting.
- Improved retrieval evaluation.
- Website widget integration.
- Observability and analytics.
