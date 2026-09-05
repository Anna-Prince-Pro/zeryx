"""Invisible webcam + MediaPipe input for the Sanctum UI.

This module intentionally never calls cv2.imshow or returns camera frames.
Only normalized index-fingertip coordinates leave the worker thread.
"""

from dataclasses import dataclass
from pathlib import Path
import threading
import time

import cv2

from hand_tracker import HandTracker


@dataclass(frozen=True)
class SensorSample:
    """A thread-safe snapshot of the camera's latest tracking result."""

    sequence: int
    point: tuple[float, float] | None
    camera_online: bool
    tracking_online: bool
    error: str | None = None


class InvisibleHandSensor:
    """Runs the proven HandTracker in the background without displaying video."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sample = SensorSample(0, None, False, False)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="sanctum-hand-sensor", daemon=True)
        self._thread.start()

    def latest(self) -> SensorSample:
        with self._lock:
            return self._sample

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _publish(self, point, camera_online: bool, tracking_online: bool, error: str | None = None) -> None:
        with self._lock:
            self._sample = SensorSample(
                self._sample.sequence + 1, point, camera_online, tracking_online, error
            )

    def _run(self) -> None:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            self._publish(None, False, False, "Unable to open webcam")
            return

        tracker = None
        try:
            tracker = HandTracker(self.model_path)  # Reuses the working MediaPipe 1.0.1 tracker.
            while not self._stop.is_set():
                ok, frame = camera.read()
                if not ok:
                    self._publish(None, True, True, "Unable to read webcam frame")
                    time.sleep(0.05)
                    continue

                # Mirror only for natural left/right input mapping; the frame is never rendered.
                frame = cv2.flip(frame, 1)
                pixel_tip = tracker.index_tip(frame)
                if pixel_tip is None:
                    self._publish(None, True, True)
                    continue

                height, width = frame.shape[:2]
                normalized = (pixel_tip[0] / width, pixel_tip[1] / height)
                self._publish(normalized, True, True)
        except Exception as error:  # Keep the UI available if the sensor fails.
            self._publish(None, True, False, str(error))
        finally:
            if tracker:
                tracker.close()
            camera.release()
