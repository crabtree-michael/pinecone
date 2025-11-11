from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class ToolError(RuntimeError):
    """Raised when a tool invocation fails."""


class Tool:
    """Base interface for tool integrations."""

    name: str
    description: str
    parameters: Dict[str, Any]

    def definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def run(self, **kwargs: Any) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class ShellTool(Tool):
    """Execute shell commands constrained to the Pinecone working tree."""

    root: Path
    name: str = "shell"
    description: str = (
        "Execute a shell command relative to the Pinecone working directory."
    )
    max_output_chars: int = 4000
    parameters: Dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.parameters = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute. Avoid long-running commands.",
                },
                "cwd": {
                    "type": "string",
                    "description": (
                        "Optional path relative to the Pinecone working directory "
                        "to run the command from."
                    ),
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 120,
                    "description": "Maximum seconds the command is allowed to run.",
                },
            },
            "required": ["command"],
        }

    def run(
        self, *, command: str, cwd: Optional[str] = None, timeout: int = 30
    ) -> str:
        working_dir = self._resolve_cwd(cwd)
        try:
            completed = subprocess.run(
                command,
                cwd=str(working_dir),
                shell=True,
                check=False,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - defensive
            raise ToolError(f"Command timed out after {timeout}s") from exc
        except FileNotFoundError as exc:  # pragma: no cover - defensive
            raise ToolError("Failed to execute command") from exc

        output = self._format_output(
            completed.stdout, completed.stderr, completed.returncode
        )
        return output[: self.max_output_chars]

    def _resolve_cwd(self, relative: Optional[str]) -> Path:
        candidate = self.root if not relative else (self.root / relative)
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise ToolError("shell tool cannot access paths outside the Pinecone directory")
        return resolved

    @staticmethod
    def _format_output(stdout: str, stderr: str, code: int) -> str:
        stdout = stdout.rstrip() or "<empty>"
        stderr = stderr.rstrip() or "<empty>"
        return f"exit_code: {code}\nstdout:\n{stdout}\nstderr:\n{stderr}"
