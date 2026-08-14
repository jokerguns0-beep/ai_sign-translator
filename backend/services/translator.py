"""
Translator: the per-session orchestrator that ties together
FrameProcessor -> LandmarkDetector -> GestureSequenceBuffer ->
GestureRecognizer -> HistoryManager. One Translator instance is created
per WebSocket connection (see routers/websocket_router.py) so different
users' buffers never mix - but it shares one process-wide LandmarkDetector
(MediaPipe graphs are too memory-heavy to create per connection, see
services/landmark_detector.py).
"""
from __future__ import annotations

from models.schemas import GestureRecognitionResult, SignLanguage
from services.frame_processor import FrameDecodeError, FrameProcessor
from services.gesture_recognizer import GestureRecognizer
from services.history_manager import HistoryManager
from services.landmark_detector import get_shared_landmark_detector
from utils.logger import logger


class Translator:
    """Owns the full per-connection pipeline state."""

    def __init__(self, language: SignLanguage = SignLanguage.RSL) -> None:
        self.language = language
        self._frame_processor = FrameProcessor()
        self._landmark_detector = get_shared_landmark_detector()
        self._recognizer = GestureRecognizer()
        self._history = HistoryManager()

    def set_language(self, language: SignLanguage) -> None:
        logger.info(f"Session language changed to {language.value}")
        self.language = language
        self._recognizer.buffer.clear()

    async def process_frame(self, data_url: str) -> GestureRecognitionResult | None:
        """Feed one raw frame through the pipeline. Returns a recognition
        result only when the buffer fires (most calls return None while
        the buffer is still accumulating).
        """
        try:
            image = self._frame_processor.decode_base64_frame(data_url)
        except FrameDecodeError:
            return None

        rgb = self._frame_processor.preprocess(image)
        landmarks = self._landmark_detector.detect(rgb)
        self._recognizer.buffer.add(landmarks)

        result = await self._recognizer.maybe_recognize(self.language)
        if result and result.confirmed and (result.predicted_phrase or result.predicted_word):
            text = result.predicted_phrase or result.predicted_word or ""
            self._history.add(text=text, language=self.language, confidence=result.confidence)
        return result

    @property
    def last_error(self) -> str | None:
        """Reason the last Gemini recognition attempt failed, if any."""
        return self._recognizer.last_error

    def close(self) -> None:
        # Intentionally does NOT close the shared LandmarkDetector - it
        # outlives individual connections. See main.py shutdown handler.
        pass
