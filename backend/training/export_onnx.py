"""
export_onnx.py: export a trained gesture_model.pt checkpoint to ONNX for
fast, dependency-light inference in production (see
services/local_model_backend.py).

Usage:
    python -m training.export_onnx --checkpoint training/artifacts/gesture_model.pt
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from training.train_model import FEATURES_PER_FRAME, GestureLSTM


def export(checkpoint_path: str, out_path: str, sequence_length: int) -> None:
    label_map_path = Path(checkpoint_path).parent / "label_map.json"
    if not label_map_path.exists():
        raise SystemExit(f"label_map.json не найден рядом с {checkpoint_path} - запусти train_model.py заново")

    label_map = json.loads(label_map_path.read_text(encoding="utf-8"))
    num_classes = len(label_map)

    model = GestureLSTM(num_classes=num_classes)
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, sequence_length, FEATURES_PER_FRAME)

    torch.onnx.export(
        model,
        dummy_input,
        out_path,
        input_names=["landmarks_sequence"],
        output_names=["class_logits"],
        dynamic_axes={"landmarks_sequence": {1: "sequence_length"}},
        opset_version=17,
    )

    # Keep the label map next to the exported model too, so
    # LocalModelBackend can load both from the same directory.
    out_label_map = Path(out_path).parent / "label_map.json"
    out_label_map.write_text(json.dumps(label_map, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Экспортировано в {out_path}\nLabel map: {out_label_map}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Экспорт обученной модели жестов в ONNX")
    parser.add_argument("--checkpoint", default="training/artifacts/gesture_model.pt")
    parser.add_argument("--out", default="training/artifacts/gesture_model.onnx")
    parser.add_argument("--sequence-length", type=int, default=40)
    args = parser.parse_args()

    export(args.checkpoint, args.out, args.sequence_length)
