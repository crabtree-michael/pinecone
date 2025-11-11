from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agents import FinderAgent
from .llm import OllamaClient


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pinecone Finder agent standalone CLI."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root the finder should operate on (defaults to CWD).",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("prompts/finder.md"),
        help="Path to the finder prompt template.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=FinderAgent.MODEL_NAME,
        help="Override the Ollama model name.",
    )
    return parser.parse_args(argv)


def load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {path}") from None


def run_finder(root: Path, prompt_template: str, model: str) -> None:
    client = OllamaClient()
    agent = FinderAgent.from_workspace(
        root=root,
        prompt_template=prompt_template,
        client=client,
        model=model,
    )
    show_banner(agent)
    loop(agent)


def show_banner(agent: FinderAgent) -> None:
    print("Pinecone Finder standalone chat")
    print(f"- workspace: {agent.root}")
    print("- type 'exit' or Ctrl-D to quit.\n")


def loop(agent: FinderAgent) -> None:
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
        print(f"[finder] {response.content}\n")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    prompt_template = load_prompt(args.prompt)
    run_finder(args.root, prompt_template, args.model)


if __name__ == "__main__":
    main()
