from __future__ import annotations

import json
from typing import Dict, List

from ..llm import OpenRouterClient
from ..tools import Tool, ToolError
from ..types import ChatMessage


class Agent:
    """Common functionality shared across Pinecone agents."""

    def __init__(
        self,
        *,
        name: str,
        model: str,
        prompt: str,
        client: OpenRouterClient,
        tools: Dict[str, Tool] | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.client = client
        self.tools = tools or {}
        self.messages: List[ChatMessage] = [
            ChatMessage(role="system", content=prompt)
        ]

    def handle_message(self, content: str) -> ChatMessage:
        """Handle a single message from the orchestrator/user."""
        self.messages.append(ChatMessage(role="user", content=content))
        return self._complete()

    def add_message(self, message: ChatMessage) -> None:
        """Append a message to the transcript without triggering a completion."""
        self.messages.append(message)

    def complete(self) -> ChatMessage:
        """Generate a response based on the current transcript."""
        return self._complete()

    def _complete(self) -> ChatMessage:
        response = self.client.chat(
            model=self.model,
            messages=self.messages,
            tools=[tool.definition() for tool in self.tools.values()]
            if self.tools
            else None,
        )

        assistant_message = response.message
        self.messages.append(assistant_message)

        if assistant_message.tool_calls:
            self._handle_tool_calls(assistant_message)
            return self._complete()

        return assistant_message

    def _handle_tool_calls(self, message: ChatMessage) -> None:
        for call in message.tool_calls:
            tool_name = call.function.name
            tool = self.tools.get(tool_name)
            if not tool:
                tool_output = f"Tool '{tool_name}' is not available."
            else:
                try:
                    arguments = self._parse_arguments(call.function.arguments)
                    tool_output = tool.run(**arguments)
                except ToolError as exc:
                    tool_output = f"Tool error: {exc}"
                except ValueError as exc:
                    tool_output = f"Invalid arguments: {exc}"

            self.messages.append(
                ChatMessage(
                    role="tool",
                    name=tool_name,
                    tool_call_id=call.id,
                    content=tool_output,
                )
            )

    @staticmethod
    def _parse_arguments(arguments: object) -> Dict[str, object]:
        if not arguments:
            return {}
        if isinstance(arguments, dict):
            parsed = arguments
        else:
            try:
                parsed = json.loads(arguments)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("Tool arguments are not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Tool arguments must deserialize into an object.")
        return parsed
