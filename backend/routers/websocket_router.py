"""
WebSocket router: the frontend streams base64 JPEG frames here, the
backend runs them through the Translator pipeline, and streams back
recognized transcripts + status updates. Kept fully async so a slow
Gemini call never blocks the video stream - `process_frame` only fires
Gemini once per buffer window, and every frame in between is handled
immediately.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.schemas import SignLanguage, WSMessage, WSMessageType
from services.translator import Translator
from utils.logger import logger

router = APIRouter()


@router.websocket("/ws/translate")
async def translate_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    translator = Translator()
    logger.info("WebSocket client connected")

    try:
        await websocket.send_json(
            WSMessage(type=WSMessageType.STATUS, payload={"status": "ready"}).model_dump(mode="json")
        )

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            payload = message.get("payload", {})

            if msg_type == WSMessageType.LANDMARKS.value:
                # payload.frame is a base64 data URL captured by the browser
                result = await translator.process_frame(payload.get("frame", ""))
                if result:
                    await websocket.send_json(
                        WSMessage(
                            type=WSMessageType.TRANSCRIPT,
                            payload=result.model_dump(mode="json"),
                        ).model_dump(mode="json")
                    )
                elif translator.last_error:
                    await websocket.send_json(
                        WSMessage(
                            type=WSMessageType.ERROR,
                            payload={"message": f"Gemini: {translator.last_error}"},
                        ).model_dump(mode="json")
                    )

            elif msg_type == WSMessageType.SET_LANGUAGE.value:
                try:
                    language = SignLanguage(payload.get("language"))
                    translator.set_language(language)
                    await websocket.send_json(
                        WSMessage(
                            type=WSMessageType.STATUS,
                            payload={"status": "language_changed", "language": language.value},
                        ).model_dump(mode="json")
                    )
                except ValueError:
                    await websocket.send_json(
                        WSMessage(
                            type=WSMessageType.ERROR, payload={"message": "Unsupported language"}
                        ).model_dump(mode="json")
                    )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"WebSocket error: {exc}")
        await websocket.close(code=1011)
    finally:
        translator.close()
