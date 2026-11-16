"""Paths and environment for the collection bot.

Photos are written under DATASET_DIR, which defaults to <repo>/dataset.
That folder is gitignored. Nothing in this project uploads it.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    """Load a .env file without overriding variables that are already set."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def dataset_dir() -> Path:
    load_env()
    raw = os.environ.get("DATASET_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (REPO_ROOT / "dataset").resolve()


def bot_token() -> str:
    load_env()
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def owner_id() -> int | None:
    load_env()
    raw = os.environ.get("OWNER_TELEGRAM_ID", "").strip()
    if not raw:
        return None
    return int(raw)
