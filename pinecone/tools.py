from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class ToolError(RuntimeError):
    """Raised when a tool invocation fails or input is invalid."""


@dataclass
class Tool:
    name: str
    description: str

    def run(self, arguments: dict) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class ShellTool(Tool):
    """Finder tool that can execute whitelisted shell commands."""

    allowed = {"ls", "find"}
    forbidden_tokens = {";", "&&", "||", "|", "&"}

    def __init__(self, workspace_root: Path | None = None) -> None:
        super().__init__(
            name="shell",
            description=(
                "Execute ls via shell"
                "Arguments: {\"command\": \"the command you wish to run\"}."
            ),
        )
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def run(self, arguments: dict) -> str:
        command = str(arguments.get("command") or "").strip()
        if not command:
            raise ToolError("shell command is required")
        try:
            tokens = shlex.split(command)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ToolError(f"invalid command: {exc}") from exc
        if not tokens:
            raise ToolError("shell command is required")
        first = tokens[0]
        if first not in self.allowed:
            raise ToolError(f"command '{first}' is not permitted")
        if any(tok in self.forbidden_tokens for tok in tokens[1:]):
            raise ToolError("command chaining operators are not allowed")
        if any(ch in command for ch in "`\n\r"):
            raise ToolError("invalid characters in command")
        process = subprocess.run(
            tokens,
            capture_output=True,
            text=True,
            cwd=self.workspace_root,
            check=False,
        )
        if process.returncode != 0:
            raise ToolError(process.stderr.strip() or "shell command failed")
        return process.stdout.strip()


class ReadTool(Tool):
    """Reader tool that returns inline file contents."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        super().__init__(
            name="read",
            description=(
                "Read a list of relative file paths and return their content in "
                "<path>content</path> format. Arguments: {\"documents\": [\"README.md\"]}."
            ),
        )
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def run(self, arguments: dict) -> str:
        docs = arguments.get("documents")
        if not docs:
            raise ToolError("documents is required")
        output_chunks: list[str] = []
        root = self.workspace_root
        for doc in docs:
            rel_path = Path(str(doc))
            target = (root / rel_path).resolve()
            print(target)
            if not target.is_relative_to(root):
                raise ToolError(f"access outside workspace denied for {rel_path}")
            if not target.exists():
                raise ToolError(f"{rel_path} does not exist")
            content = target.read_text(encoding="utf-8", errors="ignore")
            output_chunks.append(f"<{rel_path}>{content}</{rel_path}>")
        print(output_chunks)
        return "\n".join(output_chunks)


class AskAgentTool(Tool):
    """Orchestrator tool used to query other agents."""

    def __init__(self, dispatcher: Callable[[str, str], str]) -> None:
        super().__init__(
            name="ask_agent",
            description=(
                "Route a question to another agent. Arguments: "
                "{\"agent\": \"finder|reader\", \"message\": \"text\"}."
            ),
        )
        self.dispatcher = dispatcher

    def run(self, arguments: dict) -> str:
        agent = str(arguments.get("agent") or "").strip()
        message = str(arguments.get("message") or "").strip()
        if agent not in {"finder", "reader"}:
            raise ToolError("agent must be 'finder' or 'reader'")
        if not message:
            raise ToolError("message is required")
        return self.dispatcher(agent, message)
