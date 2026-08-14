"""
HistoryManager: persists recognized phrases to SQLite and supports
exporting the history as TXT or PDF, and clearing it.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from config.settings import get_config
from models.schemas import HistoryEntry, SignLanguage
from utils.logger import logger

_config = get_config()


class HistoryManager:
    """Simple synchronous SQLite-backed store. FastAPI routes should call
    these methods via `run_in_threadpool` / `asyncio.to_thread` since
    sqlite3 is blocking.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or _config.history_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add(self, text: str, language: SignLanguage, confidence: float) -> HistoryEntry:
        entry = HistoryEntry(id=str(uuid.uuid4()), text=text, language=language, confidence=confidence)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO history (id, text, language, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
                (entry.id, entry.text, entry.language.value, entry.confidence, entry.created_at.isoformat()),
            )
        return entry

    def list_recent(self, limit: int = 50) -> list[HistoryEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, text, language, confidence, created_at FROM history "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            HistoryEntry(id=r[0], text=r[1], language=r[2], confidence=r[3], created_at=r[4])
            for r in rows
        ]

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM history")
        logger.info("History cleared")

    def export_txt(self, out_path: str) -> str:
        entries = self.list_recent(limit=1000)
        lines = [f"[{e.created_at.isoformat()}] ({e.language.value}) {e.text}" for e in reversed(entries)]
        Path(out_path).write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def export_pdf(self, out_path: str) -> str:
        entries = self.list_recent(limit=1000)
        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "AI Sign Language Translator - История")
        y -= 30
        c.setFont("Helvetica", 10)
        for e in reversed(entries):
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            line = f"[{e.created_at.strftime('%Y-%m-%d %H:%M:%S')}] ({e.language.value}) {e.text}"
            c.drawString(50, y, line[:110])
            y -= 16
        c.save()
        return out_path
