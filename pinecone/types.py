from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolFunctionCall:
    name: str
    arguments: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolFunctionCall":
        return cls(name=data.get("name", ""), arguments=data.get("arguments", "{}"))


@dataclass
class ToolCall:
    id: str
    type: str
    function: ToolFunctionCall

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "function": self.function.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "function"),
            function=ToolFunctionCall.from_dict(data.get("function", {})),
        )


@dataclass
class ChatMessage:
    role: Role
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.name:
            payload["name"] = self.name
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            payload["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        tool_calls = [
            ToolCall.from_dict(tc) for tc in data.get("tool_calls", []) or []
        ]
        return cls(
            role=data.get("role", "assistant"),
            content=data.get("content", ""),
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=tool_calls,
        )


@dataclass
class ChatResponse:
    message: ChatMessage
    done_reason: Optional[str] = None

