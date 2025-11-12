from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Optional, Union

from .agents.base import Agent


def load_prompt(reference: Union[str, Path]) -> str:
    path = Path(reference)
    if path.is_absolute():
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise SystemExit(f"Prompt file not found: {path}") from None

    relative = str(reference).replace("\\", "/").lstrip("./")
    if not relative:
        raise SystemExit("Prompt reference cannot be empty.")

    prompt_root = resources.files("pinecone")
    parts = [part for part in relative.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise SystemExit("Prompt reference cannot traverse outside the package.")
    target = prompt_root.joinpath(*parts)
    if not target.is_file():
        raise SystemExit(f"Prompt file not found in package: {relative}")
    return target.read_text(encoding="utf-8")


def show_banner(agent_label: str, root: Path) -> None:
    print(f"Pinecone {agent_label.capitalize()} standalone chat")
    print(f"- workspace: {root}")
    print("- type 'exit' or Ctrl-D to quit.\n")


def chat_loop(
    agent: Agent,
    *,
    agent_label: Optional[str] = None,
    initial_message: Optional[str] = None,
) -> None:
    label = (agent_label or agent.name).lower()

    if initial_message is not None:
        response = agent.handle_message(initial_message)
        if response.content:
            print(f"[{label}] {response.content}\n")

    while True:
        try:
            message = input("orchestrator> ").strip()
        except EOFError:
            print()
            break

        if message.lower() in {"exit", "quit"}:
            break
        if not message:
            continue

        response = agent.handle_message(message)
        print(f"[{label}] {response.content}\n")
