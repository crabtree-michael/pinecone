from __future__ import annotations

"""Configuration helpers for the Pinecone agent."""

from dataclasses import dataclass
env_int = int
import os
from pathlib import Path


@dataclass
class AgentConfig:
    root_dir: Path
    memory_dir: Path
    model: str
    max_steps: int = 15
    max_tool_chars: int = 4_000
    temperature: float = 0.1

    @classmethod
    def load(cls) -> "AgentConfig":
        root = Path(os.environ.get("PINECONE_ROOT", Path.cwd()))
        memory = Path(os.environ.get("PINECONE_MEMORY", root / "memory"))
        model = os.environ.get("PINECONE_MODEL", "llama3")
        max_steps = int(os.environ.get("PINECONE_MAX_STEPS", "12"))
        max_tool_chars = int(os.environ.get("PINECONE_MAX_TOOL_CHARS", "4000"))
        temperature = float(os.environ.get("PINECONE_TEMPERATURE", "0.1"))
        memory.mkdir(parents=True, exist_ok=True)
        return cls(
            root_dir=root,
            memory_dir=memory,
            model=model,
            max_steps=max_steps,
            max_tool_chars=max_tool_chars,
            temperature=temperature,
        )


def clamp_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head - 3
    return text[:head] + "..." + text[-tail:]
