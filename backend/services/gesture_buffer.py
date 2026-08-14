"""
GestureSequenceBuffer: a ring buffer that accumulates FrameLandmarks over
a sliding window (default 30-120 frames, configurable) so the recognizer
can reason about *motion* and *trajectory* rather than a single static
pose.
"""
from __future__ import annotations

from collections import deque

from config.settings import get_config
from models.schemas import FrameLandmarks

_config = get_config()


class GestureSequenceBuffer:
    """Fixed-capacity ring buffer of FrameLandmarks.

    `is_ready()` reports whether enough frames have accumulated to attempt
    recognition; the caller (GestureRecognizer) decides the exact policy
    (e.g. fire every N frames once the minimum window is filled, or wait
    for a pause in motion).
    """

    def __init__(
        self,
        min_window: int = _config.sequence_window_min,
        max_window: int = _config.sequence_window_max,
    ) -> None:
        self.min_window = min_window
        self.max_window = max_window
        self._frames: deque[FrameLandmarks] = deque(maxlen=max_window)

    def add(self, frame: FrameLandmarks) -> None:
        self._frames.append(frame)

    def is_ready(self) -> bool:
        return len(self._frames) >= self.min_window

    def snapshot(self) -> list[FrameLandmarks]:
        """Return a copy of the current buffer contents (oldest -> newest)."""
        return list(self._frames)

    def clear(self) -> None:
        self._frames.clear()

    def __len__(self) -> int:
        return len(self._frames)

    def has_hand_activity(self) -> bool:
        """Quick heuristic: is there at least one hand visible in the most
        recent few frames? Used to avoid wasting Gemini calls on empty
        frames (e.g. user stepped away from camera).
        """
        recent = list(self._frames)[-5:]
        return any(f.hands for f in recent)
