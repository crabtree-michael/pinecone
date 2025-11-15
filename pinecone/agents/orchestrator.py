from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from typing import Dict, List

from .base import Agent
from .finder import FinderAgent
from .reader import ReaderAgent
from ..llm import OpenRouterClient
from ..tools import PublishTool, ToolError
from ..types import ChatMessage


class OrchestratorAgent(Agent):
    """Coordinates finder and reader agents via the publish tool."""

    MODEL_NAME = "gpt-5.1"
    RESPONSE_TIMEOUT_SECONDS = 300

    def __init__(
        self,
        *,
        root: Path,
        prompt_template: str,
        finder_prompt_template: str,
        reader_prompt_template: str,
        client: OpenRouterClient,
        model: str | None = None,
        finder_model: str | None = None,
        reader_model: str | None = None,
    ) -> None:
        self.root = root.resolve()
        self.response_timeout = self.RESPONSE_TIMEOUT_SECONDS
        self.sub_agents = self._initialize_sub_agents(
            root=self.root,
            finder_prompt_template=finder_prompt_template,
            reader_prompt_template=reader_prompt_template,
            finder_model=finder_model,
            reader_model=reader_model,
            client=client,
        )
        tools = {"publish": PublishTool(handler=self.publish)}
        super().__init__(
            name="orchestrator",
            model=model or self.MODEL_NAME,
            prompt=prompt_template,
            client=client,
            tools=tools,
        )

    @classmethod
    def from_workspace(
        cls,
        *,
        root: Path,
        prompt_template: str,
        finder_prompt_template: str,
        reader_prompt_template: str,
        client: OpenRouterClient,
        model: str | None = None,
        finder_model: str | None = None,
        reader_model: str | None = None,
    ) -> "OrchestratorAgent":
        return cls(
            root=root,
            prompt_template=prompt_template,
            finder_prompt_template=finder_prompt_template,
            reader_prompt_template=reader_prompt_template,
            client=client,
            model=model,
            finder_model=finder_model,
            reader_model=reader_model,
        )

    def publish(self, *, audience: str, request: str) -> str:
        audience_names = self._resolve_audience(audience)
        if not audience_names:
            raise ToolError("publish requires at least one audience member.")

        self._append_request_to_all(request)
        responses = self._collect_responses(audience_names)
        self._broadcast_responses(responses)
        return self._format_responses(audience_names, responses)

    def _initialize_sub_agents(
        self,
        *,
        root: Path,
        finder_prompt_template: str,
        reader_prompt_template: str,
        finder_model: str | None,
        reader_model: str | None,
        client: OpenRouterClient,
    ) -> Dict[str, Agent]:
        finder_agent = FinderAgent.from_workspace(
            root=root,
            prompt_template=finder_prompt_template,
            client=self._clone_client(client),
            model=finder_model,
        )
        reader_agent = ReaderAgent.from_workspace(
            root=root,
            prompt_template=reader_prompt_template,
            client=self._clone_client(client),
            model=reader_model,
        )
        return {"finder": finder_agent, "reader": reader_agent}

    @staticmethod
    def _clone_client(client: OpenRouterClient) -> OpenRouterClient:
        return OpenRouterClient(
            api_key=client.api_key,
            base_url=client.base_url,
            timeout=client.timeout,
        )

    def _resolve_audience(self, audience: str) -> List[str]:
        audience = audience.lower().strip()
        if audience == "all":
            return list(self.sub_agents.keys())
        if audience not in self.sub_agents:
            raise ToolError(f"Unknown audience '{audience}'.")
        return [audience]

    def _append_request_to_all(self, request: str) -> None:
        for agent in self.sub_agents.values():
            agent.add_message(
                ChatMessage(role="user", name="orchestrator", content=request)
            )

    def _collect_responses(self, recipients: List[str]) -> Dict[str, ChatMessage]:
        responses: Dict[str, ChatMessage] = {}
        if not recipients:
            return responses

        with ThreadPoolExecutor(max_workers=len(recipients)) as executor:
            future_map = {
                executor.submit(self.sub_agents[name].complete): name
                for name in recipients
            }
            for future, name in future_map.items():
                try:
                    responses[name] = future.result(
                        timeout=self.response_timeout
                    )
                except FuturesTimeout:
                    future.cancel()
                    responses[name] = ChatMessage(
                        role="assistant",
                        name=name,
                        content=f"<timeout after {self.response_timeout}s>",
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    responses[name] = ChatMessage(
                        role="assistant",
                        name=name,
                        content=f"<error: {exc}>",
                    )
        return responses

    def _broadcast_responses(self, responses: Dict[str, ChatMessage]) -> None:
        for responder, message in responses.items():
            for name, agent in self.sub_agents.items():
                if name == responder:
                    continue
                agent.add_message(self._clone_message(message, responder))

    @staticmethod
    def _clone_message(message: ChatMessage, responder: str) -> ChatMessage:
        cloned = copy.deepcopy(message)
        cloned.name = responder
        return cloned

    def _format_responses(
        self, recipients: List[str], responses: Dict[str, ChatMessage]
    ) -> str:
        sections: List[str] = []
        for name in recipients:
            reply = responses.get(name)
            body = reply.content if reply and reply.content else "<empty>"
            sections.append(f"[{name}]\n{body}")
        return "\n\n".join(sections)
