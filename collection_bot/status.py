"""Print how many participants and photos are on disk."""

from __future__ import annotations

from collection_bot.config import dataset_dir
from collection_bot.schema import EMOTIONS
from collection_bot.storage import DatasetStore


def main() -> None:
    store = DatasetStore(dataset_dir())
    report = store.summary()
    print(f"Dataset folder: {report['root']}")
    print(f"Complete: {report['complete']}")
    print(f"Still in progress: {report['partial']}")
    print(f"Photos: {report['photo_total']}")
    for emotion in EMOTIONS:
        print(f"  {emotion}: {report['photos'][emotion]}")


if __name__ == "__main__":
    main()
