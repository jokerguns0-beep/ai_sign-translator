"""
History REST router: list recent translations, export as TXT/PDF, clear
history. All blocking sqlite/reportlab calls are pushed to a thread pool
so they never stall the event loop.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from models.schemas import HistoryEntry
from services.history_manager import HistoryManager

router = APIRouter(prefix="/api/history", tags=["history"])
_history = HistoryManager()


@router.get("", response_model=list[HistoryEntry])
async def list_history(limit: int = 50) -> list[HistoryEntry]:
    return await run_in_threadpool(_history.list_recent, limit)


@router.delete("")
async def clear_history() -> dict:
    await run_in_threadpool(_history.clear)
    return {"status": "cleared"}


@router.get("/export/txt")
async def export_txt() -> FileResponse:
    out_path = Path(tempfile.gettempdir()) / "sign_translator_history.txt"
    await run_in_threadpool(_history.export_txt, str(out_path))
    return FileResponse(out_path, filename="history.txt", media_type="text/plain")


@router.get("/export/pdf")
async def export_pdf() -> FileResponse:
    out_path = Path(tempfile.gettempdir()) / "sign_translator_history.pdf"
    await run_in_threadpool(_history.export_pdf, str(out_path))
    return FileResponse(out_path, filename="history.pdf", media_type="application/pdf")
