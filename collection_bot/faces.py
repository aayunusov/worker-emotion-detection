"""Decode a Telegram image, keep a single face, and return a clean JPEG.

Saved files are re-encoded so phone GPS and other EXIF do not stay in the dataset.
The long side is capped at MAX_SIDE pixels.
"""

from __future__ import annotations

import cv2
import numpy as np

MAX_SIDE = 1280
JPEG_QUALITY = 90


def _cascade() -> cv2.CascadeClassifier:
    if not hasattr(cv2, "CascadeClassifier"):
        raise RuntimeError(
            "This OpenCV build has no CascadeClassifier. "
            "Install OpenCV 4 with: pip install 'opencv-python-headless>=4.10,<5'"
        )
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(path)
    if cascade.empty():
        raise RuntimeError(f"Could not load face cascade at {path}")
    return cascade


_CASCADE: cv2.CascadeClassifier | None = None


def _detector() -> cv2.CascadeClassifier:
    global _CASCADE
    if _CASCADE is None:
        _CASCADE = _cascade()
    return _CASCADE


def decode_image(image_bytes: bytes) -> np.ndarray | None:
    if not image_bytes:
        return None
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None or image.size == 0:
        return None
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    height, width = image.shape[:2]
    long_side = max(height, width)
    if long_side > MAX_SIDE:
        scale = MAX_SIDE / long_side
        image = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return image


def count_faces(image: np.ndarray, detect=None) -> int:
    if detect is not None:
        return len(list(detect(image)))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    boxes = _detector().detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(48, 48),
    )
    return len(boxes)


def encode_jpeg(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(
        ".jpg",
        image,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
    )
    if not ok:
        raise RuntimeError("Could not encode JPEG")
    return buffer.tobytes()


def inspect(image_bytes: bytes, detect=None) -> tuple[str, bytes | None]:
    """Return ('ok', jpeg) or ('bad'|'none'|'many', None)."""
    image = decode_image(image_bytes)
    if image is None:
        return "bad", None
    found = count_faces(image, detect=detect)
    if found <= 0:
        return "none", None
    if found > 1:
        return "many", None
    return "ok", encode_jpeg(image)
