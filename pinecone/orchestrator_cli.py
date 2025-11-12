from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agents import OrchestratorAgent
from .cli_utils import chat_loop, load_prompt, show_banner
from .llm import OllamaClient


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pinecone Orchestrator agent standalone CLI."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root the orchestrator should operate on (defaults to CWD).",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("prompts/orchestrator.md"),
        help="Path to the orchestrator prompt template.",
    )
    parser.add_argument(
        "--finder-prompt",
        type=Path,
        default=Path("prompts/finder.md"),
        help="Path to the finder prompt template.",
    )
    parser.add_argument(
        "--reader-prompt",
        type=Path,
        default=Path("prompts/reader.md"),
        help="Path to the reader prompt template.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=OrchestratorAgent.MODEL_NAME,
        help="Override the orchestrator Ollama model name.",
    )
    parser.add_argument(
        "--finder-model",
        type=str,
        default=None,
        help="Optional override for the finder agent model.",
    )
    parser.add_argument(
        "--reader-model",
        type=str,
        default=None,
        help="Optional override for the reader agent model.",
    )
    return parser.parse_args(argv)


def run_orchestrator(
    root: Path,
    prompt_template: str,
    finder_prompt_template: str,
    reader_prompt_template: str,
    model: str,
    finder_model: str | None,
    reader_model: str | None,
) -> None:
    client = OllamaClient()
    agent = OrchestratorAgent.from_workspace(
        root=root,
        prompt_template=prompt_template,
        finder_prompt_template=finder_prompt_template,
        reader_prompt_template=reader_prompt_template,
        client=client,
        model=model,
        finder_model=finder_model,
        reader_model=reader_model,
    )
    show_banner("orchestrator", agent.root)
    chat_loop(agent, agent_label="orchestrator")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    prompt_template = load_prompt(args.prompt)
    finder_prompt_template = load_prompt(args.finder_prompt)
    reader_prompt_template = load_prompt(args.reader_prompt)
    run_orchestrator(
        args.root,
        prompt_template,
        finder_prompt_template,
        reader_prompt_template,
        args.model,
        args.finder_model,
        args.reader_model,
    )


if __name__ == "__main__":
    main()
