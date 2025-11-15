"""Pinecone research agent package."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = []


def _load_package_dotenv() -> None:
    """Load environment variables from pinecone/.env if it exists."""
    package_dir = Path(__file__).resolve().parent
    dotenv_path = package_dir / ".env"
    if not dotenv_path.is_file():
        return

    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        cleaned = value.strip().strip('"').strip("'")
        os.environ[key] = cleaned


_load_package_dotenv()
