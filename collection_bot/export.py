"""Write dataset/manifest.csv. This file contains Telegram ids. Do not publish it."""

from __future__ import annotations

from collection_bot.config import dataset_dir
from collection_bot.storage import DatasetStore


def main() -> None:
    store = DatasetStore(dataset_dir())
    path = store.export_manifest()
    print(f"Wrote {path}")
    print("This file stays inside the dataset folder. Do not commit or publish it.")


if __name__ == "__main__":
    main()
