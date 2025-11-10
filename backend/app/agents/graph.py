from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.config.settings import get_settings
from app.models.chat import AgentResponse, ChatMessage, LeadCapture, MeetingProposal
from app.retrieval.service import RetrievalService
from app.services.discord import DiscordNotifier
from app.services.scheduling import SchedulingService


class DecisionPayload(BaseModel):
    """Structured output returned from the LLM for each turn."""

    reply: str = Field(description="Natural language response to the visitor.")
    next_action: Literal["none", "capture_lead", "schedule", "handoff"] = "none"
    lead: LeadCapture | None = None
    meeting: MeetingProposal | None = None


class AgentOrchestrator:
    """Encapsulates the LangGraph agent and supporting services."""

    def __init__(
        self,
        retrieval: RetrievalService | None = None,
        scheduling: SchedulingService | None = None,
        notifier: DiscordNotifier | None = None,
    ) -> None:
        self._settings = get_settings()
        if not self._settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY must be configured.")

        self._llm = ChatOpenAI(
            temperature=0.2,
            model=self._settings.openai_model,
            api_key=self._settings.openai_api_key.get_secret_value(),
            use_responses_api=True
        )
        self._decision_llm = self._llm.with_structured_output(DecisionPayload)
        self._retrieval = retrieval or RetrievalService()
        self._scheduling = scheduling or SchedulingService()
        self._notifier = notifier or DiscordNotifier()
        self._graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("respond", self._respond)
        builder.add_node("capture_lead", self._capture_lead)
        builder.add_node("schedule_meeting", self._schedule_meeting)

        builder.set_entry_point("respond")
        builder.add_conditional_edges(
            "respond",
            self._route_from_response,
            {
                "capture_lead": "capture_lead",
                "schedule_meeting": "schedule_meeting",
                "end": END,
            },
        )
        builder.add_edge("capture_lead", "schedule_meeting")
        builder.add_edge("schedule_meeting", END)
        return builder.compile()

    async def _respond(self, state: AgentState) -> AgentState:
        """Call the LLM with retrieval context to craft the next reply."""
        history = state.get("messages", [])
        if not history:
            raise ValueError("Conversation history required.")

        last_message = history[-1]
        query_text = last_message["content"]

        try:
            context_docs = self._retrieval.get_context(query_text)
            context_text = self._retrieval.format_context(context_docs)
        except Exception as exc:  # pragma: no cover - retrieval failures
            logger.warning("Retrieval failed: {}", exc)
            context_text = ""

        system_prompt = (
            "You are a helpful onboarding assistant for our company website. "
            "Keep responses concise, friendly, and informative. "
            "Always offer value before requesting contact information. "
            "If the visitor asks about our services, use the provided context snippets. "
            "Politely ask for contact details when appropriate and confirm the best meeting time."
        )

        structured_request = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "Conversation so far:\n"
                    f"{self._format_history(history)}\n\n"
                    f"Reference context:\n{context_text or 'None'}\n\n"
                    "Generate the next reply. "
                    "Decide on the next action based on conversation progress. "
                    "If contact info is already captured, avoid asking again. "
                    "If the visitor wants a meeting, set next_action to 'schedule'."
                )
            ),
        ]

        decision = await self._decision_llm.ainvoke(structured_request)
        logger.debug("Decision payload: {}", decision.dict())

        state["messages"] = history + [
            {"role": "assistant", "content": decision.reply},
        ]
        if decision.lead:
            state["lead_info"] = {
                key: value
                for key, value in decision.lead.dict().items()
                if value
            }
        if decision.meeting:
            state["meeting_details"] = decision.meeting.dict()
        state["next_action"] = decision.next_action
        return state

    async def _capture_lead(self, state: AgentState) -> AgentState:
        """Send captured lead details to Discord and mark the state."""
        lead_info = state.get("lead_info")
        if lead_info and lead_info.get("email") and not state.get("lead_captured"):
            await self._notifier.send_embed(
                title="New Website Lead",
                description="Captured contact information from web chat.",
                fields=lead_info,
            )
            state["lead_captured"] = True
        return state

    async def _schedule_meeting(self, state: AgentState) -> AgentState:
        """Handle meeting scheduling intent if requested."""
        meeting_details = state.get("meeting_details") or {}
        if not meeting_details:
            if state.get("next_action") == "schedule":
                # Suggest slots if none provided yet by the LLM
                slots = await self._scheduling.suggest_time_slots()
                state["meeting_details"] = {"proposed_times": slots}
                state.setdefault("messages", []).append(
                    {
                        "role": "assistant",
                        "content": (
                            "Here are a few time slots that could work:\n"
                            + "\n".join(f"- {slot}" for slot in slots)
                            + "\nLet me know which one you prefer."
                        ),
                    }
                )
        else:
            confirmed_time = meeting_details.get("confirmed_time")
            if confirmed_time and not state.get("meeting_scheduled"):
                lead = state.get("lead_info", {})
                if not lead.get("email"):
                    logger.warning("Cannot schedule meeting without lead email.")
                    return state
                invite_url = await self._scheduling.schedule_meeting(
                    attendee=lead,
                    slot=confirmed_time,
                )
                note = (
                    f"Great! I've scheduled the meeting for {confirmed_time}."
                    if invite_url is None
                    else f"Great! I've scheduled the meeting for {confirmed_time}. Here is the invite: {invite_url}"
                )
                state.setdefault("messages", []).append(
                    {
                        "role": "assistant",
                        "content": note,
                    }
                )
                state["meeting_scheduled"] = True
                await self._notifier.send_embed(
                    title="Meeting Scheduled",
                    description="A visitor booked a meeting via the web chat.",
                    fields={
                        "time": confirmed_time,
                        "invite_url": invite_url or "manual follow-up required",
                    },
                )
        state["next_action"] = "none"
        return state

    def _route_from_response(self, state: AgentState) -> str:
        """Determine the next node to execute."""
        next_action = state.get("next_action", "none")
        if next_action == "capture_lead" and not state.get("lead_captured"):
            return "capture_lead"
        if next_action == "schedule" and not state.get("meeting_scheduled"):
            return "schedule_meeting"
        return "end"

    async def run(self, session_id: str, messages: list[ChatMessage]) -> AgentResponse:
        """Execute the graph for a conversation turn."""
        state: AgentState = {
            "session_id": session_id,
            "messages": [message.dict() for message in messages],
            "lead_captured": False,
            "meeting_scheduled": False,
        }
        result_state = await self._graph.ainvoke(state)
        response_messages = [
            ChatMessage(**message) for message in result_state["messages"]
        ]

        return AgentResponse(
            session_id=session_id,
            messages=response_messages,
            lead_captured=result_state.get("lead_captured", False),
            meeting_scheduled=result_state.get("meeting_scheduled", False),
            suggested_slots=(
                result_state.get("meeting_details", {}).get("proposed_times")
                if result_state.get("meeting_details")
                else None
            ),
        )

    @staticmethod
    def _format_history(history: list[dict[str, Any]]) -> str:
        lines = []
        for message in history[-10:]:
            role = message["role"]
            content = message["content"]
            lines.append(f"{role.title()}: {content}")
        return "\n".join(lines)
