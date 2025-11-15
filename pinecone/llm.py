from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from .types import ChatMessage, ChatResponse


class OpenRouterClient:
    """Thin wrapper around the OpenRouter-compatible chat completion API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = (
            base_url
            or os.environ.get("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1"
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
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set; please export your OpenRouter API key."
            )

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [message.to_dict() for message in messages],
            "stream": stream,
            "tools": tools or [],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            message = data["error"].get("message", "Unknown OpenRouter error")
            raise RuntimeError(f"OpenRouter API error: {message}")

        choices = data.get("choices")
        if not choices:
            raise RuntimeError("OpenRouter API returned no choices.")

        choice = choices[0]
        message = ChatMessage.from_dict(choice.get("message", {}))
        finish_reason = choice.get("finish_reason")
        return ChatResponse(message=message, done_reason=finish_reason)
