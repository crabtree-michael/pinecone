from __future__ import annotations

import argparse
import logging
import sys
import textwrap

from .app import PineconeApp


PROMPT = "pinecone> "


def handle_command(app: PineconeApp, command: str) -> bool:
    """Return False to exit the loop."""
    if command == ":quit":
        return False
    if command == ":history":
        print("-" * 40)
        print(app.render_master_chat())
        print("-" * 40)
        return True
    if command == ":reset":
        app.reset()
        print("State cleared.")
        return True
    print("Unknown command. Available: :history, :reset, :quit")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pinecone",
        description="CLI for the Pinecone multi-agent research assistant.",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the startup banner.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    app = PineconeApp()
    if not args.no_banner:
        banner = textwrap.dedent(
            """
            Pinecone Research Agent
            -----------------------
            Type questions to investigate your workspace.
            Commands: :history, :reset, :quit
            """
        ).strip()
        print(banner)
    while True:
        try:
            raw = input(PROMPT)
        except EOFError:
            print()
            break
        message = raw.strip()
        if not message:
            continue
        if message.startswith(":"):
            if not handle_command(app, message):
                break
            continue
        try:
            response = app.process_user_message(message)
            print(f"orchestrator: {response}")
            print("-" * 40)
            print(app.render_master_chat())
            print("-" * 40)
        except Exception as exc:  # pragma: no cover - interactive resilience
            print(f"[error] {exc}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
