from __future__ import annotations

from pathlib import Path
from typing import List

from .base import Agent
from ..llm import OllamaClient
from ..tools import ShellTool


class FinderAgent(Agent):
    """Finder agent responsible for filesystem discovery."""

    MODEL_NAME = "gpt-oss:20b"
    INITIAL_CONTEXT_DEPTH = 3
    MAX_RESULTS_PER_FOLDER = 100

    def __init__(
        self,
        *,
        root: Path,
        prompt_template: str,
        client: OllamaClient,
        initial_context: str | None = None,
        model: str | None = None,
    ) -> None:
        initial_context = initial_context or self.build_initial_context(
            root,
            depth=self.INITIAL_CONTEXT_DEPTH,
            max_results=self.MAX_RESULTS_PER_FOLDER,
        )
        prompt = prompt_template.replace("{initial_context}", initial_context)
        super().__init__(
            name="finder",
            model=model or self.MODEL_NAME,
            prompt=prompt,
            client=client,
            tools={"shell": ShellTool(root=root)},
        )
        self.root = root
        self.initial_context = initial_context

    @classmethod
    def from_workspace(
        cls,
        *,
        root: Path,
        prompt_template: str,
        client: OllamaClient,
        model: str | None = None,
    ) -> "FinderAgent":
        return cls(
            root=root,
            prompt_template=prompt_template,
            client=client,
            model=model,
        )

    @classmethod
    def build_initial_context(
        cls,
        root: Path,
        *,
        depth: int,
        max_results: int,
    ) -> str:
        resolved_root = root.resolve()
        lines = [f". ({resolved_root})"]
        cls._walk_directory(
            resolved_root,
            current_depth=0,
            max_depth=depth,
            max_results=max_results,
            lines=lines,
        )
        return "\n".join(lines)

    @classmethod
    def _walk_directory(
        cls,
        current_path: Path,
        *,
        current_depth: int,
        max_depth: int,
        max_results: int,
        lines: List[str],
    ) -> None:
        if current_depth >= max_depth:
            return

        try:
            entries = list(current_path.iterdir())
        except (FileNotFoundError, PermissionError):
            lines.append(f"{'  ' * (current_depth + 1)}- <inaccessible>")
            return

        entries = sorted(entries, key=lambda p: (not p.is_dir(), p.name.lower()))
        displayed = entries[:max_results]

        indent = "  " * (current_depth + 1)
        for entry in displayed:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{indent}- {entry.name}{suffix}")
            if entry.is_dir():
                cls._walk_directory(
                    entry,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                    max_results=max_results,
                    lines=lines,
                )

        clipped = len(entries) - len(displayed)
        if clipped > 0:
            lines.append(f"{indent}- ... ({clipped} more entries)")
