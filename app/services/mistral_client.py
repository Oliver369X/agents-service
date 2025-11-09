from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from loguru import logger

from ..config import get_settings


class MistralOCRClient:
    """Cliente mínimo para OCR usando Mistral."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.mistral_ocr_api_key
        self.base_url = "https://api.mistral.ai/v1/ocr"

    @property
    def headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("Mistral OCR API key no configurada. Revisa MISTRAL_OCR_API_KEY.")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def extract_text(self, document_url: str) -> Dict[str, Any]:
        payload = {"document_url": document_url}
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.debug("Enviando documento a Mistral OCR")
            response = await client.post(self.base_url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()


