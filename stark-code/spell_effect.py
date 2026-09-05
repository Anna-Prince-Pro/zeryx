"""Trajectory analysis and cinematic particle effects for STARK//CODE."""

from collections import deque
from dataclasses import dataclass
import math
import random
import time

import cv2
import numpy as np


@dataclass
class SpellGeometry:
    """The best circular interpretation of the fingertip's recent path."""

    center: tuple[int, int]
    radius: int
    progress: float
    complete: bool


@dataclass
class Particle:
    """One short-lived glowing ember in the spell trail."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: int


class SpellEffect:
    """Tracks the fingertip and renders an orange, portal-like spell effect."""

    def __init__(self) -> None:
        self.path = deque(maxlen=150)
        self.particles: list[Particle] = []
        self.last_point: tuple[int, int] | None = None
        self.last_time = time.monotonic()
        self.portal_until = 0.0
        self.cooldown_until = 0.0
        self.last_geometry: SpellGeometry | None = None

    def reset_path(self) -> None:
        self.path.clear()
        self.last_point = None
        self.last_geometry = None

    def add_tip(self, point: tuple[int, int] | None, now: float) -> bool:
        """Record a fingertip point and return True exactly once per spell."""
        if point is None:
            self.reset_path()
            return False
        if now < self.cooldown_until:
            return False
        if self.last_point is None or math.dist(self.last_point, point) >= 3:
            self.path.append(point)
            self._emit_trail(point)
            self.last_point = point

        geometry = self._analyse_path()
        self.last_geometry = geometry
        if geometry and geometry.complete:
            print("SPELL_COMPLETE")
            self.portal_until = now + 1.8
            self.cooldown_until = now + 2.6
            self.reset_path()
            return True
        return False

    def _emit_trail(self, point: tuple[int, int]) -> None:
        """Give the moving fingertip a shower of fading magical embers."""
        for _ in range(4):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(20, 95)
            lifetime = random.uniform(0.25, 0.7)
            self.particles.append(Particle(
                point[0], point[1], math.cos(angle) * speed, math.sin(angle) * speed,
                lifetime, lifetime, random.randint(2, 5),
            ))

    def _analyse_path(self) -> SpellGeometry | None:
        """Loosely recognize a sizeable hand-drawn circle instead of a perfect one."""
        points = list(self.path)
        if len(points) < 18:
            return None

        xs, ys = zip(*points)
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        diameter = min(width, height)
        if diameter < 70:
            return None

        travelled = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        center_x, center_y = sum(xs) / len(xs), sum(ys) / len(ys)
        radii = [math.dist(point, (center_x, center_y)) for point in points]
        radius = sum(radii) / len(radii)
        if radius < 35:
            return None

        # The amount the path turns tells us how much of a circle was cast.
        total_turn = 0.0
        for first, second, third in zip(points, points[1:], points[2:]):
            ax, ay = second[0] - first[0], second[1] - first[1]
            bx, by = third[0] - second[0], third[1] - second[1]
            total_turn += math.atan2(ax * by - ay * bx, ax * bx + ay * by)
        progress = min(1.0, abs(total_turn) / math.tau)

        # Completion is tolerant: a large loop, enough travel, a return near
        # its start, and a roughly steady radius are enough to cast the spell.
        variation = sum(abs(value - radius) for value in radii) / len(radii)
        closed = math.dist(points[0], points[-1]) < max(45, diameter * 0.42)
        complete = (
            travelled > max(330, math.pi * diameter * 0.75)
            and progress > 0.72
            and closed
            and variation / radius < 0.5
        )
        return SpellGeometry((int(center_x), int(center_y)), int(radius), progress, complete)

    def update_and_draw(self, frame, now: float) -> None:
        """Update particle lifetimes and layer spell art over the webcam frame."""
        dt = min(now - self.last_time, 0.05)
        self.last_time = now
        self._update_particles(dt)
        self._draw_trail(frame)
        if self.last_geometry:
            self._draw_casting_circle(frame, self.last_geometry, now)
        if now < self.portal_until:
            self._draw_portal(frame, now)

    def _update_particles(self, dt: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vx *= 0.94
            particle.vy *= 0.94
            particle.life -= dt
            if particle.life > 0:
                alive.append(particle)
        self.particles = alive[-420:]

    @staticmethod
    def _blend_glow(frame, glow, alpha: float = 0.78) -> None:
        """Blurred layers make bright lines bloom like a magical portal."""
        blurred = cv2.GaussianBlur(glow, (0, 0), 11)
        cv2.addWeighted(frame, 1.0, blurred, alpha, 0, frame)
        cv2.addWeighted(frame, 1.0, glow, 0.72, 0, frame)

    def _draw_trail(self, frame) -> None:
        glow = np.zeros_like(frame)
        for particle in self.particles:
            strength = particle.life / particle.max_life
            color = (0, int(90 + 130 * strength), int(180 + 75 * strength))
            cv2.circle(glow, (int(particle.x), int(particle.y)), particle.size, color, -1)
        for index, point in enumerate(self.path):
            strength = (index + 1) / max(1, len(self.path))
            cv2.circle(glow, point, max(2, int(3 + strength * 5)), (0, int(110 + strength * 90), 255), -1)
        self._blend_glow(frame, glow)

    def _draw_casting_circle(self, frame, geometry: SpellGeometry, now: float) -> None:
        """Draw rotating rings around the circle inferred from the real hand path."""
        center, radius = geometry.center, max(20, geometry.radius)
        glow = np.zeros_like(frame)
        rotation = (now * 95) % 360
        path_points = np.array(list(self.path), dtype=np.int32)
        if len(path_points) > 1:
            cv2.polylines(glow, [path_points], False, (0, 185, 255), 3, cv2.LINE_AA)
        cv2.ellipse(glow, center, (radius, radius), 0, rotation, rotation + 280, (0, 135, 255), 2, cv2.LINE_AA)
        cv2.ellipse(glow, center, (int(radius * 0.78), int(radius * 0.78)), 0, -rotation * 1.35, 190 - rotation * 1.35, (0, 215, 255), 2, cv2.LINE_AA)
        cv2.ellipse(glow, center, (int(radius * 1.15), int(radius * 1.15)), 0, rotation * 0.55, rotation * 0.55 + 130, (0, 80, 190), 2, cv2.LINE_AA)

        rune_count = 12
        active_runes = max(3, int(rune_count * max(geometry.progress, 0.25)))
        for index in range(active_runes):
            angle = math.radians(rotation + index * 360 / rune_count)
            x = int(center[0] + math.cos(angle) * radius * 0.93)
            y = int(center[1] + math.sin(angle) * radius * 0.93)
            cv2.circle(glow, (x, y), 4, (0, 230, 255), -1)
            cv2.line(glow, (x - 7, y), (x + 7, y), (0, 180, 255), 1, cv2.LINE_AA)

        self._blend_glow(frame, glow)
        cv2.putText(frame, f"CASTING  {int(geometry.progress * 100):02d}%", (22, 76), cv2.FONT_HERSHEY_DUPLEX, 0.75, (80, 220, 255), 2, cv2.LINE_AA)

    def _draw_portal(self, frame, now: float) -> None:
        """Play a short expanding portal burst after a completed circular spell."""
        elapsed = 1.8 - (self.portal_until - now)
        height, width = frame.shape[:2]
        center = (width // 2, height // 2)
        pulse = min(1.0, elapsed / 0.42)
        max_radius = int(min(width, height) * 0.38 * pulse)
        glow = np.zeros_like(frame)
        for ring in range(6):
            radius = max_radius - ring * 15
            if radius > 8:
                color = (0, max(60, 210 - ring * 22), 255)
                cv2.ellipse(glow, center, (radius, radius), 0, ring * 30 + now * 70, ring * 30 + now * 70 + 210, color, 3, cv2.LINE_AA)
        for _ in range(22):
            angle = random.uniform(0, math.tau)
            distance = random.uniform(20, max(30, max_radius))
            point = (int(center[0] + math.cos(angle) * distance), int(center[1] + math.sin(angle) * distance))
            cv2.circle(glow, point, random.randint(2, 5), (0, 210, 255), -1)
        self._blend_glow(frame, glow, 0.95)
        cv2.putText(frame, "SPELL COMPLETE", (max(25, center[0] - 180), center[1]), cv2.FONT_HERSHEY_DUPLEX, 1.2, (110, 240, 255), 3, cv2.LINE_AA)
