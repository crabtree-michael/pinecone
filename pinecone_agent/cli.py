from __future__ import annotations

"""Command line entry point for Pinecone."""

import argparse
import sys

from .agent import PineconeAgent
from .config import AgentConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pinecone: local research agent")
    parser.add_argument("objective", help="Objective/question for Pinecone to solve")
    parser.add_argument("--max-steps", type=int, default=None, help="Override max thinking steps")
    parser.add_argument("--model", type=str, default=None, help="Ollama model name (default from env)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AgentConfig.load()
    if args.max_steps:
        config.max_steps = args.max_steps
    if args.model:
        config.model = args.model
    agent = PineconeAgent(args.objective, config=config)
    result = agent.run()
    if result.success:
        print(result.message)
        if result.citations:
            print(f"Citations: {result.citations}")
        return 0
    print(f"Agent failed: {result.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
