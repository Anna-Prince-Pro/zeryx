"""MediaPipe Tasks hand tracking for the STARK//CODE spell prototype."""

from pathlib import Path
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
INDEX_FINGERTIP = 8


def ensure_model(model_path: Path) -> None:
    """Download the official MediaPipe task model the first time it is needed."""
    if not model_path.exists():
        model_path.parent.mkdir(parents=True, exist_ok=True)
        print("Downloading the MediaPipe hand-landmarker model (first run only)...")
        urlretrieve(MODEL_URL, model_path)
        print(f"Model saved to: {model_path}")


class HandTracker:
    """Find the index fingertip using MediaPipe 1.0.1's Tasks API."""

    def __init__(self, model_path: Path) -> None:
        ensure_model(model_path)
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.55,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.timestamp_ms = 0

    def index_tip(self, frame) -> tuple[int, int] | None:
        """Return the first hand's index-fingertip position in frame pixels."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.timestamp_ms += 1  # VIDEO mode timestamps must strictly increase.
        result = self.landmarker.detect_for_video(image, self.timestamp_ms)
        if not result.hand_landmarks:
            return None

        height, width = frame.shape[:2]
        fingertip = result.hand_landmarks[0][INDEX_FINGERTIP]
        return int(fingertip.x * width), int(fingertip.y * height)

    def close(self) -> None:
        """Release MediaPipe native resources."""
        self.landmarker.close()
