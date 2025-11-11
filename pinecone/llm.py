from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from .types import ChatMessage, ChatResponse


class OllamaClient:
    """Thin wrapper around the Ollama chat HTTP API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 300.0) -> None:
        self.base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        ).rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> ChatResponse:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [message.to_dict() for message in messages],
            "stream": stream,
        }
        print(payload)
        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
        )
        response.raise_for_status()

        

        data = response.json()
        print(data)
        message = ChatMessage.from_dict(data.get("message", {}))
        return ChatResponse(message=message, done_reason=data.get("done_reason"))

