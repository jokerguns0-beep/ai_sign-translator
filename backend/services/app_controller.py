"""
AppController: top-level facade for the LOCAL (non-web) run mode - opens
the webcam directly, runs it through the same Translator pipeline used by
the web app, and speaks results aloud with pyttsx3. Useful for quick
testing on a dev machine without starting the frontend at all.

Run with:  python -m services.app_controller
"""
from __future__ import annotations

import asyncio
import base64

import cv2

from models.schemas import SignLanguage
from services.camera_manager import CameraManager
from services.speech_engine import SpeechEngine
from services.translator import Translator
from utils.logger import logger


class AppController:
    def __init__(self, language: SignLanguage = SignLanguage.RSL) -> None:
        self.translator = Translator(language=language)
        self.speech = SpeechEngine()

    @staticmethod
    def _frame_to_data_url(frame) -> str:
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("Failed to encode frame")
        return "data:image/jpeg;base64," + base64.b64encode(buf).decode("ascii")

    async def run(self) -> None:
        logger.info("Starting local AppController - press 'q' to quit")
        with CameraManager() as camera:
            for frame in camera.frames():
                result = await self.translator.process_frame(self._frame_to_data_url(frame))
                if result and (result.predicted_phrase or result.predicted_word):
                    text = result.predicted_phrase or result.predicted_word
                    print(f">> {text} (confidence={result.confidence:.2f})")
                    self.speech.speak(text)

                cv2.imshow("AI Sign Language Translator (local)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        self.translator.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(AppController().run())
