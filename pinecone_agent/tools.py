from __future__ import annotations

"""Command execution utilities limited to safe binaries."""

import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import clamp_text

ALLOWED_COMMANDS = {"ls", "cat", "rg", "grep"}


@dataclass
class ToolResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    def for_prompt(self, limit: int) -> str:
        summary = {
            "cmd": " ".join(shlex.quote(arg) for arg in self.command),
            "code": self.returncode,
            "stdout": clamp_text(self.stdout, limit),
            "stderr": clamp_text(self.stderr, limit // 2),
        }
        return json.dumps(summary, ensure_ascii=False)


class ToolRunner:
    def __init__(self, cwd: Path, max_chars: int = 4000) -> None:
        self.cwd = cwd
        self.max_chars = max_chars

    def run(self, args: Sequence[str]) -> ToolResult:
        if not args:
            raise ValueError("Empty command")
        binary = args[0]
        if binary not in ALLOWED_COMMANDS:
            raise ValueError(f"Command '{binary}' not permitted")
        proc = subprocess.run(
            list(args),
            cwd=self.cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return ToolResult(command=list(args), returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
