from __future__ import annotations

from typing import Callable

from .base import Agent, AgentConfig
from ..tools import AskAgentTool


class OrchestratorAgent(Agent):
    def __init__(self, dispatcher: Callable[[str, str], str]) -> None:
        config = AgentConfig(
            name="orchestrator",
            prompt_file="orchestor.md",
            tools=[AskAgentTool(dispatcher)],
        )
        super().__init__(config)
