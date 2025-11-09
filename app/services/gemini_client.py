from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from loguru import logger

from ..config import get_settings


class GeminiClient:
    """Cliente mínimo para consumir Gemini 2.5 Pro vía API REST."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("Gemini API key no configurada. Revisa GEMINI_API_KEY.")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def chat(self, messages: list[dict[str, str]]) -> Dict[str, Any]:
        """Invoca el modelo conversacional."""
        url = f"{self.base_url}/models/gemini-2.5-pro-latest:generateContent"
        payload = {"contents": [{"parts": messages}]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug("Enviando solicitud a Gemini")
            response = await client.post(url, json=payload, headers=self.headers, params={"key": self.api_key})
            response.raise_for_status()
            return response.json()


