"""
CameraManager: owns a local OpenCV VideoCapture device. Only used by the
local/desktop entry point (AppController) - the web app gets its frames
from the browser over WebSocket instead, since a server has no direct
access to the end user's webcam.
"""
from __future__ import annotations

from collections.abc import Iterator

import cv2
import numpy as np

from utils.logger import logger


class CameraError(Exception):
    pass


class CameraManager:
    """Context-manager wrapper around cv2.VideoCapture."""

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self._cap: cv2.VideoCapture | None = None

    def __enter__(self) -> "CameraManager":
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            raise CameraError(f"Could not open camera device {self.device_index}")
        logger.info(f"Camera device {self.device_index} opened")

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._cap is not None:
            self._cap.release()
            logger.info("Camera released")

    def frames(self) -> Iterator[np.ndarray]:
        if self._cap is None:
            # Использование явного исключения вместо assert гарантирует, что проверка
            # всегда будет выполняться, независимо от режима запуска Python.
            raise RuntimeError("CameraManager must be initialized as a context manager before calling frames.")
        while True:
            ok, frame = self._cap.read()
            if not ok:
                logger.warning("Failed to read frame from camera")
                break
            yield frame
