from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agents import FinderAgent
from .cli_utils import chat_loop, load_prompt, show_banner
from .llm import OpenRouterClient


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
        help="Override the OpenRouter model name.",
    )
    return parser.parse_args(argv)


def run_finder(root: Path, prompt_template: str, model: str) -> None:
    client = OpenRouterClient()
    agent = FinderAgent.from_workspace(
        root=root,
        prompt_template=prompt_template,
        client=client,
        model=model,
    )
    show_banner("finder", agent.root)
    chat_loop(agent, agent_label="finder")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    prompt_template = load_prompt(args.prompt)
    run_finder(args.root, prompt_template, args.model)


if __name__ == "__main__":
    main()
