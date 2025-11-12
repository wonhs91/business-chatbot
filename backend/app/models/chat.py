from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message in the conversation history."""

    role: Literal["user", "assistant", "system"] = Field(description="Message author.")
    content: str = Field(description="Text content of the message.")
    # timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatTurn(BaseModel):
    """Incoming chat payload from the widget."""

    session_id: str
    message: ChatMessage
    # history: list[ChatMessage] = Field(default_factory=list)
    # metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Agent response wrapper returned to the widget."""

    session_id: str
    messages: list[ChatMessage]
    lead_captured: bool = False
    meeting_scheduled: bool = False
    suggested_slots: Optional[list[str]] = None


class LeadCapture(BaseModel):
    """Lead information captured during conversation."""

    name: str | None = None
    email: str | None = None
    company: str | None = None
    phone: str | None = None
    notes: str | None = None


class MeetingProposal(BaseModel):
    """Meeting proposal details."""

    proposed_times: list[str] = Field(default_factory=list)
    confirmed_time: str | None = None
    calendly_invite_url: str | None = None
