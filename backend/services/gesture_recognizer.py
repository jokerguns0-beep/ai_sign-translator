"""
GestureRecognizer: decides *when* to fire a recognition request against
the accumulated GestureSequenceBuffer, and delegates the actual inference
to GeminiClient. Kept separate from GeminiClient so the firing policy
(debouncing, cooldowns) can evolve independently of the API integration.
"""
from __future__ import annotations

import asyncio
import time

from models.schemas import GestureRecognitionResult, SignLanguage
from services.gemini_client import GeminiClient, GeminiClientError
from services.gesture_buffer import GestureSequenceBuffer
from utils.logger import logger


class GestureRecognizer:
    """Wraps a GestureSequenceBuffer + GeminiClient pair for one active
    connection/session, applying a cooldown so we don't spam the API on
    every single frame once the buffer is full.
    """

    def __init__(self, cooldown_seconds: float = 1.5) -> None:
        self.buffer = GestureSequenceBuffer()
        self._client = GeminiClient()
        self._cooldown_seconds = cooldown_seconds
        self._last_fired_at: float = 0.0
        self._lock = asyncio.Lock()
        self.last_error: str | None = None

    def _should_fire(self) -> bool:
        if not self.buffer.is_ready():
            return False
        if not self.buffer.has_hand_activity():
            return False
        return (time.monotonic() - self._last_fired_at) >= self._cooldown_seconds

    async def maybe_recognize(
        self, language: SignLanguage = SignLanguage.RSL
    ) -> GestureRecognitionResult | None:
        """Return a recognition result if the buffer is ready and the
        cooldown has elapsed, otherwise None (caller keeps streaming
        frames).
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
                result = await self._client.recognize(sequence, language)
                logger.info(
                    f"Recognized gesture: '{result.predicted_phrase or result.predicted_word}' "
                    f"(confidence={result.confidence:.2f})"
                )
                self.last_error = None
                return result
            except GeminiClientError as exc:
                # Do not crash the session on a single failed recognition -
                # the buffer keeps accumulating and we'll retry next cycle.
                # Store the reason so the caller can surface it to the user
                # instead of failing silently.
                self.last_error = str(exc)
                return None
