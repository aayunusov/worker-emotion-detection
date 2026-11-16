"""On-disk dataset: one folder per participant, one JPEG per posed shot.

Layout (default root is the repository's dataset/ directory):

    dataset/registry.json
    dataset/P0001/meta.json
    dataset/P0001/neutral_01.jpg
    dataset/P0001/neutral_02.jpg
    dataset/P0001/happy_01.jpg
    ...

registry.json maps a Telegram user id to a participant id so /delete can
find the folder. Timestamps are UTC.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from collection_bot.schema import EMOTIONS, POLICY_VERSION, SHOTS_PER_EMOTION

_PARTICIPANT_ID = re.compile(r"^P\d{4,}$")


def next_request(meta: dict) -> tuple[str, int] | None:
    """Return the next (emotion, shot) still missing, or None when all exist."""
    have = {(item["emotion"], int(item["shot"])) for item in meta.get("photos", [])}
    for emotion in EMOTIONS:
        for shot in range(1, SHOTS_PER_EMOTION + 1):
            if (emotion, shot) not in have:
                return emotion, shot
    return None


def stage(meta: dict) -> str:
    """Where this participant is in the session."""
    if not meta.get("consented_at"):
        return "consent"
    if not meta.get("age_band"):
        return "age_band"
    if not meta.get("region"):
        return "region"
    if not meta.get("gender"):
        return "gender"
    if next_request(meta) is not None:
        return "photo"
    if meta.get("allow_example") is None:
        return "example"
    return "complete"


class DatasetStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.json"
        self._lock = threading.RLock()

    def _load_registry(self) -> dict:
        if not self.registry_path.is_file():
            return {"next_id": 1, "users": {}}
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def _participant_dir(self, participant_id: str) -> Path:
        if not _PARTICIPANT_ID.match(participant_id):
            raise ValueError(f"unsafe participant id: {participant_id}")
        folder = (self.root / participant_id).resolve()
        if folder.parent != self.root:
            raise ValueError(f"participant path escapes dataset: {participant_id}")
        return folder

    def _read_meta(self, participant_id: str) -> dict:
        path = self._participant_dir(participant_id) / "meta.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_meta(self, participant_id: str, meta: dict) -> None:
        self._write_json(self._participant_dir(participant_id) / "meta.json", meta)

    def get(self, telegram_id: int) -> dict | None:
        with self._lock:
            registry = self._load_registry()
            entry = registry["users"].get(str(telegram_id))
            if not entry:
                return None
            meta_path = self._participant_dir(entry["participant_id"]) / "meta.json"
            if not meta_path.is_file():
                return None
            return self._read_meta(entry["participant_id"])

    def create(self, telegram_id: int, language: str) -> dict:
        """Create the participant at the moment they accept the policy."""
        with self._lock:
            registry = self._load_registry()
            key = str(telegram_id)
            if key in registry["users"]:
                return self._read_meta(registry["users"][key]["participant_id"])
            participant_id = f"P{int(registry['next_id']):04d}"
            registry["next_id"] = int(registry["next_id"]) + 1
            registry["users"][key] = {"participant_id": participant_id}
            folder = self._participant_dir(participant_id)
            folder.mkdir(parents=True, exist_ok=False)
            meta = {
                "participant_id": participant_id,
                "telegram_id": int(telegram_id),
                "language": language,
                "policy_version": POLICY_VERSION,
                "consented_at": datetime.now(timezone.utc).isoformat(),
                "age_band": None,
                "region": None,
                "gender": None,
                "allow_example": None,
                "photos": [],
            }
            self._write_meta(participant_id, meta)
            self._write_json(self.registry_path, registry)
            return meta

    def update(self, participant_id: str, **fields) -> dict:
        with self._lock:
            meta = self._read_meta(participant_id)
            meta.update(fields)
            self._write_meta(participant_id, meta)
            return meta

    def save_photo(
        self,
        participant_id: str,
        emotion: str,
        shot: int,
        jpeg_bytes: bytes,
    ) -> dict:
        if emotion not in EMOTIONS:
            raise ValueError(f"unknown emotion: {emotion}")
        if shot not in range(1, SHOTS_PER_EMOTION + 1):
            raise ValueError(f"shot out of range: {shot}")
        filename = f"{emotion}_{shot:02d}.jpg"
        with self._lock:
            folder = self._participant_dir(participant_id)
            target = folder / filename
            temporary = target.with_suffix(".jpg.tmp")
            temporary.write_bytes(jpeg_bytes)
            temporary.replace(target)
            meta = self._read_meta(participant_id)
            photos = [
                item
                for item in meta.get("photos", [])
                if not (item["emotion"] == emotion and int(item["shot"]) == shot)
            ]
            photos.append(
                {
                    "emotion": emotion,
                    "shot": shot,
                    "file": filename,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            meta["photos"] = photos
            self._write_meta(participant_id, meta)
            return meta

    def delete(self, telegram_id: int) -> bool:
        with self._lock:
            registry = self._load_registry()
            entry = registry["users"].get(str(telegram_id))
            if not entry:
                return False
            folder = self._participant_dir(entry["participant_id"])
            if folder.is_dir():
                shutil.rmtree(folder)
            registry["users"].pop(str(telegram_id), None)
            self._write_json(self.registry_path, registry)
            return True

    def summary(self) -> dict:
        counts = {emotion: 0 for emotion in EMOTIONS}
        complete = 0
        partial = 0
        with self._lock:
            registry = self._load_registry()
            for entry in registry["users"].values():
                meta_path = self._participant_dir(entry["participant_id"]) / "meta.json"
                if not meta_path.is_file():
                    partial += 1
                    continue
                meta = self._read_meta(entry["participant_id"])
                if stage(meta) == "complete":
                    complete += 1
                else:
                    partial += 1
                for item in meta.get("photos", []):
                    emotion = item["emotion"]
                    counts[emotion] = counts.get(emotion, 0) + 1
        return {
            "root": str(self.root),
            "complete": complete,
            "partial": partial,
            "photos": counts,
            "photo_total": sum(counts.values()),
        }

    def export_manifest(self, path: Path | None = None) -> Path:
        """Write a private CSV. It includes Telegram ids, so keep it in dataset/."""
        target = path or (self.root / "manifest.csv")
        fieldnames = [
            "participant_id",
            "telegram_id",
            "emotion",
            "shot",
            "file",
            "age_band",
            "region",
            "gender",
            "allow_example",
            "language",
            "policy_version",
            "consented_at",
        ]
        rows: list[dict] = []
        with self._lock:
            registry = self._load_registry()
            for entry in registry["users"].values():
                meta = self._read_meta(entry["participant_id"])
                for item in meta.get("photos", []):
                    rows.append(
                        {
                            "participant_id": meta["participant_id"],
                            "telegram_id": meta["telegram_id"],
                            "emotion": item["emotion"],
                            "shot": item["shot"],
                            "file": item["file"],
                            "age_band": meta.get("age_band"),
                            "region": meta.get("region"),
                            "gender": meta.get("gender"),
                            "allow_example": meta.get("allow_example"),
                            "language": meta.get("language"),
                            "policy_version": meta.get("policy_version"),
                            "consented_at": meta.get("consented_at"),
                        }
                    )
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return target
