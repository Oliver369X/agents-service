from __future__ import annotations

from typing import List, Optional

import strawberry


@strawberry.type
class HealthStatus:
    status: str
    version: str
    integrations: List[str]


@strawberry.type
class GeminiMessage:
    role: str
    content: str


@strawberry.input
class ChatMessageInput:
    role: str
    content: str


@strawberry.type
class ChatResponse:
    messages: List[GeminiMessage]
    raw: Optional[str] = None


@strawberry.type
class OCRResult:
    text: str
    confidence: Optional[float] = None
    raw: Optional[str] = None