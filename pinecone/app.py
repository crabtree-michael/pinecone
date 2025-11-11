from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agents.finder import FinderAgent
from .agents.orchestrator import OrchestratorAgent
from .agents.reader import ReaderAgent


@dataclass
class ChatEntry:
    sender: str
    content: str
    target: str | None = None


class PineconeApp:
    """High-level façade that wires all agents together and exposes the CLI API."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.master_chat: list[ChatEntry] = []
        self.agents = {
            "finder": FinderAgent(self.workspace_root),
            "reader": ReaderAgent(self.workspace_root),
        }
        self.finder = self.agents["finder"]
        self.reader = self.agents["reader"]
        self.orchestrator = OrchestratorAgent(self._dispatch_agent)

    def _dispatch_agent(self, agent_name: str, message: str) -> str:
        if agent_name not in self.agents:
            raise ValueError(f"unknown agent '{agent_name}'")


        self.append_master_chat(ChatEntry(sender='orchestrator', content=message, target=agent_name))
        targeted_response = ""
        for name, agent in self.agents.items():
            if name != agent_name:
                continue
            reply = agent.get_next_answer()
            if reply.strip():
                self.append_master_chat(ChatEntry(sender=name, content=reply))
            targeted_response = reply
        return targeted_response
    
    def append_master_chat(self,entry: ChatEntry):
        self.master_chat.append(entry)
        for name, agent in self.agents.items():
            agent.update_chat_history(entry.content, entry.sender)

    def record_user_message(self, text: str) -> None:
        self.master_chat.append(ChatEntry(sender="user", content=text))

    def process_user_message(self, text: str) -> str:
        """Entry point used by the CLI."""
        self.record_user_message(text)
        response = self.orchestrator.handle(text, sender="user")
        self.master_chat.append(ChatEntry(sender="orchestrator", content=response))
        return response

    def _format_targeted_message(self, target: str, message: str) -> str:
        return f"orchestrator->{target}: {message}"

    def render_master_chat(self) -> str:
        if not self.master_chat:
            return "<empty>"
        lines: list[str] = []
        for entry in self.master_chat:
            prefix = entry.sender if not entry.target else f"{entry.sender}->{entry.target}"
            lines.append(f"{prefix}: {entry.content}")
        return "\n".join(lines)

    def reset(self) -> None:
        self.master_chat.clear()
        for agent in self.agents.values():
            agent.reset()
        self.orchestrator.reset()
