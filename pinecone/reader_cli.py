from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agents import ReaderAgent
from .cli_utils import chat_loop, load_prompt, show_banner
from .llm import OllamaClient


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pinecone Reader agent standalone CLI."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root the reader should operate on (defaults to CWD).",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("prompts/reader.md"),
        help="Path to the reader prompt template.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=ReaderAgent.MODEL_NAME,
        help="Override the Ollama model name.",
    )
    return parser.parse_args(argv)


def run_reader(root: Path, prompt_template: str, model: str) -> None:
    client = OllamaClient()
    agent = ReaderAgent.from_workspace(
        root=root,
        prompt_template=prompt_template,
        client=client,
        model=model,
    )
    show_banner("reader", agent.root)
    chat_loop(agent, agent_label="reader", initial_message="")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    prompt_template = load_prompt(args.prompt)
    run_reader(args.root, prompt_template, args.model)


if __name__ == "__main__":
    main()
