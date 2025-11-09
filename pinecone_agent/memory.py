from __future__ import annotations

"""Lightweight markdown memory store."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class MemoryEntry:
    path: Path
    created_at: datetime
    content: str

    def to_prompt(self) -> str:
        timestamp = self.created_at.isoformat(timespec="seconds")
        return f"- {timestamp}: {self.content.strip()}"


def load_memories(memory_dir: Path, limit: int = 5) -> list[MemoryEntry]:
    entries: list[MemoryEntry] = []
    for path in sorted(memory_dir.glob("*.md")):
        try:
            created = datetime.fromtimestamp(path.stat().st_mtime)
            content = path.read_text()
        except OSError:
            continue
        entries.append(MemoryEntry(path=path, created_at=created, content=content))
    return entries[-limit:]


def remember(memory_dir: Path, content: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = memory_dir / f"memory-{timestamp}.md"
    path.write_text(content.strip() + "\n")
    return path
