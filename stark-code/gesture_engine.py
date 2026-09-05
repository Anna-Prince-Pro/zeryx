"""Canvas-coordinate trajectory and tolerant circular-spell recognition."""

from collections import deque
from dataclasses import dataclass
import math
import time


@dataclass(frozen=True)
class CircleGeometry:
    center: tuple[float, float]
    radius: float
    progress: float
    complete: bool


class CircleGestureEngine:
    """Recognizes a meaningful, imperfect loop in either drawing direction."""

    def __init__(self) -> None:
        self.path = deque(maxlen=150)
        self.last_point: tuple[float, float] | None = None
        self.last_seen = 0.0
        self.geometry: CircleGeometry | None = None
        self.completed_geometry: CircleGeometry | None = None
        self.complete_until = 0.0
        self.cooldown_until = 0.0
        self.state = "WAITING"

    def observe(self, point: tuple[float, float] | None, now: float | None = None) -> bool:
        """Add one UI point; return True only on the frame a spell completes."""
        now = time.monotonic() if now is None else now
        self._advance_state(now)
        if point is None:
            if now - self.last_seen > 0.24 and now >= self.cooldown_until:
                self._clear_path()
            return False

        self.last_seen = now
        if now < self.cooldown_until:
            return False
        if self.last_point is None or math.dist(self.last_point, point) >= 4:
            self.path.append(point)
            self.last_point = point

        self.geometry = self._analyse_path()
        if self.geometry and self.geometry.complete:
            self.completed_geometry = self.geometry
            self.complete_until = now + 1.9
            self.cooldown_until = now + 2.7
            self.state = "SPELL COMPLETE"
            self._clear_path()
            return True

        self.state = "CASTING" if len(self.path) > 2 else "WAITING"
        return False

    def _advance_state(self, now: float) -> None:
        if self.state == "SPELL COMPLETE" and now >= self.complete_until:
            self.state = "COOLDOWN" if now < self.cooldown_until else "WAITING"
        elif self.state == "COOLDOWN" and now >= self.cooldown_until:
            self.state = "WAITING"

    def _clear_path(self) -> None:
        self.path.clear()
        self.last_point = None
        self.geometry = None

    def _analyse_path(self) -> CircleGeometry | None:
        points = list(self.path)
        if len(points) < 20:
            return None
        xs, ys = zip(*points)
        diameter = min(max(xs) - min(xs), max(ys) - min(ys))
        if diameter < 100:  # Reject tiny wrist/finger jitter.
            return None

        traveled = sum(math.dist(first, second) for first, second in zip(points, points[1:]))
        center = (sum(xs) / len(xs), sum(ys) / len(ys))
        radii = [math.dist(point, center) for point in points]
        radius = sum(radii) / len(radii)
        if radius < 48:
            return None

        total_turn = 0.0
        for first, second, third in zip(points, points[1:], points[2:]):
            ax, ay = second[0] - first[0], second[1] - first[1]
            bx, by = third[0] - second[0], third[1] - second[1]
            total_turn += math.atan2(ax * by - ay * bx, ax * bx + ay * by)
        progress = min(1.0, abs(total_turn) / math.tau)  # abs accepts either rotation direction.

        variation = sum(abs(value - radius) for value in radii) / len(radii)
        closed = math.dist(points[0], points[-1]) <= max(46, diameter * 0.42)
        complete = (
            traveled >= max(420, math.pi * diameter * 0.74)
            and progress >= 0.72
            and closed
            and variation / radius <= 0.5
        )
        return CircleGeometry(center, radius, progress, complete)
