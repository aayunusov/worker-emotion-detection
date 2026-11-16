"""Run the collection bot.

Images are saved on this computer, under dataset/ (or DATASET_DIR).
The process must stay running while people participate.
"""

from __future__ import annotations

import logging
import sys
import warnings

from collection_bot.config import bot_token, dataset_dir
from collection_bot.faces import _cascade
from collection_bot.storage import DatasetStore


def configure_logging(folder) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(folder / "bot.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # Mixed photo and button session: per_message must stay False.
    from telegram.warnings import PTBUserWarning

    warnings.filterwarnings("ignore", category=PTBUserWarning)


def preflight() -> tuple[str, DatasetStore]:
    token = bot_token()
    root = dataset_dir()
    if not token:
        sys.exit(
            "TELEGRAM_BOT_TOKEN is missing.\n"
            "1. In Telegram, open @BotFather and send /newbot.\n"
            "2. Copy the token into .env (see .env.example).\n"
            "3. Run: python -m collection_bot"
        )
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        sys.exit(f"Cannot write to the dataset folder {root}: {exc}")
    try:
        _cascade()
    except Exception as exc:  # pragma: no cover - depends on the local OpenCV install
        sys.exit(f"Face detector failed to load: {exc}")
    print(f"Saving images to: {root}")
    print("Each person gets a folder such as dataset/P0001/.")
    print("Leave this program running while people participate.")
    return token, DatasetStore(root)


def main() -> None:
    token, store = preflight()
    configure_logging(store.root)
    # Imported after preflight so a missing token fails before Telegram setup,
    # and so unit tests of storage do not need the Telegram package.
    from telegram.ext import Application

    from collection_bot.handlers import build_application

    application = build_application(token, store)
    if not isinstance(application, Application):
        sys.exit("Bot application was not created")
    logging.info("Dataset folder: %s", store.root)
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
