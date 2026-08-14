"""
SpeechEngine: local text-to-speech via pyttsx3, used only by the local
desktop entry point (AppController). The web version deliberately does
NOT use this - it uses the browser's Web Speech API on the frontend,
since server-side audio has no reliable way to play back on the client's
device. Keeping both paths lets the same core pipeline run either as a
web app or a standalone local script.
"""
from __future__ import annotations

import pyttsx3

from utils.logger import logger


class SpeechEngine:
    """Thin wrapper around pyttsx3 with configurable rate/volume/voice."""

    def __init__(self, rate: int = 175, volume: float = 1.0, voice_id: str | None = None) -> None:
        self._engine = pyttsx3.init()
        self.set_rate(rate)
        self.set_volume(volume)
        if voice_id:
            self.set_voice(voice_id)

    def list_voices(self) -> list[dict]:
        return [
            {"id": v.id, "name": v.name, "languages": v.languages}
            for v in self._engine.getProperty("voices")
        ]

    def set_rate(self, rate: int) -> None:
        self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float) -> None:
        self._engine.setProperty("volume", max(0.0, min(1.0, volume)))

    def set_voice(self, voice_id: str) -> None:
        self._engine.setProperty("voice", voice_id)

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        logger.debug(f"Speaking: {text!r}")
        self._engine.say(text)
        self._engine.runAndWait()
