from __future__ import annotations

from pathlib import Path

from .base import Agent, AgentConfig
from ..tools import ShellTool


class FinderAgent(Agent):
    def __init__(self, workspace_root: Path | None = None) -> None:
        config = AgentConfig(
            name="finder",
            prompt_file="finder.md",
            tools=[ShellTool(workspace_root=workspace_root)],
        )
        super().__init__(config)
