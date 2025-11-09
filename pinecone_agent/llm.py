from __future__ import annotations

"""Ollama chat client."""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass
class ChatMessage:
    role: str
    content: str


class OllamaClient:
    def __init__(self, model: str, temperature: float = 0.1, base_url: str | None = None) -> None:
        self.model = model
        self.temperature = temperature
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    def chat(
        self,
        messages: Iterable[ChatMessage],
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [message.__dict__ for message in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = list(tools)
        data_bytes = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            raise RuntimeError(f"Ollama HTTP error {exc.code}: {detail}") from exc
        data: dict[str, Any] = json.loads(body)
        message = data.get("message")
        if not message:
            raise RuntimeError("Ollama returned no message payload")
        return message
