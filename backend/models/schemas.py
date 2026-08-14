"""
Pydantic models shared across the backend: landmark frames, gesture
sequences, Gemini responses, WebSocket message envelopes, and history
records. Keeping these in one module avoids circular imports between
services and routers.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SignLanguage(str, Enum):
    """Supported (or planned) national sign languages.

    Only RSL is fully wired up today; the others are placeholders so the
    frontend/backend contract does not need to change when they are added.
    """

    RSL = "rsl"  # Русский жестовый язык (default)
    ASL = "asl"
    BSL = "bsl"


class Point3D(BaseModel):
    x: float
    y: float
    z: float
    visibility: float | None = None  # only present for pose landmarks


class HandLandmarks(BaseModel):
    handedness: Literal["Left", "Right"]
    landmarks: list[Point3D] = Field(..., min_length=21, max_length=21)


class FrameLandmarks(BaseModel):
    """All landmark data extracted from a single video frame."""

    timestamp_ms: int
    hands: list[HandLandmarks] = Field(default_factory=list)
    pose: list[Point3D] | None = None  # 33 pose landmarks (torso, shoulders, elbows...)


class GestureAlternative(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class GestureRecognitionResult(BaseModel):
    """The structured result returned by Gemini for one gesture sequence."""

    recognized_gesture: str
    confidence: float = Field(ge=0.0, le=1.0)
    predicted_word: str | None = None
    predicted_phrase: str | None = None
    alternatives: list[GestureAlternative] = Field(default_factory=list)
    language: SignLanguage = SignLanguage.RSL
    confirmed: bool = True  # passed consensus check (see GestureRecognizer) - False means "tentative"


class WSMessageType(str, Enum):
    LANDMARKS = "landmarks"          # frontend -> backend: one frame of landmarks
    TRANSCRIPT = "transcript"        # backend -> frontend: recognized text
    STATUS = "status"                # backend -> frontend: model/buffer status
    ERROR = "error"
    SET_LANGUAGE = "set_language"    # frontend -> backend


class WSMessage(BaseModel):
    type: WSMessageType
    payload: dict


class HistoryEntry(BaseModel):
    id: str
    text: str
    language: SignLanguage
    confidence: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
