"""Cliente para enviar notificaciones al notification-service."""
from __future__ import annotations

from typing import Dict, Optional

import httpx
from loguru import logger

from ..config import get_settings


class NotificationClient:
    """Cliente para disparar notificaciones push/web desde el agente."""

    def __init__(self) -> None:
        settings = get_settings()
        self.notification_url = settings.notification_service_url

    async def send_notification(
        self, user_id: str, title: str, message: str, notification_type: str = "INFO"
    ) -> Dict[str, str]:
        """Envía una notificación al usuario."""
        mutation = """
        mutation CreateNotification($input: CreateNotificationInput!) {
          createNotification(input: $input) {
            id
            title
            message
            type
            read
          }
        }
        """
        input_data = {"userId": user_id, "title": title, "message": message, "type": notification_type}
        payload = {"query": mutation, "variables": {"input": input_data}}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug("Enviando notificación a {}: {}", user_id, title)
                response = await client.post(self.notification_url, json=payload)
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    logger.error("Error al enviar notificación: {}", data["errors"])
                    return {"status": "error", "message": str(data["errors"])}
                return {"status": "ok", "notification_id": data.get("data", {}).get("createNotification", {}).get("id")}
        except httpx.HTTPError as exc:
            logger.warning("Fallo al enviar notificación (servicio no disponible): {}", exc)
            return {"status": "error", "message": str(exc)}

