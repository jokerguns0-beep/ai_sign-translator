"""
GeminiClient: sends a buffered gesture sequence (landmark trajectories +
metadata) to Gemini and parses the structured JSON response back into a
GestureRecognitionResult.

Prompt engineering notes:
- We never send raw pixels for every frame (too expensive / slow); instead
  we send normalized landmark trajectories, which Gemini reasons about as
  a compact numeric "motion description". A cropped hand image can
  optionally be attached for the first/last/peak-motion frame to give the
  model visual grounding.
- We force JSON-only output via response_mime_type + an explicit schema in
  the prompt, so parsing is robust.
"""
from __future__ import annotations

import json

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import get_config
from models.schemas import FrameLandmarks, GestureRecognitionResult, SignLanguage
from utils.logger import logger

_config = get_config()

_SYSTEM_PROMPT = """\
Ты — экспертная система распознавания жестового языка. Тебе передаётся
последовательность координат ключевых точек (landmarks) кистей рук, пальцев
и верхней части тела за окно из нескольких десятков кадров, снятая с
веб-камеры пользователя, говорящего на {language}.

Проанализируй:
- траекторию и скорость движения каждой руки;
- форму кисти и взаимное расположение пальцев;
- направление движения относительно тела;
- взаимодействие между обеими руками (если задействованы обе);
- положение корпуса и плеч как дополнительный контекст.

Верни ТОЛЬКО валидный JSON (без markdown, без пояснений) со следующей схемой:
{{
  "recognized_gesture": string,       // краткое техническое описание жеста
  "confidence": number,               // 0.0-1.0
  "predicted_word": string | null,    // наиболее вероятное слово
  "predicted_phrase": string | null,  // наиболее вероятная фраза/предложение, если жест составной
  "alternatives": [{{"text": string, "confidence": number}}]  // до 3 альтернатив
}}
"""


class GeminiClientError(Exception):
    """Raised when Gemini cannot be reached or returns an unparsable response."""


class GeminiClient:
    """Async-friendly wrapper around google-generativeai for gesture
    sequence interpretation.
    """

    def __init__(self) -> None:
        if not _config.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set - GeminiClient will fail on first call")
        genai.configure(api_key=_config.gemini_api_key)
        self._model = genai.GenerativeModel(
            _config.gemini_model,
            generation_config={"response_mime_type": "application/json"},
        )

    def _build_prompt(self, sequence: list[FrameLandmarks], language: SignLanguage) -> str:
        # Compact numeric representation - keeps token usage low and lets
        # Gemini focus on motion/shape rather than parsing verbose JSON.
        compact = [
            {
                "t": f.timestamp_ms,
                "hands": [
                    {
                        "side": h.handedness,
                        "pts": [[round(p.x, 4), round(p.y, 4), round(p.z, 4)] for p in h.landmarks],
                    }
                    for h in f.hands
                ],
                "pose": [[round(p.x, 4), round(p.y, 4)] for p in (f.pose or [])],
            }
            for f in sequence
        ]
        system = _SYSTEM_PROMPT.format(language=language.value.upper())
        return f"{system}\n\nПоследовательность кадров (JSON):\n{json.dumps(compact)}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def recognize(
        self, sequence: list[FrameLandmarks], language: SignLanguage = SignLanguage.RSL
    ) -> GestureRecognitionResult:
        """Send a gesture sequence to Gemini and return a parsed result.

        Retries with exponential backoff on transient failures (network
        blips, rate limits). Raises GeminiClientError if the response
        cannot be parsed after retries are exhausted.
        """
        prompt = self._build_prompt(sequence, language)
        try:
            response = await self._model.generate_content_async(prompt)
            data = json.loads(response.text)
            data["language"] = language.value
            return GestureRecognitionResult.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Gemini recognition failed: {exc}")
            raise GeminiClientError(str(exc)) from exc
