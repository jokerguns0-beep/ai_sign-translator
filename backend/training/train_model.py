"""
train_model.py: reference training script - an LSTM classifier over
flattened per-frame landmark features, trained on dataset.jsonl produced
by collect_dataset.py.

This is a starting point, not a tuned production pipeline: expect to
adjust hidden size, number of layers, learning rate, and augmentation
once you have real data and can see validation curves.

Usage:
    python -m training.train_model --dataset training/dataset.jsonl --epochs 50
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, random_split

MAX_HANDS = 2
LANDMARKS_PER_HAND = 21
COORDS_PER_LANDMARK = 3  # x, y, z
POSE_LANDMARKS = 14  # upper-body subset kept by LandmarkDetector
POSE_COORDS = 3

FEATURES_PER_FRAME = (
    MAX_HANDS * LANDMARKS_PER_HAND * COORDS_PER_LANDMARK + POSE_LANDMARKS * POSE_COORDS
)


def frame_to_vector(frame: dict) -> np.ndarray:
    """Flatten one FrameLandmarks dict into a fixed-size feature vector.
    Missing hands/pose are zero-padded so every frame has the same shape
    regardless of how many hands were visible.
    """
    vec = np.zeros(FEATURES_PER_FRAME, dtype=np.float32)
    offset = 0

    hands = frame.get("hands", [])[:MAX_HANDS]
    for hand in hands:
        for point in hand["landmarks"]:
            vec[offset : offset + 3] = [point["x"], point["y"], point["z"]]
            offset += 3
        # skip ahead even if this hand had fewer than 21 points (shouldn't happen)
    offset = MAX_HANDS * LANDMARKS_PER_HAND * COORDS_PER_LANDMARK

    pose = frame.get("pose") or []
    for point in pose[:POSE_LANDMARKS]:
        vec[offset : offset + 3] = [point["x"], point["y"], point["z"]]
        offset += 3

    return vec


class GestureDataset(Dataset):
    def __init__(self, records: list[dict], label_to_idx: dict[str, int]) -> None:
        self.records = records
        self.label_to_idx = label_to_idx

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int):
        record = self.records[idx]
        frames = [frame_to_vector(f) for f in record["frames"]]
        x = torch.tensor(np.stack(frames), dtype=torch.float32)
        y = self.label_to_idx[record["label"]]
        return x, y


class GestureLSTM(nn.Module):
    def __init__(self, num_classes: int, hidden_size: int = 128, num_layers: int = 2) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=FEATURES_PER_FRAME,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.3 if num_layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, (h_n, _) = self.lstm(x)
        return self.classifier(h_n[-1])


def load_dataset(path: str) -> tuple[list[dict], dict[str, int]]:
    records = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = sorted({r["label"] for r in records})
    label_to_idx = {label: i for i, label in enumerate(labels)}
    return records, label_to_idx


def train(dataset_path: str, epochs: int, batch_size: int, lr: float, out_dir: str) -> None:
    records, label_to_idx = load_dataset(dataset_path)
    if len(records) < 10:
        raise SystemExit(
            f"Датасет слишком мал ({len(records)} записей) - собери больше через collect_dataset.py"
        )

    dataset = GestureDataset(records, label_to_idx)
    val_size = max(1, int(0.2 * len(dataset)))
    train_ds, val_ds = random_split(dataset, [len(dataset) - val_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = GestureLSTM(num_classes=len(label_to_idx)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                preds = model(x).argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        val_acc = correct / max(1, total)

        print(f"Epoch {epoch}/{epochs} - loss={total_loss / len(train_loader):.4f} - val_acc={val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), out_path / "gesture_model.pt")
            (out_path / "label_map.json").write_text(
                json.dumps({v: k for k, v in label_to_idx.items()}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    print(f"\nЛучшая точность на валидации: {best_val_acc:.3f}. Модель сохранена в {out_path}/gesture_model.pt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Обучение LSTM-классификатора жестов РЖЯ")
    parser.add_argument("--dataset", default="training/dataset.jsonl")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out", default="training/artifacts")
    args = parser.parse_args()

    train(args.dataset, args.epochs, args.batch_size, args.lr, args.out)
