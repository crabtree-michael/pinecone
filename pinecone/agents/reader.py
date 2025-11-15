from __future__ import annotations

from pathlib import Path
from typing import List

from .base import Agent
from ..llm import OpenRouterClient
from ..tools import ReadTool


class ReaderAgent(Agent):
    """Reader agent capable of inspecting file contents."""

    MODEL_NAME = "gpt-5.1"
    INITIAL_FILE_COUNT = 3

    def __init__(
        self,
        *,
        root: Path,
        prompt_template: str,
        client: OpenRouterClient,
        model: str | None = None,
        initial_context: str | None = None,
    ) -> None:
        read_tool = ReadTool(root=root)
        initial_context = initial_context or self.build_initial_context(
            root=root,
            read_tool=read_tool,
            max_files=self.INITIAL_FILE_COUNT,
        )
        prompt = prompt_template.replace("{initial_context}", initial_context)
        super().__init__(
            name="reader",
            model=model or self.MODEL_NAME,
            prompt=prompt,
            client=client,
            tools={"read": read_tool},
        )
        self.root = root
        self.initial_context = initial_context

    @classmethod
    def from_workspace(
        cls,
        *,
        root: Path,
        prompt_template: str,
        client: OpenRouterClient,
        model: str | None = None,
    ) -> "ReaderAgent":
        return cls(
            root=root,
            prompt_template=prompt_template,
            client=client,
            model=model,
        )

    @classmethod
    def build_initial_context(
        cls,
        *,
        root: Path,
        read_tool: ReadTool,
        max_files: int,
    ) -> str:
        files = cls._select_initial_files(root, max_files=max_files)
        if not files:
            return "No files were found in the workspace root."
        relative_paths = [
            str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
            for path in files
        ]
        return read_tool.run(files=relative_paths)

    @staticmethod
    def _select_initial_files(root: Path, *, max_files: int) -> List[Path]:
        try:
            entries = list(root.resolve().iterdir())
        except FileNotFoundError:
            return []
        files = [entry for entry in entries if entry.is_file()]
        files.sort(key=lambda path: path.name.lower())
        return files[:max_files]
