# Lumeluxe RAG Chatbot

[![CI Status](https://github.com/Sabtain-Dev/RAG-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Sabtain-Dev/RAG-Chatbot/actions)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector%20store-6E56CF?style=flat)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq-F55036?style=flat)](https://groq.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-oriented Retrieval-Augmented Generation (RAG) chatbot for **Lumeluxe**, an e-commerce skincare and haircare brand. Answers customer questions about products, pricing, availability, and store policies using the store's real, live catalog, grounded strictly in retrieved context, with an explicit fallback (plus contact details) when information isn't available, instead of guessing.

**Live demo:** [Lumeluxe Chatbot](https://lumeluxe-chatbot.vercel.app/)

## 🎥 Video Demonstration

[![Watch the Lumeluxe RAG Chatbot demonstration](https://img.youtube.com/vi/tzwhiS8wivc/hqdefault.jpg)](https://youtu.be/tzwhiS8wivc)

Select the preview to watch the video.

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Building the Knowledge Base](#-building-the-knowledge-base)
- [Running Locally](#-running-locally)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Continuous Integration](#-continuous-integration)
- [Security](#-security)
- [Deployment](#-deployment)
- [Known Limitations](#-known-limitations)
- [Roadmap](#-roadmap)
- [Contact](#-contact)

---

## 🎯 Overview

Most storefront chatbots either hallucinate product details or require constant manual content updates. This project solves both problems:

- **Product data is pulled directly from the store's live MongoDB database**, not scraped or hand-maintained, pricing, stock, and catalog changes are accurate at every re-index.
- **Answers are strictly grounded in retrieved context.** If the knowledge base doesn't contain the answer, the bot says so and provides real contact details instead of fabricating a response.
- **Conversation memory** enables natural follow-ups (e.g. *"what's its price?"* correctly resolves to the previously discussed product).
- **Rate-limited on both ends** per-IP request throttling on the API, and an internal queue that keeps outbound LLM calls within the provider's rate limit, so the system degrades gracefully under load instead of failing.

## 🏗️ Architecture

```text
┌──────────────────┐        HTTPS           ┌───────────────────┐
│   Chat Widget    │ ─────────────────────> │   FastAPI Backend │
│   (Vercel)       │ <───────────────────── │   (SnapDeploy)    │
└──────────────────┘                        └─────┬─────────┬───┘
                                                  │         │
                                        ┌─────────▼──┐  ┌───▼──────┐
                                        │  ChromaDB  │  │ Groq API │
                                        │(Vector DB) │  │   (LLM)  │
                                        └────────────┘  └──────────┘
                                                  ▲
                                                  │ Ingestion
                                        ┌─────────┴────────────┐
                                        │   MongoDB Atlas      │
                                        │ (live product data)  │
                                        └──────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Vector database | ChromaDB |
| Embeddings | `BAAI/bge-small-en-v1.5` via `fastembed` (ONNX runtime — low memory footprint) |
| LLM | Groq API (`openai/gpt-oss-20b`) |
| Product data source | MongoDB Atlas (live catalog) |
| Static content source | Direct extraction from frontend source (About Us, Privacy Policy) |
| Rate limiting | `slowapi` (incoming, per-IP) + custom token-bucket throttle (outgoing LLM calls) |
| Backend hosting | SnapDeploy (Docker) |
| Frontend hosting | Vercel |
| CI | GitHub Actions |

## 📁 Project Structure

```text
app/
├── api/          # FastAPI routes
├── chatbot/      # RAG service, retriever, generator, prompts, conversation memory
├── core/         # configuration, rate limiting
├── models/       # request/response schemas
├── rag/          # chunking, embeddings, vector DB client
└── main.py       # application entry point

data/
└── cleaned/      # processed knowledge base (products, about, privacy)

scripts/          # MongoDB ingestion, chunking/indexing, CLI chat client
tests/            # pytest suite (API + retrieval)
frontend/         # standalone chat widget (HTML/CSS/JS)
Dockerfile        # backend container definition
```

## ⚙️ Installation

### Prerequisites
- Python 3.10
- A MongoDB Atlas connection string
- A [Groq](https://console.groq.com) API key

### Setup
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```env
MONGO_URI=your_mongodb_connection_string
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

## 🗃️ Building the Knowledge Base

```bash
python scripts/ingest_from_db.py      # pull the live product catalog from MongoDB
python scripts/index_documents.py     # chunk, embed, and index into ChromaDB
```
Re-run whenever the product catalog changes.

## 🚀 Running Locally

**API server:**
```bash
uvicorn app.main:app --reload
```

**CLI client:**
```bash
python scripts/chat.py
```

**Docker:**
```bash
docker build -t lumeluxe-chatbot .
docker run -p 8000:8000 --env-file .env lumeluxe-chatbot
```
- Pre-built image available on Docker Hub: [`Chatbot Docker Image`](https://hub.docker.com/r/msabtainkhan/lumeluxe-chatbot)

## 🔌 API Reference

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/chat` | `POST` | Send a message, receive a grounded answer and session ID |
| `/chat/reset` | `POST` | Clear conversation memory for a session |
| `/health` | `GET` | Liveness check |

**`POST /chat`**
```json
{
  "message": "What is the price of Vitamin C Herbal Soap?",
  "session_id": "optional-existing-session-id"
}
```

## 🧪 Testing

```bash
pytest -v
```
Covers API contract validation (mocked, no external dependencies) and retrieval accuracy against a curated question set.

## ⚙️ Continuous Integration

GitHub Actions runs the full test suite on every push and pull request to `main`, gated behind branch protection requiring passing checks and review approval before merge.

## 🛡️ Security

- Secrets (`MONGO_URI`, `GROQ_API_KEY`) are injected as environment variables at runtime, never committed or baked into the Docker image.
- Only the `sellerproducts` collection is read from MongoDB; customer PII (orders, users, transactions) is never accessed by the ingestion pipeline.
- Per-IP rate limiting on all chat endpoints; message length capped to prevent abuse.
- CORS restricted to explicitly whitelisted origins.

## 📦 Deployment

- **Backend** is containerized (`Dockerfile` at the repo root) and deployed on [SnapDeploy](https://snapdeploy.dev), built directly from this repository's `main` branch.
- **Frontend** (`frontend/`) is deployed as a static site on Vercel, pointed at the backend's public API URL.

## ⚠️ Known Limitations

- The backend's free-tier hosting may go idle after periods of inactivity; the first request after idle time can take longer while the container restarts. This is a hosting-tier characteristic, not an application bug.

## 🗺️ Roadmap

- [x] Live MongoDB-backed product ingestion
- [x] Session-based conversation memory
- [x] Rate limiting (incoming + outgoing)
- [x] Standalone demo deployment
- [ ] Persistent always-on hosting
- [ ] Full website widget integration (`lumeluxe.pk`)
- [ ] Query rewriting for improved follow-up retrieval

## 👤 Contact

**M. Sabtain Khan**

- **GitHub:** [@Sabtain-Dev](https://github.com/Sabtain-Dev)
- **LinkedIn:** [msabtainkhan](https://linkedin.com/in/msabtainkhan)