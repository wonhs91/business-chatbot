from typing import Optional

from app.models.chat import LeadCapture, MeetingProposal


class LeadTracker:
    """In-memory placeholder for session lead details (replace with persistent store)."""

    def __init__(self) -> None:
        self._lead: Optional[LeadCapture] = None
        self._meeting: Optional[MeetingProposal] = None

    def set_lead(self, lead: LeadCapture) -> None:
        self._lead = lead

    def get_lead(self) -> Optional[LeadCapture]:
        return self._lead

    def set_meeting(self, meeting: MeetingProposal) -> None:
        self._meeting = meeting

    def get_meeting(self) -> Optional[MeetingProposal]:
        return self._meeting

