from typing import Any

import httpx
from loguru import logger

from app.config.settings import get_settings


class DiscordNotifier:
    """Sends lead and meeting notifications to a Discord channel."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def send_embed(self, title: str, description: str, fields: dict[str, Any]) -> None:
        if not self._settings.discord_webhook_url:
            logger.warning("Discord webhook URL not configured; skipping notification.")
            return

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "fields": [
                        {"name": key, "value": str(value), "inline": False}
                        for key, value in fields.items()
                    ],
                }
            ]
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                str(self._settings.discord_webhook_url),
                json=payload,
            )
            response.raise_for_status()
            logger.info("Sent Discord notification: {}", title)

