# Setup Guide

## 1. Backend (FastAPI + LangGraph)

### Install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .
```

Copy `.env.example` to `.env` and update credentials:

- `OPENAI_API_KEY` and `OPENAI_MODEL`
- `VECTOR_STORE_*` for Qdrant (or swap to another vector DB)
- `DISCORD_WEBHOOK_URL` for notifications
- `CALENDLY_*` and `FALLBACK_MEETING_LINK`
- `CORS_ORIGINS` to include your WordPress domain

### Run locally

```bash
uvicorn app.main:app --reload
```

### Document ingestion (placeholder)

1. Place company knowledge base files under `backend/data/source_docs/`.
2. Implement an ingestion script that loads documents via `app.retrieval.document_loader`.
3. Call `VectorStoreProvider().ingest_documents(docs)` to populate the vector store.
4. Schedule periodic re-ingestion as needed.

## 2. Widget (TypeScript)

### Install & build

```bash
cd widget
npm install
npm run build
```

The build command emits `dist/index.js` exposing `window.BusinessChatWidget.init`.

### Embed in WordPress

1. Upload `dist/index.js` to your theme assets or CDN.
2. Append the following snippet to your footer (replace `baseUrl`):

```html
<script src="https://cdn.yourdomain.com/chat-widget/index.js" defer></script>
<script>
  window.addEventListener("DOMContentLoaded", function () {
    window.BusinessChatWidget?.init({
      baseUrl: "https://api.yourdomain.com",
      title: "Hi there!",
      placeholder: "Ask us anything about our services",
      primaryColor: "#2563eb"
    });
  });
</script>
```

## 3. Deployment Notes

- **Backend**: Deploy FastAPI behind HTTPS (e.g., AWS ECS/Fargate, Azure App Service, Vercel serverless) with environment variables mirrored from `.env`.
- **Vector Store**: Managed Qdrant/Pinecone or self-hosted instance reachable by the backend.
- **Docs Refresh**: Automate ingestion via GitHub Actions or scheduled job to keep embeddings current.
- **Monitoring**: Enable structured logging (Loguru is configured) and add APM if needed.
- **Security**: Lock down the API with rate limiting / origin checking, and consider signed session tokens for production.
- **Conversation Memory**: The agent uses LangChain's `ChatOpenAI` with an
  application-managed history cache (`SessionMemory`). Prior messages are stored
  per session and replayed on each turn. Replace the in-memory store with Redis or
  a database for multi-instance deployments.

## 4. Next Steps

- Implement persistent session storage (Redis/Postgres) for multi-device continuity.
- Add analytics instrumentation for widget interactions.
- Expand scheduling integration (two-way availability lookup, ICS attachments).
