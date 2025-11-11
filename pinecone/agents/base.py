from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..llm import OllamaClient, build_prompt
from ..tools import Tool, ToolError
from ..types import LLMResponse, Message, ToolCall


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt_file(filename: str) -> str:
    path = PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


@dataclass
class AgentConfig:
    name: str
    prompt_file: str
    tools: Iterable[Tool] = ()
    max_tool_loops: int = 10


class Agent:
    def __init__(self, config: AgentConfig, llm: OllamaClient | None = None) -> None:
        self.config = config
        self.llm = llm or OllamaClient()
        self.history: list[Message] = []
        self.tools = {tool.name: tool for tool in config.tools}
        agent_prompt = load_prompt_file(config.prompt_file)
        tool_text = self._tool_description()
        self.system_prompt = "\n\n".join(
            part
            for part in (agent_prompt.strip(), tool_text.strip())
            if part
        )

    def _tool_description(self) -> str:
        if not self.tools:
            return "No tools are available."
        lines = ["Available tools (use the exact name shown when making tool calls):"]
        for tool in self.tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def reset(self) -> None:
        self.history.clear()

    def handle(self, message: str, sender: str = "system") -> str:
        self.update_chat_history(message, sender, "user")
        return self.get_next_answer()

    def update_chat_history(self, message, sender: str = "system", role: str = "user"):
        self.history.append(Message(role, content=message, name=sender))
    
    def get_next_answer(self):
        for _ in range(self.config.max_tool_loops):
            prompt = build_prompt(self.system_prompt, self.history)
            response = self.llm.generate(prompt)
            self.history.append(Message(role="assistant", content=response.content, name=self.config.name))
            if response.tool_calls:
                self._process_tools(response)
                continue
            return response.content
        raise RuntimeError(f"{self.config.name} exceeded tool loop limit")

    def _process_tools(self, response: LLMResponse) -> None:
        for call in response.tool_calls:
            tool = self._resolve_tool(call)
            if not tool:
                error = f"Unknown tool '{call.name}'"
                self.history.append(Message(role="tool", content=error, name=call.name))
                continue
            try:
                result = tool.run(call.arguments)
            except ToolError as exc:
                result = f"ToolError: {exc}"
            print("Adding to tool history", result)
            self.history.append(Message(role="tool", content=result, name=call.name))

    def _resolve_tool(self, call: ToolCall) -> Tool | None:
        tool = self.tools.get(call.name)
        if tool:
            return tool
        if len(self.tools) == 1:
            return next(iter(self.tools.values()))
        if isinstance(call.arguments, dict):
            alias = call.arguments.get("name") or call.arguments.get("tool")
            if isinstance(alias, str):
                return self.tools.get(alias)
        return None
