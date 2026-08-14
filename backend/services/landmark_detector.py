"""
LandmarkDetector: wraps MediaPipe Hands + Pose to extract every available
landmark (hands, fingers, palm, wrists, elbows, shoulders) from a single
RGB frame and returns a strongly-typed FrameLandmarks object.
"""
from __future__ import annotations

import time

import mediapipe as mp
import numpy as np

from config.settings import get_config
from models.schemas import FrameLandmarks, HandLandmarks, Point3D
from utils.logger import logger

_config = get_config()


class LandmarkDetector:
    """Thin, resource-owning wrapper around MediaPipe's Hands and Pose
    solutions. One instance should be reused across frames (creating a new
    MediaPipe graph per frame is expensive) and closed on shutdown.
    """

    # Pose landmark indices we actually care about for sign language
    # (torso + arms only - legs are irrelevant and dropped to save bandwidth).
    _POSE_UPPER_BODY_INDICES = list(range(11, 25))  # shoulders -> hips inclusive

    def __init__(self) -> None:
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=_config.mp_hands_max_num_hands,
            min_detection_confidence=_config.mp_hands_min_detection_confidence,
            min_tracking_confidence=_config.mp_hands_min_tracking_confidence,
        )
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            min_detection_confidence=_config.mp_pose_min_detection_confidence,
            model_complexity=1,
        )
        logger.info("LandmarkDetector initialized (MediaPipe Hands + Pose)")

    def detect(self, rgb_image: np.ndarray) -> FrameLandmarks:
        """Run both solutions on a single RGB frame and return combined
        landmark data. Frames with no detected hands still return pose
        data (useful for framing/quality feedback in the UI).
        """
        hands_result = self._hands.process(rgb_image)
        pose_result = self._pose.process(rgb_image)

        hands: list[HandLandmarks] = []
        if hands_result.multi_hand_landmarks and hands_result.multi_handedness:
            for lm_set, handedness in zip(
                hands_result.multi_hand_landmarks, hands_result.multi_handedness
            ):
                hands.append(
                    HandLandmarks(
                        handedness=handedness.classification[0].label,  # type: ignore[arg-type]
                        landmarks=[Point3D(x=p.x, y=p.y, z=p.z) for p in lm_set.landmark],
                    )
                )

        pose: list[Point3D] | None = None
        if pose_result.pose_landmarks:
            pose = [
                Point3D(x=p.x, y=p.y, z=p.z, visibility=p.visibility)
                for i, p in enumerate(pose_result.pose_landmarks.landmark)
                if i in self._POSE_UPPER_BODY_INDICES
            ]

        return FrameLandmarks(timestamp_ms=int(time.time() * 1000), hands=hands, pose=pose)

    def close(self) -> None:
        self._hands.close()
        self._pose.close()
        logger.info("LandmarkDetector released MediaPipe resources")
