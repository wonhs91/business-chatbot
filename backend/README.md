# Backend Service

This FastAPI service hosts the LangGraph-based conversational agent that powers the website widget.

## Key Modules

- `app/api/`: HTTP and WebSocket routes for chat sessions and health checks.
- `app/agents/`: LangGraph graph definition and supporting nodes.
- `app/services/`: Integrations such as Discord notifications and scheduling APIs.
- `app/retrieval/`: Document ingestion pipeline and vector store utilities.
- `app/models/`: Pydantic schemas shared across modules.
- `app/config/`: Settings management and environment loading.

## Running Locally

```bash
uvicorn app.main:app --reload
```

Before running, create a `.env` file (see `app/config/settings.py`) with credentials for:

- OpenAI (or alternative LLM provider)
- Vector store (e.g., Qdrant URL and API key)
- Discord webhook URL
- Scheduling provider (Calendly or Google Calendar)
