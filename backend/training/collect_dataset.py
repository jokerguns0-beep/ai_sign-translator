"""
collect_dataset.py: interactively record labeled gesture sequences into
dataset.jsonl, reusing the exact same CameraManager + LandmarkDetector +
GestureSequenceBuffer classes used in production, so the training data
matches production feature extraction exactly.

Usage:
    python -m training.collect_dataset --label привет --sessions 20
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow running as `python -m training.collect_dataset` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # noqa: E402

from services.camera_manager import CameraManager  # noqa: E402
from services.gesture_buffer import GestureSequenceBuffer  # noqa: E402
from services.landmark_detector import LandmarkDetector  # noqa: E402


def collect(label: str, sessions: int, out_path: str, window: int) -> None:
    detector = LandmarkDetector()
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with CameraManager() as camera, open(out_file, "a", encoding="utf-8") as f:
        frame_iter = camera.frames()
        for session in range(1, sessions + 1):
            input(f"\n[{session}/{sessions}] Приготовься показать жест '{label}'. Enter - начать запись...")
            buffer = GestureSequenceBuffer(min_window=window, max_window=window)

            print("Записываю... покажи жест сейчас")
            while len(buffer) < window:
                frame = next(frame_iter)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                landmarks = detector.detect(rgb)
                buffer.add(landmarks)
                cv2.imshow("Сбор датасета - q для выхода", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    detector.close()
                    cv2.destroyAllWindows()
                    return

            record = {
                "label": label,
                "language": "rsl",
                "recorded_at": time.time(),
                "frames": [f.model_dump(mode="json") for f in buffer.snapshot()],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"Записано {len(buffer)} кадров для '{label}'")

    detector.close()
    cv2.destroyAllWindows()
    print(f"\nГотово. Датасет сохранён в {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сбор датасета РЖЯ для обучения локальной модели")
    parser.add_argument("--label", required=True, help="Слово/жест, который записываем")
    parser.add_argument("--sessions", type=int, default=20, help="Сколько повторов записать")
    parser.add_argument("--out", default="training/dataset.jsonl", help="Путь к выходному файлу")
    parser.add_argument("--window", type=int, default=40, help="Кадров на один пример")
    args = parser.parse_args()

    collect(args.label, args.sessions, args.out, args.window)
