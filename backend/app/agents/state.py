from typing import Any, Literal, TypedDict


class AgentState(TypedDict, total=False):
    """State tracked throughout the LangGraph conversation."""

    session_id: str
    messages: list[dict[str, Any]]
    lead_captured: bool
    meeting_scheduled: bool
    lead_info: dict[str, Any]
    meeting_details: dict[str, Any]
    next_action: Literal[
        "greet",
        "collect_context",
        "answer_question",
        "capture_lead",
        "schedule_meeting",
        "finalize",
    ]

