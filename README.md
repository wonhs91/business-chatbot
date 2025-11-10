# AI Webchat Agent Project

This repository contains two primary components:

- `backend/`: FastAPI-based service hosting a LangGraph-powered conversational agent with document retrieval, scheduling, and Discord notification integrations.
- `widget/`: Embeddable web chat widget that connects to the backend service and can be inserted into a WordPress site.

## High-Level Architecture

```text
┌────────────────┐    HTTPS/WebSocket    ┌───────────────────────┐
│  WordPress UI  │◀────────────────────▶│  Web Chat Widget (JS)  │
└────────────────┘                       └─────────┬────────────┘
                                                  REST / WS
                                                 ┌──────────────┐
                                                 │   Backend    │
                                                 │  FastAPI +   │
                                                 │  LangGraph   │
                                                 └──────┬───────┘
                         ┌─────────────────────┬────────┼────────┬─────────────────────┐
                         │                     │        │        │                     │
               ┌─────────▼───────┐  ┌──────────▼────┐  │  ┌──────▼──────────┐  ┌──────▼─────────┐
               │ Vector Store    │  │ Document      │  │  │ Discord Webhook │  │ Scheduling API │
               │ (Embeddings)    │  │ Ingestion Ops │  │  │ Notifications   │  │ (Calendly/GCal)│
               └─────────────────┘  └───────────────┘  │  └─────────────────┘  └────────────────┘
                                                       │
                                          ┌────────────▼────────────┐
                                          │  LLM Provider (GPT-4o)  │
                                          └─────────────────────────┘
```

### Core Responsibilities

- Deliver a conversational assistant embedded in the website with non-intrusive UX.
- Retrieve answers from internal documents via retrieval-augmented generation (RAG).
- Capture visitor contact information and preferred meeting times.
- Schedule meetings via external APIs and push lead data to Discord.

Implementation details for each component are provided in their respective directories.

## Getting Started

- Backend setup instructions: `backend/README.md` and `docs/SETUP.md`
- Widget setup instructions: `widget/README.md`
- Environment configuration template: `backend/.env.example`

For detailed deployment notes and next steps, review `docs/SETUP.md`.
