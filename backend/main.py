"""
FastAPI application entrypoint.

Run locally with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_config
from routers import history_router, websocket_router
from utils.logger import logger

config = get_config()

app = FastAPI(
    title="AI Sign Language Translator API",
    description="Real-time sign-language-to-text-and-speech translation backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router.router)
app.include_router(history_router.router)

@app.get("/")
async def read_root():
    return {"message": "Бэкенд AI Sign Language Translator успешно запущен!"}

@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "env": config.app_env}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"AI Sign Language Translator API starting (env={config.app_env})")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("AI Sign Language Translator API shutting down")
