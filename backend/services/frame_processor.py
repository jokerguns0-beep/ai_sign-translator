"""
FrameProcessor: turns raw frame data coming from the client (base64 JPEG
over WebSocket) into a numpy/OpenCV image ready for MediaPipe, and applies
any pre-processing (resize, color conversion) needed for stable landmark
detection.
"""
from __future__ import annotations

import base64

import cv2
import numpy as np

from config.settings import get_config
from utils.logger import logger

_config = get_config()


class FrameDecodeError(Exception):
    """Raised when an incoming frame cannot be decoded."""


class FrameProcessor:
    """Stateless helper that decodes and normalizes incoming video frames."""

    def __init__(self, target_width: int | None = None) -> None:
        self.target_width = target_width or _config.frame_target_width

    def decode_base64_frame(self, data_url: str) -> np.ndarray:
        """Decode a base64 data-URL (``data:image/jpeg;base64,...``) into a
        BGR OpenCV image.
        """
        try:
            header, encoded = data_url.split(",", 1) if "," in data_url else ("", data_url)
            raw = base64.b64decode(encoded)
            arr = np.frombuffer(raw, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                raise FrameDecodeError("cv2.imdecode returned None")
            return image
        except Exception as exc:  # noqa: BLE001 - we want to wrap any decode failure
            logger.warning(f"Failed to decode incoming frame: {exc}")
            raise FrameDecodeError(str(exc)) from exc

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Resize to a consistent width (keeps FPS predictable across
        wildly different client cameras) and convert BGR -> RGB, which is
        what MediaPipe expects.
        """
        h, w = image.shape[:2]
        if w != self.target_width:
            scale = self.target_width / w
            image = cv2.resize(image, (self.target_width, int(h * scale)))
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
