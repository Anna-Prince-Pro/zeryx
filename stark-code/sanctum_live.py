"""Live STARK//CODE Sanctum: invisible camera input over the cinematic HUD."""

from dataclasses import dataclass
from pathlib import Path
import math
import random
import time
import tkinter as tk

from gesture_engine import CircleGeometry, CircleGestureEngine
from invisible_sensor import InvisibleHandSensor
from sanctum_ui import GOLD, ORANGE, BURNT_ORANGE, AMBER, LIGHT_GOLD, SanctumApp, Particle


class LiveSanctumApp(SanctumApp):
    """Adds private webcam control and cinematic portal construction."""

    def __init__(self) -> None:
        self._live_ready = False
        super().__init__()
        model_path = Path(__file__).resolve().parent / "models" / "hand_landmarker.task"
        self.sensor = InvisibleHandSensor(model_path)
        self.gesture = CircleGestureEngine()
        self.last_sample_sequence = 0
        self.latest_sample = self.sensor.latest()
        self.current_tip: tuple[float, float] | None = None
        self.hand_particles: list[Particle] = []
        self.trail_points: list[tuple[float, float, float]] = []
        self.hand_last_draw = time.monotonic()
        self._live_ready = True

        self.root.bind("<Escape>", self._close)
        self.root.bind("q", self._close)
        self.root.bind("Q", self._close)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def run(self) -> None:
        self.sensor.start()
        super().run()

    def _close(self, _event=None) -> None:
        if getattr(self, "sensor", None):
            self.sensor.stop()
        self.root.destroy()

    def _animate(self) -> None:
        if getattr(self, "_live_ready", False):
            self._consume_sensor(time.monotonic())
        super()._animate()

    def _consume_sensor(self, now: float) -> None:
        sample = self.sensor.latest()
        self.latest_sample = sample
        if sample.sequence == self.last_sample_sequence:
            self.gesture.observe(None, now)
            return

        self.last_sample_sequence = sample.sequence
        if sample.point is None:
            self.current_tip = None
            self.gesture.observe(None, now)
            return

        x = max(0, min(self.width, sample.point[0] * self.width))
        y = max(0, min(self.height, sample.point[1] * self.height))
        point = (x, y)
        
        if self.current_tip:
            dist = math.dist(self.current_tip, point)
            if dist > 1.0:
                self._emit_energy_particles(point, self.current_tip, dist)
                
        self.current_tip = point
        self.trail_points.append((x, y, now))
        
        if self.gesture.observe(point, now):
            print("SPELL_COMPLETE")

    def _emit_energy_particles(self, current: tuple[float, float], previous: tuple[float, float], dist: float) -> None:
        count = int(min(15, max(1, dist * 0.2)))
        dx = current[0] - previous[0]
        dy = current[1] - previous[1]
        
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(5, 50)
            lifetime = random.uniform(0.3, 0.9)
            color = random.choice((GOLD, ORANGE, LIGHT_GOLD, "#ffffff"))
            self.hand_particles.append(Particle(
                current[0] + random.uniform(-5, 5),
                current[1] + random.uniform(-5, 5),
                (dx * 0.5) + math.cos(angle) * speed,
                (dy * 0.5) + math.sin(angle) * speed,
                lifetime, lifetime, random.uniform(1.0, 3.5), color
            ))

    def _draw_spell(self, now: float) -> None:
        progress = 0.0
        if getattr(self, "_live_ready", False) and self.gesture.geometry:
            progress = self.gesture.geometry.progress
        
        original_pulse = self.pulse
        self.pulse += progress * 1.5
        
        self.rotation_inner += progress * 15
        
        super()._draw_spell(now)
        
        self.pulse = original_pulse
        
        if getattr(self, "_live_ready", False):
            self._draw_hand_magic(now)

    def _draw_hand_magic(self, now: float) -> None:
        dt = min(now - self.hand_last_draw, 0.05)
        self.hand_last_draw = now
        
        self._update_and_draw_particles(dt)
        self._draw_fading_trail(now)
        
        if self.gesture.geometry:
            self._draw_progressive_spell(self.gesture.geometry, now)
            
        if now < self.gesture.complete_until and self.gesture.completed_geometry:
            self._draw_completion_burst(self.gesture.completed_geometry, now)
            
        if self.current_tip:
            self._draw_energy_fingertip(self.current_tip, now)

    def _update_and_draw_particles(self, dt: float) -> None:
        alive = []
        for p in self.hand_particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.9
            p.vy *= 0.9
            p.life -= dt
            if p.life > 0:
                alpha = p.life / p.max_life
                size = p.size * alpha
                self.canvas.create_oval(p.x - size, p.y - size, p.x + size, p.y + size, fill=p.color, outline="")
                if p.color in (LIGHT_GOLD, "#ffffff") and alpha > 0.5:
                    glow = size * 2.5
                    self.canvas.create_oval(p.x - glow, p.y - glow, p.x + glow, p.y + glow, fill="", outline=ORANGE, width=1)
                alive.append(p)
        self.hand_particles = alive[-600:]
        
    def _draw_fading_trail(self, now: float) -> None:
        self.trail_points = [pt for pt in self.trail_points if now - pt[2] < 1.2]
        if len(self.trail_points) < 2:
            return
            
        points_drawn = []
        for x, y, t in self.trail_points:
            age = now - t
            alpha = max(0.0, 1.0 - (age / 1.2))
            points_drawn.append((x, y, alpha))
            
        for i in range(len(points_drawn) - 1):
            x1, y1, a1 = points_drawn[i]
            x2, y2, a2 = points_drawn[i+1]
            w = 1 + a2 * 4
            color = GOLD if a2 > 0.6 else BURNT_ORANGE
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=w, capstyle=tk.ROUND, smooth=True)

    def _draw_energy_fingertip(self, point: tuple[float, float], now: float) -> None:
        x, y = point
        pulse = 4 + math.sin(now * 20) * 2
        self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#ffffff", outline="")
        self.canvas.create_oval(x - pulse, y - pulse, x + pulse, y + pulse, outline=LIGHT_GOLD, width=2)
        aura = pulse * 3
        self.canvas.create_oval(x - aura, y - aura, x + aura, y + aura, outline=BURNT_ORANGE, width=1)

    def _draw_progressive_spell(self, geometry: CircleGeometry, now: float) -> None:
        cx, cy = geometry.center
        radius = geometry.radius
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        rotation = (now * 60) % 360
        
        extent = max(10, geometry.progress * 360)
        
        self.canvas.create_arc(*box, start=-rotation, extent=extent, style="arc", outline=AMBER, width=4)
        
        stability = geometry.progress
        chaos = (1.0 - stability) * 15
        inner = radius * 0.85
        
        for i in range(int(3 + stability * 5)):
            r_offset = random.uniform(-chaos, chaos)
            r = inner + r_offset
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=rotation * 1.5 + i*45,
                                   extent=extent * 0.6, style="arc", outline=ORANGE, width=2)

    def _draw_completion_burst(self, geometry: CircleGeometry, now: float) -> None:
        elapsed = 1.9 - (self.gesture.complete_until - now)
        if elapsed < 0: return
        
        cx, cy = geometry.center
        
        if elapsed < 0.2:
            flash = (0.2 - elapsed) * 5
            r = geometry.radius * (1.0 + flash * 0.5)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#ffffff", width=int(10 * flash))
            
    def _draw_live_diagnostics(self, now: float) -> None:
        super()._draw_live_diagnostics(now)
        if not getattr(self, "_live_ready", False):
            return

        y_base = self.height - 120
        self.canvas.create_text(40, y_base, anchor="w", text="SENSOR ARRAY", fill=GOLD, font=("Consolas", 9, "bold"))
        self.canvas.create_line(40, y_base + 8, 120, y_base + 8, fill=BURNT_ORANGE)
        
        cam_state = "ONLINE" if self.latest_sample.camera_online else "STANDBY"
        trk_state = "ONLINE" if self.latest_sample.tracking_online else "STANDBY"
        spl_state = self.gesture.state
        
        self.canvas.create_text(40, y_base + 25, anchor="w", text=f"OPTICAL : {cam_state}", fill=AMBER, font=("Consolas", 8))
        self.canvas.create_text(40, y_base + 40, anchor="w", text=f"TRACKING: {trk_state}", fill=AMBER, font=("Consolas", 8))
        
        progress = ""
        if self.gesture.geometry:
            progress = f" [{int(self.gesture.geometry.progress * 100)}%]"
        self.canvas.create_text(40, y_base + 55, anchor="w", text=f"GESTURE : {spl_state}{progress}", fill=LIGHT_GOLD, font=("Consolas", 8, "bold"))


if __name__ == "__main__":
    LiveSanctumApp().run()
