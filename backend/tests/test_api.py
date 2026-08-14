"""
Basic API + unit tests. Run with: pytest -v
"""
import base64

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from main import app
from services.frame_processor import FrameDecodeError, FrameProcessor
from services.gesture_buffer import GestureSequenceBuffer
from models.schemas import FrameLandmarks

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_history_empty_by_default():
    response = client.get("/api/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def _fake_data_url() -> str:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", frame)
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode("ascii")


def test_frame_processor_decodes_valid_frame():
    processor = FrameProcessor()
    image = processor.decode_base64_frame(_fake_data_url())
    assert image is not None
    assert image.shape[2] == 3


def test_frame_processor_raises_on_garbage():
    processor = FrameProcessor()
    with pytest.raises(FrameDecodeError):
        processor.decode_base64_frame("data:image/jpeg;base64,not-valid-base64!!")


def test_gesture_buffer_ready_threshold():
    buffer = GestureSequenceBuffer(min_window=3, max_window=5)
    assert not buffer.is_ready()
    for i in range(3):
        buffer.add(FrameLandmarks(timestamp_ms=i))
    assert buffer.is_ready()


def test_gesture_buffer_ring_eviction():
    buffer = GestureSequenceBuffer(min_window=2, max_window=3)
    for i in range(5):
        buffer.add(FrameLandmarks(timestamp_ms=i))
    assert len(buffer) == 3
    assert buffer.snapshot()[0].timestamp_ms == 2  # oldest 2 frames evicted
