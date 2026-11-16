import csv
import tempfile
import unittest
from pathlib import Path

from collection_bot.faces import inspect
from collection_bot.schema import EMOTIONS, SHOTS_PER_EMOTION, TOTAL_PHOTOS
from collection_bot.storage import DatasetStore, next_request, stage
from collection_bot.texts import covered, photo_prompt


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DatasetStore(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_consent_creates_a_private_folder_and_resume_stage(self):
        meta = self.store.create(1001, "uz")
        self.assertEqual(meta["participant_id"], "P0001")
        self.assertTrue((self.store.root / "P0001" / "meta.json").is_file())
        self.assertEqual(stage(meta), "age_band")
        self.assertIsNone(meta["age_band"])
        again = self.store.create(1001, "en")
        self.assertEqual(again["participant_id"], "P0001")
        self.assertEqual(again["language"], "uz")

        second = self.store.create(1002, "ru")
        self.assertEqual(second["participant_id"], "P0002")

    def test_photos_follow_the_prompt_order_and_can_be_deleted(self):
        meta = self.store.create(7, "en")
        meta = self.store.update(meta["participant_id"], age_band="18-24", region="samarqand", gender="female")
        self.assertEqual(stage(meta), "photo")
        saved = 0
        for emotion in EMOTIONS:
            for shot in range(1, SHOTS_PER_EMOTION + 1):
                self.assertEqual(next_request(meta), (emotion, shot))
                meta = self.store.save_photo(meta["participant_id"], emotion, shot, b"\xff\xd8\xff")
                saved += 1
                self.assertEqual(len(meta["photos"]), saved)
                path = self.store.root / meta["participant_id"] / f"{emotion}_{shot:02d}.jpg"
                self.assertEqual(path.read_bytes(), b"\xff\xd8\xff")
        self.assertEqual(saved, TOTAL_PHOTOS)
        self.assertIsNone(next_request(meta))
        self.assertEqual(stage(meta), "example")
        meta = self.store.update(meta["participant_id"], allow_example=False)
        self.assertEqual(stage(meta), "complete")

        # A retake replaces the same slot instead of adding a second row.
        meta = self.store.save_photo(meta["participant_id"], "happy", 1, b"\xff\xd8new")
        happy = [item for item in meta["photos"] if item["emotion"] == "happy" and item["shot"] == 1]
        self.assertEqual(len(happy), 1)
        self.assertEqual((self.store.root / "P0001" / "happy_01.jpg").read_bytes(), b"\xff\xd8new")

        report = self.store.summary()
        self.assertEqual(report["complete"], 1)
        self.assertEqual(report["photo_total"], TOTAL_PHOTOS)
        manifest = self.store.export_manifest()
        with manifest.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), TOTAL_PHOTOS)
        self.assertEqual(rows[0]["telegram_id"], "7")

        self.assertTrue(self.store.delete(7))
        self.assertFalse((self.store.root / "P0001").exists())
        self.assertIsNone(self.store.get(7))
        self.assertFalse(self.store.delete(7))

    def test_participant_ids_cannot_escape_the_dataset_folder(self):
        with self.assertRaises(ValueError):
            self.store._participant_dir("../outside")
        with self.assertRaises(ValueError):
            self.store._participant_dir("P0001/../../etc")


class TextTests(unittest.TestCase):
    def test_every_language_covers_the_same_script(self):
        self.assertTrue(covered())

    def test_photo_prompt_names_the_class_the_file_will_use(self):
        text = photo_prompt("en", "disgust", 2, 12, TOTAL_PHOTOS)
        self.assertIn("Disgust", text)
        self.assertIn("2/2", text)
        self.assertIn("12/14", text)


class FaceTests(unittest.TestCase):
    def test_invalid_bytes_are_rejected(self):
        status, jpeg = inspect(b"this is not an image")
        self.assertEqual(status, "bad")
        self.assertIsNone(jpeg)

    def test_detector_results_decide_the_label(self):
        import cv2
        import numpy as np

        image = np.full((80, 80, 3), 255, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(ok)
        payload = encoded.tobytes()

        status, jpeg = inspect(payload, detect=lambda frame: [object()])
        self.assertEqual(status, "ok")
        self.assertTrue(jpeg.startswith(b"\xff\xd8"))

        status, jpeg = inspect(payload, detect=lambda frame: [])
        self.assertEqual(status, "none")
        self.assertIsNone(jpeg)

        status, jpeg = inspect(payload, detect=lambda frame: [object(), object()])
        self.assertEqual(status, "many")
        self.assertIsNone(jpeg)


if __name__ == "__main__":
    unittest.main()
