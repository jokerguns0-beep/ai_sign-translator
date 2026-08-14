"""
RecognitionBackend: the abstract contract every gesture-recognition
engine must satisfy. GeminiClient implements this today; a future
locally-trained model (see training/) can implement the same interface
and be swapped in via GestureRecognizer without touching the buffer,
WebSocket protocol, or frontend at all.
"""
from __future__ import annotations

from typing import Protocol

from models.schemas import FrameLandmarks, GestureRecognitionResult, SignLanguage


class RecognitionBackend(Protocol):
    """Structural interface for any gesture recognition engine."""

    async def recognize(
        self, sequence: list[FrameLandmarks], language: SignLanguage
    ) -> GestureRecognitionResult:
        """Given a windowed sequence of landmarks, return a structured
        recognition result. Implementations should raise a
        backend-specific error on failure so GestureRecognizer can log
        and retry on the next window rather than crashing the session.
        """
        ...