from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from loguru import logger

from app.config.settings import get_settings


class SchedulingService:
    """Interact with Calendly (or fallback) to propose/schedule meetings."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def suggest_time_slots(self) -> list[str]:
        """Return candidate meeting slots."""
        # Placeholder implementation: return next three business-day slots.
        now = datetime.utcnow()
        slots = []
        for i in range(1, 4):
            slot = now + timedelta(days=i)
            slots.append(slot.replace(hour=15, minute=0, second=0, microsecond=0).isoformat())
        return slots

    async def schedule_meeting(self, attendee: dict[str, Any], slot: str) -> Optional[str]:
        """Confirm a meeting at the selected slot via Calendly API if available."""
        if not self._settings.calendly_api_token or not self._settings.calendly_user_uri:
            logger.info("Calendly not configured; returning fallback meeting link.")
            return str(self._settings.fallback_meeting_link) if self._settings.fallback_meeting_link else None

        headers = {
            "Authorization": f"Bearer {self._settings.calendly_api_token.get_secret_value()}",
            "Content-Type": "application/json",
        }
        payload = {
            "invitees": [
                {
                    "email": attendee["email"],
                    "name": attendee.get("name", "Website Visitor"),
                }
            ],
            "start_time": slot,
            "end_time": (datetime.fromisoformat(slot) + timedelta(minutes=30)).isoformat(),
            "location": {"type": "zoom"},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.calendly.com/scheduled_events",
                headers=headers,
                json=payload,
            )
            if response.is_error:
                logger.error(
                    "Calendly scheduling failed: {} {}",
                    response.status_code,
                    response.text,
                )
                return None

            data = response.json()
            return data.get("resource", {}).get("uri")

