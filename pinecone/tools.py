from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, Callable, Dict, List, Optional


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


@dataclass
class ReadTool(Tool):
    """Read files from the Pinecone working directory."""

    root: Path
    name: str = "read"
    description: str = (
        "Read one or more files relative to the Pinecone working directory."
    )
    max_files: int = 5
    max_chars_per_file: int = 20000
    delineator_template: Template = field(
        default_factory=lambda: Template("# <$absolute_file_path>")
    )
    parameters: Dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.parameters = {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": (
                        "List of file paths (absolute or relative to the Pinecone "
                        "working directory) to read."
                    ),
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": self.max_files,
                },
            },
            "required": ["files"],
        }

    def run(self, *, files: List[str]) -> str:
        if not files:
            raise ToolError("Provide at least one file to read.")
        if len(files) > self.max_files:
            raise ToolError(f"Read tool supports up to {self.max_files} files at once.")

        sections = [self._read_file(path_str) for path_str in files]
        return "\n\n".join(sections)

    def _read_file(self, raw_path: str) -> str:
        target = self._resolve_path(raw_path)
        header = self.delineator_template.substitute(
            absolute_file_path=str(target)
        )

        if not target.exists():
            return f"{header}\n<missing file>"
        if not target.is_file():
            return f"{header}\n<not a regular file>"

        try:
            contents = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ToolError(f"Failed to read {target}: {exc}") from exc

        truncated = False
        if len(contents) > self.max_chars_per_file:
            contents = contents[: self.max_chars_per_file]
            truncated = True

        body = contents.rstrip()
        if not body:
            body = "<empty file>"
        if truncated:
            body += "\n\n<truncated>"
        return f"{header}\n{body}"

    def _resolve_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        candidate = candidate if candidate.is_absolute() else self.root / candidate
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise ToolError("read tool cannot access paths outside the Pinecone directory")
        return resolved


@dataclass
class PublishTool(Tool):
    """Publish requests to Pinecone sub-agents."""

    handler: Callable[..., str]
    name: str = "publish"
    description: str = (
        "Publish a request to one or more Pinecone sub-agents and collect their responses."
    )
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "audience": {
                    "type": "string",
                    "enum": ["all", "finder", "reader"],
                    "description": "Which sub-agents should respond to the request.",
                },
                "request": {
                    "type": "string",
                    "description": "Instruction to forward to the selected agents.",
                },
            },
            "required": ["audience", "request"],
        }

    def run(self, *, audience: str, request: str) -> str:
        normalized = request.strip()
        if not normalized:
            raise ToolError("publish request cannot be empty.")
        return self.handler(audience=audience, request=normalized)
