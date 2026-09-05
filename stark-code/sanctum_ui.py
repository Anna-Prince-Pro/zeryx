"""Fullscreen STARK//CODE Sanctum interface.

This visual-only module intentionally has no camera, hand tracking, or
automation integration. A future controller can call ``set_tracking_input``
to feed normalized fingertip coordinates into the HUD.
"""

from dataclasses import dataclass
import math
import random
import time
import tkinter as tk


ORANGE = "#ff6f00"
BURNT_ORANGE = "#d64e00"
GOLD = "#ffd54f"
LIGHT_GOLD = "#ffe082"
AMBER = "#ffaa00"
DARK_BROWN = "#2d1303"
BG_COLOR = "#030201"
TEXT = "#fff8e1"
MUTED = "#8a6343"


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: str


@dataclass
class OrbitalSpark:
    angle: float
    distance: float
    speed: float
    size: float
    phase: float
    layer: int


class SanctumApp:
    """Cinematic Avengers-inspired developer workstation rendered with Tk Canvas."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("STARK//CODE — THE SANCTUM")
        self.root.configure(background=BG_COLOR)
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("q", lambda _event: self.root.destroy())
        self.root.bind("Q", lambda _event: self.root.destroy())
        self.root.bind("<F11>", self._toggle_fullscreen)

        self.canvas = tk.Canvas(self.root, highlightthickness=0, background=BG_COLOR)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        self.start_time = time.monotonic()
        self.last_time = self.start_time
        
        self.rotation_inner = 0.0
        self.rotation_mid = 0.0
        self.rotation_outer = 0.0
        self.pulse = 0.0
        
        self.tracking_input: tuple[float, float] | None = None
        
        self.orbital_sparks = [
            OrbitalSpark(
                angle=random.uniform(0, math.tau),
                distance=random.uniform(0.3, 1.5),
                speed=random.uniform(-0.8, 0.8),
                size=random.uniform(1.0, 3.5),
                phase=random.uniform(0, math.tau),
                layer=random.randint(0, 2)
            )
            for _ in range(250)
        ]
        
        self._animate()

    def run(self) -> None:
        self.root.mainloop()

    def set_tracking_input(self, x: float, y: float, active: bool = True) -> None:
        self.tracking_input = (x, y) if active else None

    def _toggle_fullscreen(self, _event=None) -> None:
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def _on_resize(self, event) -> None:
        if event.width < 100 or event.height < 100:
            return
        self.width, self.height = event.width, event.height
        
    @property
    def spell_center(self) -> tuple[float, float]:
        return self.width * 0.5, self.height * 0.5

    @property
    def spell_radius(self) -> float:
        return min(self.width, self.height) * 0.35

    def _animate(self) -> None:
        now = time.monotonic()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now
        
        self.rotation_inner = (self.rotation_inner + dt * 45) % 360
        self.rotation_mid = (self.rotation_mid - dt * 25) % 360
        self.rotation_outer = (self.rotation_outer + dt * 12) % 360
        self.pulse = (math.sin((now - self.start_time) * 1.5) + 1) / 2
        
        self.canvas.delete("all")
        self._draw_background(now)
        self._draw_spell(now)
        self._draw_floating_telemetry(now)
        self._draw_live_diagnostics(now)
        
        self.root.after(16, self._animate)
        
    def _draw_background(self, now: float) -> None:
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill=BG_COLOR, outline="")
        cx, cy = self.spell_center
        max_dim = max(self.width, self.height)
        glow_radius = max_dim * 0.6 + self.pulse * 20
        self.canvas.create_oval(cx - glow_radius, cy - glow_radius, cx + glow_radius, cy + glow_radius, 
                                outline="#0a0502", width=100)
        
        for i in range(15):
            mx = (cx + math.sin(now * 0.1 + i) * self.width * 0.4) % self.width
            my = (cy + math.cos(now * 0.15 + i) * self.height * 0.4) % self.height
            self.canvas.create_oval(mx-1, my-1, mx+1, my+1, fill="#1a0d04", outline="")
            
    def _draw_spell(self, now: float) -> None:
        cx, cy = self.spell_center
        radius = self.spell_radius
        
        outer_r = radius * 1.3 + math.sin(now * 2) * 5
        self.canvas.create_oval(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                                outline="#1a0701", width=15)
                                
        mid_r = radius * 1.05
        self.canvas.create_arc(cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r,
                               start=self.rotation_mid, extent=120, style="arc", outline=DARK_BROWN, width=8)
        self.canvas.create_arc(cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r,
                               start=self.rotation_mid + 180, extent=120, style="arc", outline=DARK_BROWN, width=8)
                               
        inner_r = radius * 0.8
        pulse_inner = inner_r + self.pulse * 8
        self.canvas.create_oval(cx - pulse_inner, cy - pulse_inner, cx + pulse_inner, cy + pulse_inner,
                                outline=BURNT_ORANGE, width=2)
        
        for i in range(3):
            r = radius * (0.85 + i * 0.05)
            w = 4 - i
            rot = self.rotation_inner * (1 + i*0.2)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                   start=rot, extent=45 + i*20, style="arc", outline=AMBER, width=w)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                   start=rot + 180, extent=45 + i*20, style="arc", outline=AMBER, width=w)
                                   
        self._draw_runes(cx, cy, radius, now)
        self._draw_orbital_sparks(cx, cy, radius, now)
        self._draw_central_identity(cx, cy, radius)
        
    def _draw_runes(self, cx: float, cy: float, radius: float, now: float) -> None:
        for index in range(12):
            angle = math.radians(self.rotation_inner * 0.8 + index * 360 / 12)
            r = radius * 0.72
            x, y = cx + math.cos(angle) * r, cy + math.sin(angle) * r
            tangent = (-math.sin(angle), math.cos(angle))
            length = 15 if index % 2 else 25
            color = GOLD if index % 4 == 0 else ORANGE
            self.canvas.create_line(x - tangent[0] * length, y - tangent[1] * length,
                                    x + tangent[0] * length, y + tangent[1] * length,
                                    fill=color, width=2)
            self.canvas.create_line(x, y, x - math.cos(angle)*10, y - math.sin(angle)*10, fill=color, width=1)
            
    def _draw_orbital_sparks(self, cx: float, cy: float, radius: float, now: float) -> None:
        for spark in self.orbital_sparks:
            speed_mult = 1.0 + spark.layer * 0.5
            angle = spark.angle + now * spark.speed * speed_mult
            
            wobble_x = math.cos(now * 1.5 + spark.phase) * radius * 0.1 * spark.layer
            wobble_y = math.sin(now * 2.1 + spark.phase) * radius * 0.1 * spark.layer
            
            distance = radius * spark.distance
            
            tilt_y = 0.95
            
            x = cx + math.cos(angle) * distance + wobble_x
            y = cy + math.sin(angle) * distance * tilt_y + wobble_y
            
            flicker = 0.6 + 0.4 * math.sin(now * (8 + spark.layer) + spark.phase)
            size = max(0.5, spark.size * flicker)
            
            if spark.layer == 0:
                color = "#8a3a00"
            elif spark.layer == 1:
                color = ORANGE
            else:
                color = GOLD
                
            self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")
            
    def _draw_central_identity(self, cx: float, cy: float, radius: float) -> None:
        self.canvas.create_text(cx, cy - 25, text="STARK // CODE", fill=LIGHT_GOLD,
                                font=("Segoe UI", 22, "bold", "italic"))
        self.canvas.create_text(cx, cy + 10, text="SANCTUM OS CORE", fill=AMBER,
                                font=("Consolas", 10, "bold", "italic"))
        self.canvas.create_line(cx - 70, cy + 25, cx + 70, cy + 25, fill=DARK_BROWN)
        
    def _draw_floating_telemetry(self, now: float) -> None:
        self.canvas.create_text(40, 40, anchor="w", text="STARK // CODE", fill=GOLD, font=("Segoe UI", 16, "bold"))
        self.canvas.create_text(42, 62, anchor="w", text="AVENGERS DEV PROTOCOL", fill=MUTED, font=("Consolas", 8, "bold"))
        
        self.canvas.create_text(self.width - 40, 40, anchor="e", text="SANCTUM OS / ONLINE", fill=AMBER, font=("Consolas", 12, "bold"))
        self.canvas.create_text(self.width - 40, 62, anchor="e", text="CORE LINK STABLE", fill=MUTED, font=("Consolas", 8))
        
        y_base = self.height - 40
        self.canvas.create_text(self.width - 40, y_base, anchor="e", text=f"SYS.LOAD {42 + int(math.sin(now)*5)}%", fill=ORANGE, font=("Consolas", 10))
        self.canvas.create_text(self.width - 150, y_base, anchor="e", text="NEURAL BRIDGE ACTIVE", fill=MUTED, font=("Consolas", 10))
        
        for i in range(5):
            y = self.height * 0.3 + i * 80
            self.canvas.create_line(30, y, 40, y, fill=DARK_BROWN, width=2)
            if i == 2:
                self.canvas.create_text(50, y, anchor="w", text="SPELL MATRIX // ALIGNED", fill=AMBER, font=("Consolas", 9, "bold"))
                
    def _draw_live_diagnostics(self, now: float) -> None:
        pass

if __name__ == "__main__":
    SanctumApp().run()
