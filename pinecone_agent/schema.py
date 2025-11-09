from __future__ import annotations

"""Data structures for structured LLM outputs."""

from dataclasses import dataclass, field
from typing import Any, Literal
import json


Action = Literal["plan", "command", "respond", "memory", "noop"]


def parse_action(data: dict[str, Any]) -> "AgentStep":
    try:
        action = data["action"]
    except KeyError as exc:
        raise ValueError(f"Missing action: {data}") from exc
    if action not in {"plan", "command", "respond", "memory", "noop"}:
        raise ValueError(f"Unknown action: {action}")
    action_input = data.get("action_input") or {}
    if not isinstance(action_input, dict):
        raise ValueError("action_input must be an object")
    plan = data.get("plan") or []
    if isinstance(plan, str):
        plan = [plan]
    elif not isinstance(plan, list):
        raise ValueError("plan must be list or string")
    else:
        plan = [str(item) for item in plan]
    return AgentStep(
        thought=str(data.get("thought", "")),
        plan=plan,
        action=action,
        action_input=action_input,
        cite=str(data.get("cite", "")),
    )


@dataclass
class AgentStep:
    thought: str
    plan: list[str]
    action: Action
    action_input: dict[str, Any] = field(default_factory=dict)
    cite: str = ""

    def to_debug(self) -> str:
        return json.dumps(
            {
                "thought": self.thought,
                "plan": self.plan,
                "action": self.action,
                "action_input": self.action_input,
                "cite": self.cite,
            },
            indent=2,
        )
