# RAG Chatbot: Deployment Guide

## Deployment Model

```text
Vercel Frontend
      |
     HTTPS
      v
SnapDeploy Backend
      |
      +--> ChromaDB
      +--> Groq API
      +--> MongoDB Atlas
```

## Environment Variables

```env
MONGO_URI=your_mongodb_connection_string
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit `.env` or real credentials.

## Local Docker Test

```bash
docker build -t lumeluxe-chatbot .
docker run -p 8000:8000 --env-file .env lumeluxe-chatbot
```

## Health Check

```text
GET /health
```

Expected:

```json
{"status":"ok"}
```

## Chat Check

```text
POST /chat
```

Example:

```json
{
  "message": "What is the price of Vitamin C Herbal Soap?",
  "session_id": "demo-session"
}
```

## Frontend
Deploy `frontend/` as a static site and configure it to call the public backend URL, not localhost.

## CORS
Allow only required production origins. Localhost can be allowed for development. Avoid unrestricted wildcard CORS in production.

## Client Demo Workflow

```text
Deploy
  -> Developer verification
  -> Public demo URL
  -> Client desktop/mobile testing
  -> Feedback
  -> Fixes
  -> Redeploy
  -> Client approval
```

## Website Integration
Only after approval:
1. Obtain website/developer access.
2. Identify the website platform.
3. Add the chatbot widget.
4. Configure the production API URL.
5. Update CORS.
6. Test all relevant pages.
7. Test mobile and desktop.
8. Run production smoke tests.

## Free-Tier Note
The free backend host may sleep after inactivity, so the first request after idle time can be slower.
