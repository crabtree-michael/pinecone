from __future__ import annotations

from pathlib import Path

from .base import Agent, AgentConfig
from ..tools import ReadTool


class ReaderAgent(Agent):
    def __init__(self, workspace_root: Path | None = None) -> None:
        config = AgentConfig(
            name="reader",
            prompt_file="reader.md",
            tools=[ReadTool(workspace_root=workspace_root)],
        )
        super().__init__(config)
