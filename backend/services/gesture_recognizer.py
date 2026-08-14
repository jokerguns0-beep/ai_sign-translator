"""
GestureRecognizer: decides *when* to fire a recognition request against
the accumulated GestureSequenceBuffer, delegates inference to a
RecognitionBackend (Gemini today, potentially a locally-trained model
later - see services/recognition_backend.py), and applies a lightweight
consensus check before trusting a result: a single noisy frame window
should not be enough to emit an answer.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque

from models.schemas import GestureRecognitionResult, SignLanguage
from services.gemini_client import GeminiClient, GeminiClientError
from services.gesture_buffer import GestureSequenceBuffer
from services.recognition_backend import RecognitionBackend
from utils.logger import logger

# Below this confidence, a single window is never trusted on its own -
# it must be confirmed by a matching next window (see _check_consensus).
HIGH_CONFIDENCE_THRESHOLD = 0.85


class GestureRecognizer:
    """Wraps a GestureSequenceBuffer + RecognitionBackend pair for one
    active connection/session, applying a cooldown so we don't spam the
    API on every single frame once the buffer is full, plus a consensus
    check across consecutive windows to filter out one-off
    misrecognitions.
    """

    def __init__(
        self,
        backend: RecognitionBackend | None = None,
        cooldown_seconds: float = 1.5,
    ) -> None:
        self.buffer = GestureSequenceBuffer()
        self._backend: RecognitionBackend = backend or GeminiClient()
        self._cooldown_seconds = cooldown_seconds
        self._last_fired_at: float = 0.0
        self._lock = asyncio.Lock()
        self.last_error: str | None = None
        self._recent: deque[GestureRecognitionResult] = deque(maxlen=2)

    def _should_fire(self) -> bool:
        if not self.buffer.is_ready():
            return False
        if not self.buffer.has_hand_activity():
            return False
        return (time.monotonic() - self._last_fired_at) >= self._cooldown_seconds

    @staticmethod
    def _same_answer(a: GestureRecognitionResult, b: GestureRecognitionResult) -> bool:
        text_a = (a.predicted_phrase or a.predicted_word or "").strip().lower()
        text_b = (b.predicted_phrase or b.predicted_word or "").strip().lower()
        return bool(text_a) and text_a == text_b

    def _check_consensus(self, result: GestureRecognitionResult) -> bool:
        """Return True if this result should be treated as confirmed
        (trusted enough to save to history / speak aloud), based on
        either high standalone confidence or agreement with the
        immediately preceding window's answer.

        Importantly, this NEVER blocks the result from reaching the
        frontend - it only tags it. A silently-withheld result is much
        harder to debug than a visibly "tentative" one.
        """
        self._recent.append(result)

        if result.confidence >= HIGH_CONFIDENCE_THRESHOLD:
            return True

        if len(self._recent) == 2 and self._same_answer(self._recent[0], self._recent[1]):
            return True

        logger.info(
            f"Recognition '{result.predicted_phrase or result.predicted_word}' "
            f"(confidence={result.confidence:.2f}) is tentative - sent to client but not confirmed"
        )
        return False

    async def maybe_recognize(
        self, language: SignLanguage = SignLanguage.RSL
    ) -> GestureRecognitionResult | None:
        """Return a recognition result if the buffer is ready and the
        cooldown has elapsed - otherwise None (caller keeps streaming
        frames). The result is ALWAYS returned once the backend responds;
        `result.confirmed` tells the caller whether it passed the
        consensus check.
        """
        if not self._should_fire():
            return None

        async with self._lock:
            # Re-check inside the lock in case another task already fired.
            if not self._should_fire():
                return None
            self._last_fired_at = time.monotonic()
            sequence = self.buffer.snapshot()
            try:
                result = await self._backend.recognize(sequence, language)
                logger.info(
                    f"Recognized gesture: '{result.predicted_phrase or result.predicted_word}' "
                    f"(confidence={result.confidence:.2f})"
                )
                self.last_error = None
                result.confirmed = self._check_consensus(result)
                return result
            except GeminiClientError as exc:
                # Do not crash the session on a single failed recognition -
                # the buffer keeps accumulating and we'll retry next cycle.
                # Store the reason so the caller can surface it to the user
                # instead of failing silently.
                self.last_error = str(exc)
                return None
