from __future__ import annotations

"""Core Pinecone agent loop."""

import json
import shlex
from dataclasses import dataclass
from typing import Any, Optional

from .config import AgentConfig
from .llm import ChatMessage, OllamaClient
from .memory import load_memories, remember
from .prompts import SYSTEM_PROMPT, TOOLS
from .schema import AgentStep, parse_action
from .tools import ToolResult, ToolRunner


@dataclass
class AgentResult:
    success: bool
    message: str
    citations: Optional[str] = None
    steps_taken: int = 0
    last_step: Optional[AgentStep] = None


class PineconeAgent:
    def __init__(self, objective: str, config: Optional[AgentConfig] = None) -> None:
        self.config = config or AgentConfig.load()
        self.objective = objective.strip()
        if not self.objective:
            raise ValueError("Objective cannot be empty")
        self.ollama = OllamaClient(self.config.model, temperature=self.config.temperature)
        self.tool_runner = ToolRunner(self.config.root_dir, max_chars=self.config.max_tool_chars)
        self.memories = load_memories(self.config.memory_dir)
        self.conversation: list[ChatMessage] = []
        self.request_count = 0
        self._seed_conversation()

    def _seed_conversation(self) -> None:
        if self.memories:
            mem_lines = "\n".join(entry.to_prompt() for entry in self.memories)
            memory_text = f"Recent memories:\n{mem_lines}"
        else:
            memory_text = "No stored memories yet."
        initial_user = (
            f"Objective: {self.objective}\n"
            f"{memory_text}\n"
            "Use the available tools (`command`, `action`) to work through SPAR."
        )
        self.conversation = [ChatMessage(role="user", content=initial_user)]

    def run(self) -> AgentResult:
        for step_id in range(1, self.config.max_steps + 1):
            try:
                message = self._request_message()
            except Exception as exc:  # capture and abort
                return AgentResult(False, f"LLM error: {exc}", steps_taken=step_id - 1)

            result = self._handle_message(message, step_id)
            if result is not None:
                return result

        return AgentResult(False, "Max steps exceeded without respond action", steps_taken=self.config.max_steps)

    def _request_message(self) -> dict[str, Any]:
        messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)] + self.conversation
        self.request_count += 1
        self._log_request(messages)
        return self.ollama.chat(messages, tools=TOOLS)

    def _handle_message(self, message: dict[str, Any], step_id: int) -> AgentResult | None:
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            content = (message.get("content") or "").strip()
            if content:
                self._append_observation(f"Unexpected free-form response: {content}")
                return None
            raise RuntimeError("LLM response did not include a tool call")

        call = tool_calls[0]
        function = call.get("function") or {}
        name = function.get("name")
        args = self._normalize_arguments(function.get("arguments"))
        self._record_tool_use(name or "unknown", args)

        if name == "command":
            obs = self._execute_command(args)
            self._append_observation(obs)
            return None
        if name == "action":
            try:
                step = parse_action(args)
            except ValueError as exc:
                self._append_observation(f"Invalid action payload: {exc}")
                return None
            return self._process_action_step(step, step_id)
        if name == "respond":
            result = self._handle_response(args, step_id)
            if result is None:
                return None
            return result

        self._append_observation(f"Unknown tool '{name}' requested.")
        return None

    def _process_action_step(self, step: AgentStep, step_id: int) -> AgentResult | None:
        if step.action == "plan":
            self._append_observation("Plan acknowledged.")
            return None
        if step.action == "noop":
            self._append_observation("No operation executed; provide another action.")
            return None
        if step.action == "command":  # backward compatibility if model regresses
            obs = self._execute_command(step.action_input)
            self._append_observation(obs)
            return None
        if step.action == "memory":
            obs = self._handle_memory(step)
            self._append_observation(obs)
            return None
        if step.action == "respond":
            payload = dict(step.action_input)
            if step.cite and "cite" not in payload:
                payload["cite"] = step.cite
            if step.thought and "thought" not in payload:
                payload["thought"] = step.thought
            result = self._handle_response(payload, step_id)
            if result:
                result.last_step = step
            return result

        self._append_observation(f"Unhandled action '{step.action}'.")
        return None

    def _handle_response(self, payload: dict[str, Any], step_id: int) -> AgentResult | None:
        text = (payload.get("text") or "").strip()
        if not text:
            self._append_observation("Respond tool invoked without text.")
            return None
        cite = payload.get("cite") or payload.get("citation")
        return AgentResult(True, text, citations=cite, steps_taken=step_id)

    def _normalize_arguments(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return {}
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {"text": raw}
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        return {}

    def _record_tool_use(self, name: str, args: dict[str, Any]) -> None:
        summary = json.dumps({"tool": name, "arguments": args}, ensure_ascii=False)
        self.conversation.append(ChatMessage(role="assistant", content=summary))

    def _execute_command(self, payload: dict[str, Any]) -> str:
        command = payload.get("command")
        args = payload.get("args")
        if isinstance(args, str):
            args = shlex.split(args)
        if args is None:
            args = []
        command_line: list[str]
        if command:
            command_line = [command, *args]
        else:
            command_line = args
        if not command_line:
            return "Command action missing command line"
        try:
            result = self.tool_runner.run(command_line)
            self._log_tool_response(result)
            prompt_view = result.for_prompt(self.config.max_tool_chars)
        except Exception as exc:  # convert to observation
            self._log_tool_error(command_line, exc)
            prompt_view = f"Command failed to execute: {exc}"
        return prompt_view

    def _handle_memory(self, step: AgentStep) -> str:
        text = step.action_input.get("text") or step.thought or ""
        if not text.strip():
            return "No memory stored (empty text)."
        path = remember(self.config.memory_dir, text)
        return f"Stored memory at {path}"

    def _append_observation(self, text: str) -> None:
        content = f"Observation: {text}"
        self.conversation.append(ChatMessage(role="user", content=content))

    def _log_request(self, messages: list[ChatMessage]) -> None:
        total_chars = sum(len(msg.content) for msg in messages)
        print(f"\n=== Pinecone Request {self.request_count} ===")
        print(f"Context messages: {len(messages)} | Context chars: {total_chars}")
        for msg in messages:
            content = self._clamp_text(msg.content.strip(), 2000)
            print(f"[{msg.role}] {content}")
        print("=== End Request ===")

    def _log_tool_response(self, result: ToolResult) -> None:
        print("\n--- Tool Response ---")
        print(f"Cmd: {' '.join(result.command)}")
        print(f"Exit: {result.returncode}")
        if result.stdout:
            print("Stdout:")
            print(self._clamp_text(result.stdout, 2000))
        if result.stderr:
            print("Stderr:")
            print(self._clamp_text(result.stderr, 1000))
        print("---------------------\n")

    def _log_tool_error(self, command_line: list[str], exc: Exception) -> None:
        print("\n--- Tool Error ---")
        print(f"Cmd: {' '.join(command_line) or '<none>'}")
        print(f"Error: {exc}")
        print("-------------------\n")

    @staticmethod
    def _clamp_text(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        head = limit // 2
        tail = limit - head - 3
        return text[:head] + "..." + text[-tail:]
