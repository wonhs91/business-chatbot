from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.agents.graph import AgentOrchestrator
from app.models.chat import AgentResponse, ChatTurn

router = APIRouter()


@lru_cache
def get_agent() -> AgentOrchestrator:
    return AgentOrchestrator()


@router.get("/health", response_class=JSONResponse)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=AgentResponse)
async def chat(turn: ChatTurn) -> AgentResponse:
    if not turn.message.content:
        raise HTTPException(status_code=400, detail="Message content required.")

    return await get_agent().run(session_id=turn.session_id, messages=[turn.message])


