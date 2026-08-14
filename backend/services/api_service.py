"""
APIService: a thin, reusable async HTTP client wrapper with retry/backoff,
used for any external HTTP call that isn't the Gemini SDK itself (e.g.
future third-party sign-language dictionaries, telemetry, webhook
callbacks). Kept separate from GeminiClient to avoid coupling generic
HTTP concerns to Gemini-specific prompt logic.
"""
from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import logger


class APIService:
    """Reusable async HTTP client with sane timeouts and retries."""

    def __init__(self, base_url: str = "", timeout_seconds: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
    async def get(self, path: str, **kwargs) -> httpx.Response:
        response = await self._client.get(path, **kwargs)
        response.raise_for_status()
        return response

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
    async def post(self, path: str, **kwargs) -> httpx.Response:
        response = await self._client.post(path, **kwargs)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        await self._client.aclose()
        logger.debug("APIService HTTP client closed")
