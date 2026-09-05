import tkinter as tk
import math
import random
import time
import threading
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def get_model_path():
    return Path(__file__).resolve().parent / "models" / "hand_landmarker.task"

class SpidermanHandTracker:
    def __init__(self, model_path: Path):
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

    def detect_spiderman_pose(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.timestamp_ms += 1
        result = self.landmarker.detect_for_video(image, self.timestamp_ms)
        if not result.hand_landmarks:
            return False, None, 0.0, 0.0
            
        handedness = result.handedness[0][0].category_name
        # The webcam image is horizontally mirrored (cv2.flip(frame, 1)),
        # so a physical RIGHT hand appears as a "Left" hand to MediaPipe.
        if handedness != "Left":
            return False, None, 0.0, 0.0
            
        lm = result.hand_landmarks[0]
        height, width = frame.shape[:2]
        
        def dist3d(a, b):
            return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
            
        # Ultra-forgiving gesture detection based on a point system
        # We give a point for each finger that roughly matches the spider-man pose
        score = 0
        
        # Index extended
        if dist3d(lm[8], lm[5]) > dist3d(lm[6], lm[5]) * 0.9: score += 1
        # Middle folded
        if dist3d(lm[12], lm[9]) < dist3d(lm[10], lm[9]) * 1.35: score += 1
        # Ring folded
        if dist3d(lm[16], lm[13]) < dist3d(lm[14], lm[13]) * 1.35: score += 1
        # Pinky extended
        if dist3d(lm[20], lm[17]) > dist3d(lm[18], lm[17]) * 0.9: score += 1
        
        # Require only 3 out of 4 to pass. This allows messy live-demo gestures!
        is_spidey = (score >= 3)
        
        origin = (lm[8].x * width, lm[8].y * height)
        
        # Determine firing direction from Index PIP (6) to Index Tip (8)
        dir_x = lm[8].x - lm[6].x
        dir_y = lm[8].y - lm[6].y
        
        length = math.hypot(dir_x, dir_y)
        if length > 0:
            dir_x /= length
            dir_y /= length
        else:
            dir_x, dir_y = 0.0, -1.0
            
        return is_spidey, origin, dir_x, dir_y

class SpidermanSensor:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.trigger_event = False
        self.origin = None
        self.dir_x = 0.0
        self.dir_y = 0.0
        
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            
    def poll_trigger(self):
        with self._lock:
            trigger = self.trigger_event
            self.trigger_event = False
            return trigger, self.origin, self.dir_x, self.dir_y
            
    def _run(self):
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Failed to open webcam.")
            return
            
        tracker = None
        try:
            tracker = SpidermanHandTracker(self.model_path)
            spidey_start = None
            cooldown_until = 0.0
            
            while not self._stop.is_set():
                ok, frame = camera.read()
                if not ok:
                    time.sleep(0.05)
                    continue
                    
                frame = cv2.flip(frame, 1)
                is_spidey, origin, dir_x, dir_y = tracker.detect_spiderman_pose(frame)
                
                now = time.monotonic()
                    
                if is_spidey:
                    if spidey_start is None:
                        spidey_start = now
                    # Near-instant trigger: ~10ms stability
                    elif now - spidey_start > 0.01 and now > cooldown_until:
                        cooldown_until = now + 1.2
                        with self._lock:
                            self.trigger_event = True
                            self.origin = origin
                            self.dir_x = dir_x
                            self.dir_y = dir_y
                else:
                    spidey_start = None
        finally:
            if tracker:
                tracker.landmarker.close()
            camera.release()

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

class SpiderWebTestApp:
    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir
        self._execution_triggered = False

        self.root = tk.Tk()
        self.root.title("Spider-Web Overlay Test")
        
        self.bg_color = "#010203"
        self.root.configure(background=self.bg_color)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", self.bg_color)
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(self.root, highlightthickness=0, background=self.bg_color)
        self.canvas.pack(fill="both", expand=True)
        
        self.root.bind("<Escape>", self._close)
        self.root.bind("q", self._close)
        self.root.bind("Q", self._close)
        
        self.last_time = time.perf_counter()
        self.state = "IDLE"
        self.state_start = 0.0
        
        self.origin = (self.width // 2, self.height)
        self.target = (0, self.height // 2)
        self.particles = []
        self.web_radials = []
        self.web_spirals = []
        
        self.sensor = SpidermanSensor(get_model_path())
        self.sensor.start()
        
        self._animate()
        
    def _close(self, event=None):
        self.sensor.stop()
        self.root.destroy()
        
    def trigger_web(self, origin, dir_x, dir_y):
        if self.state in ("IDLE", "FADING"):
            self._execution_triggered = False
            self.state = "SHOOTING"
            self.state_start = time.perf_counter()
            self.origin = origin
            
            # Target the screen center instead of the screen edge
            self.target = (self.width / 2, self.height / 2)
            
            self._generate_web_geometry(self.target[0], self.target[1])
            self.particles.clear()
            
    def _generate_web_geometry(self, cx, cy):
        self.web_radials = []
        self.web_spirals = []
        num_radials = random.randint(18, 25)
        max_radius = random.uniform(500, 900)
        
        base_angle = 0 if cx == 0 else math.pi
        
        for _ in range(num_radials):
            angle = base_angle + random.uniform(-math.pi/1.8, math.pi/1.8)
            self.web_radials.append((angle, max_radius * random.uniform(0.7, 1.3)))
            
        self.web_radials.sort(key=lambda x: x[0])
        
        num_rings = random.randint(10, 16)
        for ring in range(1, num_rings + 1):
            r = (max_radius / num_rings) * ring
            points = []
            for angle, max_r in self.web_radials:
                if r < max_r:
                    r_jitter = r * random.uniform(0.85, 1.15)
                    points.append((cx + math.cos(angle)*r_jitter, cy + math.sin(angle)*r_jitter))
            if len(points) > 1:
                self.web_spirals.append(points)
                
    def _emit_impact_particles(self, cx, cy):
        for _ in range(60):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(300, 1200)
            life = random.uniform(0.3, 0.8)
            self.particles.append(Particle(
                x=cx, y=cy,
                vx=math.cos(angle)*speed, vy=math.sin(angle)*speed,
                life=life, max_life=life,
                size=random.uniform(2, 6),
                color=random.choice(["#ffffff", "#f0fdff", "#e0f7fa"])
            ))

    def _animate(self):
        now = time.perf_counter()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now
        
        triggered, origin, dir_x, dir_y = self.sensor.poll_trigger()
        if triggered:
            self.trigger_web(origin, dir_x, dir_y)
            
        self.canvas.delete("all")
        elapsed = now - self.state_start
        
        if self.state == "SHOOTING":
            # Fast THWIP (80ms)
            duration = 0.08
            progress = min(1.0, elapsed / duration)
            x = self.origin[0] + (self.target[0] - self.origin[0]) * progress
            y = self.origin[1] + (self.target[1] - self.origin[1]) * progress
            
            ctrl_x = self.origin[0] + (x - self.origin[0]) * 0.5
            ctrl_y = self.origin[1] + (y - self.origin[1]) * 0.5 + min(self.height*0.2, 200)
            self.canvas.create_line(self.origin[0], self.origin[1], ctrl_x, ctrl_y, x, y, 
                                    fill="#ffffff", width=3, smooth=True)
            
            for i in range(4):
                r = 4 + i*6
                self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#e0f7fa", width=2)
            
            if progress >= 1.0:
                self.state = "IMPACT"
                self.state_start = now
                self._emit_impact_particles(self.target[0], self.target[1])
                
        elif self.state == "IMPACT":
            duration = 0.1
            progress = min(1.0, elapsed / duration)
            flash_size = 80 + progress * 200
            self.canvas.create_oval(self.target[0]-flash_size, self.target[1]-flash_size,
                                    self.target[0]+flash_size, self.target[1]+flash_size,
                                    outline="#ffffff", width=15 - progress*15)
                                    
            if progress >= 1.0:
                self.state = "EXPANDING"
                self.state_start = now
                
        elif self.state in ("EXPANDING", "FADING"):
            is_fading = (self.state == "FADING")
            fade_elapsed = now - self.state_start if is_fading else 0
            
            if not is_fading and elapsed > 2.5:
                self.state = "FADING"
                self.state_start = now
                
            alpha = max(0.0, 1.0 - (fade_elapsed / 1.2)) if is_fading else 1.0
            
            if alpha <= 0:
                self.state = "IDLE"
                if not self._execution_triggered:
                    self._execution_triggered = True
                    threading.Thread(target=self._run_project, daemon=True).start()
            elif alpha > 0:
                self._draw_web(elapsed if not is_fading else 2.5, alpha)
                
        self._update_and_draw_particles(dt)
                                
        self.root.after(16, self._animate)
        
    def _run_project(self):
        """Execute the current project's main.py and show the result GUI."""
        if self.project_dir is None:
            # Try to find the most recently created STARK project
            base = Path.home() / "Desktop" / "STARK_PROJECTS"
            if base.exists():
                dirs = sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                self.project_dir = dirs[0] if dirs else None

        if self.project_dir is None:
            self._show_execution_result(False, "", "No STARK project found.\nRun the Doctor Strange spell first.", "UNKNOWN")
            return

        main_py = self.project_dir / "main.py"
        if not main_py.exists():
            self._show_execution_result(False, "", f"main.py not found in:\n{self.project_dir}", self.project_dir.name)
            return

        try:
            result = subprocess.run(
                [sys.executable, str(main_py)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self._show_execution_result(
                result.returncode == 0,
                result.stdout,
                result.stderr,
                self.project_dir.name,
            )
        except subprocess.TimeoutExpired:
            self._show_execution_result(False, "", "Execution timed out after 30 seconds.", self.project_dir.name)
        except Exception as e:
            self._show_execution_result(False, "", f"Failed to execute main.py:\n{e}", self.project_dir.name)

    def _show_execution_result(self, success, stdout, stderr, project_name):
        """Must be called from the background thread — schedules GUI on main thread."""
        try:
            from execution_gui import show_result
            # show_result with block=False runs in its own thread, safe to call here
            show_result(
                success=success,
                stdout=stdout,
                stderr=stderr,
                project_name=project_name,
                block=False,
            )
        except Exception as e:
            print(f"[execution_gui] Failed to show result: {e}")
        
    def _draw_web(self, elapsed, alpha):
        cx, cy = self.target
        expand_progress = min(1.0, elapsed / 0.25)
        
        line_width = max(1, int(3 * alpha))
        
        for angle, max_r in self.web_radials:
            r = max_r * expand_progress
            end_x = cx + math.cos(angle) * r
            end_y = cy + math.sin(angle) * r
            self.canvas.create_line(cx, cy, end_x, end_y, fill="#f0fdff", width=line_width)
            
        spiral_limit = int(len(self.web_spirals) * expand_progress)
        for ring_points in self.web_spirals[:spiral_limit]:
            for j in range(len(ring_points) - 1):
                p1 = ring_points[j]
                p2 = ring_points[j + 1]
                mid_x = (p1[0] + p2[0])/2
                mid_y = (p1[1] + p2[1])/2
                sag = 0.9 + random.uniform(-0.03, 0.03)
                ctrl_x = cx + (mid_x - cx) * sag
                ctrl_y = cy + (mid_y - cy) * sag
                
                self.canvas.create_line(p1[0], p1[1], ctrl_x, ctrl_y, p2[0], p2[1], 
                                        fill="#e0f7fa", width=max(1, line_width-1), smooth=True)

    def _update_and_draw_particles(self, dt):
        alive = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 1200 * dt
            p.vx *= 0.92
            p.vy *= 0.92
            
            p.life -= dt
            if p.life > 0:
                alpha = p.life / p.max_life
                size = p.size * alpha
                self.canvas.create_oval(p.x-size, p.y-size, p.x+size, p.y+size, fill=p.color, outline="")
                alive.append(p)
        self.particles = alive

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Spider-Man web overlay")
    parser.add_argument("--project-dir", type=str, default=None,
                        help="Path to the STARK project folder whose main.py will be executed")
    args = parser.parse_args()

    project_dir = Path(args.project_dir) if args.project_dir else None
    app = SpiderWebTestApp(project_dir=project_dir)
    app.root.mainloop()
