from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence
from urllib import error as urlerror
from urllib import request as urlrequest

from .types import LLMResponse, Message, ToolCall


logger = logging.getLogger(__name__)


class LLMInvocationError(RuntimeError):
    """Raised when the underlying LLM process fails."""


def _default_host() -> str:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host.rstrip("/")


@dataclass
class LLMSettings:
    model: str = "gpt-oss:20b"
    host: str = field(default_factory=_default_host)
    timeout: int = 120


class OllamaClient:
    """HTTP client for the Ollama /api/chat endpoint."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        env_model = os.getenv("PINECONE_MODEL")
        self.settings = settings or LLMSettings()
        if env_model:
            self.settings.model = env_model
        self.endpoint = f"{self.settings.host}/api/chat"

    def generate(self, messages: Sequence[Message]) -> LLMResponse:
        """Send a chat transcript to Ollama and parse the response."""
        serialized = [_serialize_message(msg) for msg in messages]
        # logger.info(
        #     "LLM request (model=%s via %s):\n%s",
        #     self.settings.model,
        #     self.endpoint,
        #     json.dumps(serialized, indent=2),
        # )
        payload = json.dumps(
            {
                "model": self.settings.model,
                "messages": serialized,
                "stream": False,
            }
        ).encode("utf-8")
        request = urlrequest.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(request, timeout=self.settings.timeout) as response:
                raw_http = response.read().decode("utf-8")
        except urlerror.HTTPError as exc:  # pragma: no cover - depends on server
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMInvocationError(detail or f"HTTP error {exc.code}") from exc
        except urlerror.URLError as exc:  # pragma: no cover - depends on server
            raise LLMInvocationError(str(exc)) from exc
        logger.info("LLM HTTP response:\n%s", raw_http.strip())
        http_payload = json.loads(raw_http)
        message = http_payload.get("message") or {}
        content_text = str(message.get("content") or "").strip()
        tool_calls_raw = message.get("tool_calls") or []
        # Back-compat: some prompts ask the LLM to return JSON in content.
        parsed_payload = _maybe_parse_json_object(content_text) if not tool_calls_raw else None
        if parsed_payload:
            content_text = str(parsed_payload.get("content") or "").strip()
            tool_calls_raw = parsed_payload.get("tool_calls") or []
        tool_calls: list[ToolCall] = []
        for call in tool_calls_raw:
            converted = _convert_tool_call(call)
            if converted:
                tool_calls.append(converted)
        return LLMResponse(content=content_text, tool_calls=tool_calls, raw=raw_http)


def build_prompt(
    system_prompt: str,
    history: Iterable[Message],
    response_instructions: str = "",
) -> list[Message]:
    """Build a structured message list for chat-based LLMs."""
    messages: list[Message] = []
    if system_prompt.strip():
        messages.append(Message(role="system", content=system_prompt.strip()))
    messages.extend(history)
    if response_instructions.strip():
        messages.append(Message(role="system", content=response_instructions.strip()))
    return messages


JSON_BLOCK_RE = re.compile(r"(\{.*\})", re.DOTALL)


def _maybe_parse_json_object(output: str) -> dict | None:
    """Return a dict if the string looks like JSON, otherwise None."""
    text = output.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = JSON_BLOCK_RE.search(text)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


def _convert_tool_call(call: dict | None) -> ToolCall | None:
    if not call:
        return None
    function = call.get("function") or {}
    name = function.get("name") or call.get("name")
    if not name:
        return None
    raw_arguments = function.get("arguments") or call.get("arguments") or {}
    if isinstance(raw_arguments, str):
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            arguments = {}
    elif isinstance(raw_arguments, dict):
        arguments = raw_arguments
    else:
        arguments = {}
    return ToolCall(name=name, arguments=arguments)


def _serialize_message(message: Message) -> dict:
    data = {"role": message.role, "content": message.content}
    if message.name:
        data["name"] = message.name
    return data
