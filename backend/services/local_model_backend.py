"""
LocalModelBackend: placeholder for a locally-trained gesture recognition
model (e.g. an LSTM/Transformer over landmark sequences, exported to
ONNX). Implements the same RecognitionBackend interface as GeminiClient,
so it's a drop-in replacement once trained - see training/ for how to
produce the model file this class expects.

Until a trained model exists, this raises NotImplementedError so it's
obvious if it accidentally gets wired in before it's ready.
"""
from __future__ import annotations

from pathlib import Path

from models.schemas import FrameLandmarks, GestureRecognitionResult, SignLanguage
from utils.logger import logger


class LocalModelBackend:
    """ONNX-Runtime-based local inference, once a model has been trained
    (see training/train_model.py + training/export_onnx.py).

    Expected input tensor shape: (1, sequence_length, num_features), where
    num_features flattens hand + pose landmark coordinates per frame -
    see training/README.md for the exact feature layout so the frontend/
    backend feature extraction and the training data stay consistent.
    """

    def __init__(self, model_path: str = "training/artifacts/gesture_model.onnx") -> None:
        self.model_path = Path(model_path)
        self._session = None
        if self.model_path.exists():
            self._load()
        else:
            logger.warning(
                f"No local model found at {self.model_path} - "
                "LocalModelBackend will raise NotImplementedError until one is trained "
                "(see backend/training/)."
            )

    def _load(self) -> None:
        import onnxruntime as ort  # local import: optional dependency, only needed here

        self._session = ort.InferenceSession(str(self.model_path))
        logger.info(f"Loaded local gesture model from {self.model_path}")

    async def recognize(
        self,
        sequence: list[FrameLandmarks],
        language: SignLanguage,
        reference_images: list[bytes] | None = None,
    ) -> GestureRecognitionResult:
        if self._session is None:
            raise NotImplementedError(
                "LocalModelBackend has no trained model loaded yet. "
                "Train one with backend/training/train_model.py and export it with "
                "backend/training/export_onnx.py, or continue using GeminiClient."
            )
        # TODO once a model exists:
        #   1. Convert `sequence` into the same feature tensor layout used
        #      during training (see training/README.md).
        #   2. Run self._session.run(...) - this is CPU-bound, so wrap in
        #      asyncio.to_thread() to avoid blocking the event loop.
        #   3. Map the output class index back to a label via the label
        #      map saved alongside the model, and build a
        #      GestureRecognitionResult.
        raise NotImplementedError
