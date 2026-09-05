"""STARK//CODE: Doctor Strange gateway into a cinematic developer command system."""

import math
import random
import time
import tkinter as tk

from experience_state import ExperienceFlow, ExperienceStage
from sanctum_live import LiveSanctumApp
from sanctum_ui import GOLD, LIGHT_GOLD, AMBER, ORANGE, BURNT_ORANGE, DARK_BROWN, MUTED, BG_COLOR
from project_launcher import ProjectLauncher


class StarkCodeExperience(LiveSanctumApp):
    """Cinematic multi-stage Avengers-inspired command system."""

    def __init__(self) -> None:
        self._experience_ready = False
        super().__init__()
        self.flow = ExperienceFlow()
        self.launcher = ProjectLauncher()
        self._experience_ready = True
        
        self.env_particles = [(random.uniform(0, self.width), random.uniform(0, self.height), 
                               random.uniform(0.1, 0.5), random.choice((GOLD, ORANGE, BURNT_ORANGE))) 
                              for _ in range(60)]

    def _consume_sensor(self, now: float) -> None:
        previous = self.gesture.state
        super()._consume_sensor(now)
        if not self._experience_ready:
            return
        if previous != "SPELL COMPLETE" and self.gesture.state == "SPELL COMPLETE":
            self.flow.verify_spell(now)
        self.flow.advance(now, self.gesture.state == "CASTING")

    def _draw_spell(self, now: float) -> None:
        if not self._experience_ready:
            super()._draw_spell(now)
            return

        stage = self.flow.stage
        
        if stage not in (ExperienceStage.WORKSPACE_ACTIVE, ExperienceStage.ERROR_PROJECT, ExperienceStage.ERROR_VSCODE):
            super()._draw_spell(now)

        if stage is ExperienceStage.BOOT:
            self._draw_boot_overlay(now)
        elif stage is ExperienceStage.SPELL_VERIFIED:
            self._draw_verification(now)
        elif stage is ExperienceStage.GATEWAY_OPENING:
            self._draw_portal_transition(now)
        elif stage is ExperienceStage.SANCTUM_INITIALIZING:
            self._draw_sanctum_initializing(now)
        elif stage is ExperienceStage.PROJECT_INITIALIZING:
            self._draw_project_initializing(now)
            self._check_project_creation(now)
        elif stage is ExperienceStage.LAUNCHING_VSCODE:
            self._draw_launching_vscode(now)
            self._check_vscode_launch(now)
        elif stage is ExperienceStage.WORKSPACE_ACTIVE:
            self._draw_main_environment(now)
        elif stage is ExperienceStage.ERROR_PROJECT:
            self._draw_error_overlay("PROJECT CREATION FAILED")
        elif stage is ExperienceStage.ERROR_VSCODE:
            self._draw_error_overlay("DEVELOPER ENVIRONMENT UNAVAILABLE")

    def _draw_boot_overlay(self, now: float) -> None:
        progress = self.flow.progress(now, 0.75)
        cx, cy = self.spell_center
        radius = 50 + progress * 200
        
        for i in range(3):
            r = radius + i * 40
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=now * 120 + i*90,
                                   extent=120, style="arc", outline=BURNT_ORANGE, width=2)
                                   
        self.canvas.create_text(cx, cy - 20, text="SANCTUM GATEWAY", fill=LIGHT_GOLD, font=("Segoe UI", 24, "bold"))
        self.canvas.create_text(cx, cy + 20, text="INITIALIZING...", fill=AMBER, font=("Consolas", 12, "bold"))
        self.canvas.create_line(cx - 150, cy + 45, cx - 150 + 300 * progress, cy + 45, fill=GOLD, width=3)

    def _draw_verification(self, now: float) -> None:
        progress = self.flow.progress(now, 1.0)
        cx, cy = self.spell_center
        
        for i in range(5):
            r = self.spell_radius * (0.5 + progress * 0.5) + i * 20
            rot = (1.0 - progress) * 360 * (i+1)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=rot,
                                   extent=280, style="arc", outline=GOLD, width=max(1, 4-i))
                                   
        core_r = 10 + progress * 60
        self.canvas.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill="", outline="#ffffff", width=2)
        
        self.canvas.create_text(cx, cy - core_r - 40, text="SPELL VERIFIED", fill="#ffffff", font=("Segoe UI", 32, "bold"))

    def _draw_portal_transition(self, now: float) -> None:
        progress = self.flow.progress(now, 1.25)
        cx, cy = self.spell_center
        max_dim = max(self.width, self.height)
        portal_r = progress * progress * max_dim * 1.5
        
        burst_count = 36
        for i in range(burst_count):
            angle = math.tau * i / burst_count + now
            inner = portal_r * 0.8
            outer = portal_r * 1.2 + random.uniform(0, 100)
            self.canvas.create_line(cx + math.cos(angle)*inner, cy + math.sin(angle)*inner,
                                    cx + math.cos(angle)*outer, cy + math.sin(angle)*outer,
                                    fill=ORANGE, width=3)
                                    
        for i in range(4):
            r = portal_r - i * (max_dim * 0.1)
            if r > 0:
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=GOLD, width=6-i)
                
        for i in range(50):
            dist = max_dim * (1.0 - progress) + random.uniform(-100, 100)
            if dist > 0:
                angle = random.uniform(0, math.tau)
                x = cx + math.cos(angle) * dist
                y = cy + math.sin(angle) * dist
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="#ffffff", outline="")

        if progress > 0.8:
            flash_width = int((progress - 0.8) * 5 * max_dim)
            self.canvas.create_oval(cx - flash_width, cy - flash_width, cx + flash_width, cy + flash_width,
                                    outline="#ffffff", width=100)
            
        self.canvas.create_text(cx, cy, text="GATEWAY OPEN", fill="#fff8e1", font=("Segoe UI", 40, "bold"))

    def _draw_sanctum_initializing(self, now: float) -> None:
        cx, cy = self.spell_center
        self.canvas.create_text(cx, cy, text="SANCTUM INITIALIZING", fill=LIGHT_GOLD, font=("Segoe UI", 36, "bold"))
        
    def _draw_project_initializing(self, now: float) -> None:
        cx, cy = self.spell_center
        self.canvas.create_text(cx, cy - 60, text="SANCTUM CORE ........ ONLINE", fill=AMBER, font=("Consolas", 14))
        self.canvas.create_text(cx, cy - 30, text="PROJECT FORGE ....... INITIALIZING", fill=AMBER, font=("Consolas", 14))
        self.canvas.create_text(cx, cy, text="DEVELOPER LINK ...... ESTABLISHED", fill=AMBER, font=("Consolas", 14))
        
        if self.launcher.status == "CREATED":
            self.canvas.create_text(cx, cy + 60, text="PROJECT READY", fill=GOLD, font=("Segoe UI", 24, "bold"))
            
    def _check_project_creation(self, now: float) -> None:
        if self.launcher.status == "IDLE":
            self.launcher.create_project_async()
        elif self.launcher.status == "CREATED":
            if now - self.flow.stage_started > 1.5:
                self.flow.trigger_next(ExperienceStage.LAUNCHING_VSCODE, now)
        elif self.launcher.status == "ERROR_PROJECT":
            self.flow.trigger_next(ExperienceStage.ERROR_PROJECT, now)

    def _draw_launching_vscode(self, now: float) -> None:
        cx, cy = self.spell_center
        self.canvas.create_text(cx, cy, text="LAUNCHING WORKSPACE", fill=LIGHT_GOLD, font=("Segoe UI", 32, "bold"))
        self.canvas.create_text(cx, cy + 40, text="CONNECTING TO VS CODE...", fill=MUTED, font=("Consolas", 14))
        
    def _check_vscode_launch(self, now: float) -> None:
        if self.launcher.status == "CREATED":
            self.launcher.launch_vscode_async()
        elif self.launcher.status == "DONE":
            self.flow.trigger_next(ExperienceStage.WORKSPACE_ACTIVE, now)
        elif self.launcher.status == "ERROR_VSCODE":
            self.flow.trigger_next(ExperienceStage.ERROR_VSCODE, now)

    def _draw_error_overlay(self, message: str) -> None:
        cx, cy = self.spell_center
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#120502", outline="")
        self.canvas.create_text(cx, cy, text=message, fill="#ff3333", font=("Segoe UI", 36, "bold"))
        self.canvas.create_text(cx, cy + 50, text="SYSTEM HALTED", fill=MUTED, font=("Consolas", 16))

    def _draw_main_environment(self, now: float) -> None:
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill=BG_COLOR, outline="")
        self._draw_ambient_environment(now)
        self._draw_main_holographic_core(now)
        self._draw_main_floating_telemetry(now)
        
    def _draw_ambient_environment(self, now: float) -> None:
        for i, (x, y, speed, color) in enumerate(self.env_particles):
            nx = (x + math.sin(now * speed) * 0.5) % self.width
            ny = (y - speed * 2) % self.height
            self.env_particles[i] = (nx, ny, speed, color)
            self.canvas.create_oval(nx-1, ny-1, nx+1, ny+1, fill=color, outline="")
            
        cx, cy = self.width * 0.5, self.height * 0.5
        self.canvas.create_oval(cx - 400, cy - 400, cx + 400, cy + 400, outline="#0a0502", width=60)

    def _draw_main_holographic_core(self, now: float) -> None:
        cx, cy = self.width * 0.5, self.height * 0.5
        radius = min(self.width, self.height) * 0.28
        pulse = math.sin(now * 1.5) * 10
        
        for i in range(3):
            r_x = radius * 1.4 + i * 30
            r_y = radius * 0.6 + i * 15
            self.canvas.create_oval(cx - r_x, cy - r_y, cx + r_x, cy + r_y, outline=DARK_BROWN, width=2)
            
            node_angle = math.radians(now * (30 + i*10))
            nx = cx + math.cos(node_angle) * r_x
            ny = cy + math.sin(node_angle) * r_y
            self.canvas.create_oval(nx-4, ny-4, nx+4, ny+4, fill=AMBER, outline="")
            self.canvas.create_line(cx, cy, nx, ny, fill="#1a0d04")
            
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=BURNT_ORANGE, width=1)
        
        for i in range(6):
            angle = math.radians(now * 20 + i * 60)
            r = radius * 0.8
            x, y = cx + math.cos(angle) * r, cy + math.sin(angle) * r
            self.canvas.create_line(cx, cy, x, y, fill="#3a1805", width=2)
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=GOLD, outline="")
            
        core_r = radius * 0.4 + pulse
        self.canvas.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, outline=AMBER, width=2)
        
        self.canvas.create_text(cx, cy - 20, text="PROJECT FORGE", fill=LIGHT_GOLD, font=("Segoe UI", 26, "bold"))
        self.canvas.create_text(cx, cy + 20, text="DEVELOPMENT ENVIRONMENT ACTIVE", fill=AMBER, font=("Consolas", 10, "bold"))
        self.canvas.create_line(cx - 120, cy + 40, cx + 120, cy + 40, fill=ORANGE)
        
        modules = ["CODE MATRIX", "NEURAL BUILD", "SENTINEL NETWORK"]
        for i, mod in enumerate(modules):
            angle = math.radians(now * -10 + i * 120)
            mx = cx + math.cos(angle) * (radius * 1.1)
            my = cy + math.sin(angle) * (radius * 1.1)
            self.canvas.create_text(mx, my, text=mod, fill=MUTED, font=("Consolas", 9, "bold"))
            self.canvas.create_line(cx + math.cos(angle)*radius*0.8, cy + math.sin(angle)*radius*0.8, mx, my, fill=DARK_BROWN)

    def _draw_main_floating_telemetry(self, now: float) -> None:
        self.canvas.create_text(50, 50, anchor="w", text="STARK // CODE", fill=LIGHT_GOLD, font=("Segoe UI", 22, "bold"))
        self.canvas.create_text(52, 80, anchor="w", text="SANCTUM OS", fill=AMBER, font=("Consolas", 14, "bold"))
        self.canvas.create_text(52, 100, anchor="w", text="SYSTEM ONLINE", fill=MUTED, font=("Consolas", 10))
        self.canvas.create_line(50, 120, 200, 120, fill=DARK_BROWN, width=2)
        
        right_x = self.width - 50
        systems = [("SANCTUM CORE", "ONLINE"), ("HAND LINK", "ACTIVE"), ("SPELL ENGINE", "ARMED"), ("SYSTEM CORE", "STABLE")]
        for i, (name, status) in enumerate(systems):
            y = 150 + i * 60
            self.canvas.create_text(right_x, y, anchor="e", text=name, fill=MUTED, font=("Consolas", 10, "bold"))
            self.canvas.create_text(right_x, y + 20, anchor="e", text=status, fill=GOLD, font=("Consolas", 12, "bold"))
            self.canvas.create_line(right_x - 150, y + 35, right_x, y + 35, fill=BURNT_ORANGE if status == "ACTIVE" else DARK_BROWN)
            
        bottom_y = self.height - 60
        metrics = [
            ("NEURAL LINK", "SECURE"),
            ("HARDWARE BRIDGE", "SYNCED"),
            ("SYSTEM LOAD", f"{30 + int(math.sin(now)*10)}%"),
            ("SPELL VECTOR", "0.9942"),
            ("CORE STABILITY", "NOMINAL")
        ]
        
        spacing = (self.width - 100) / len(metrics)
        for i, (label, val) in enumerate(metrics):
            x = 50 + i * spacing
            self.canvas.create_text(x, bottom_y, anchor="w", text=label, fill=MUTED, font=("Consolas", 9, "bold"))
            self.canvas.create_text(x, bottom_y + 20, anchor="w", text=val, fill=AMBER, font=("Consolas", 11, "bold"))
            if i < len(metrics) - 1:
                self.canvas.create_line(x + spacing - 20, bottom_y, x + spacing - 20, bottom_y + 30, fill=DARK_BROWN)

    def _draw_live_diagnostics(self, now: float) -> None:
        if self._experience_ready and self.flow.stage in (ExperienceStage.WORKSPACE_ACTIVE, ExperienceStage.ERROR_PROJECT, ExperienceStage.ERROR_VSCODE):
            return
        super()._draw_live_diagnostics(now)


if __name__ == "__main__":
    StarkCodeExperience().run()
