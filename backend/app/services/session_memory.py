from __future__ import annotations

from collections import deque
from typing import Deque, List

from app.models.chat import ChatMessage


class SessionMemory:
    """In-memory conversation store keyed by session ID.

    Replace with a persistent cache (e.g., Redis) for production/multi-instance deployments.
    """

    def __init__(self, *, max_messages: int = 50) -> None:
        self._max_messages = max_messages
        self._history: dict[str, Deque[ChatMessage]] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        history = self._history.get(session_id)
        if not history:
            return []
        return list(history)

    def append_messages(self, session_id: str, messages: List[ChatMessage]) -> None:
        if session_id not in self._history:
            self._history[session_id] = deque(maxlen=self._max_messages)
        history = self._history[session_id]
        history.extend(messages)

    def set_history(self, session_id: str, messages: List[ChatMessage]) -> None:
        self._history[session_id] = deque(messages[-self._max_messages :], maxlen=self._max_messages)

    def clear(self, session_id: str) -> None:
        self._history.pop(session_id, None)
