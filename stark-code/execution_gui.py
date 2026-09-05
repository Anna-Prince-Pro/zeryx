"""
STARK // CODE — Execution Core GUI
===================================
Standalone module for displaying the result of a Python program execution.

Can be launched directly for testing:
    python execution_gui.py --demo success
    python execution_gui.py --demo error

Or imported and used programmatically:
    from execution_gui import show_result
    show_result(success=True, stdout="Hello, Avenger.", stderr="")
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import math
import sys
import argparse

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DEEP      = "#0a0603"   # near-black with warm brown tint
BG_PANEL     = "#110d07"   # slightly lighter panel background
AMBER        = "#c8860a"   # core amber accent
AMBER_BRIGHT = "#f0a830"   # bright amber for titles / success
AMBER_DIM    = "#6b4a0a"   # dim amber for decorative lines
SUCCESS_CLR  = "#30d080"   # green-tinted success
ERROR_CLR    = "#e04040"   # red error
TEXT_PRIMARY = "#f0e8d8"   # warm white body text
TEXT_DIM     = "#7a6a50"   # muted label text
TERMINAL_BG  = "#070503"   # deepest black for terminal area
TERMINAL_FG  = "#d4b060"   # amber-tinted terminal text


class _ParticleField:
    """Lightweight floating particle animation drawn on a Canvas."""

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        import random
        self._rng = random
        self._particles = [self._spawn() for _ in range(40)]
        self._running = False

    def _spawn(self):
        x = self._rng.uniform(0, self.width)
        y = self._rng.uniform(0, self.height)
        vy = self._rng.uniform(-0.3, -0.08)
        size = self._rng.uniform(1.0, 2.5)
        alpha = self._rng.uniform(0.2, 0.7)
        return {"x": x, "y": y, "vy": vy, "size": size, "alpha": alpha,
                "color": self._amber_shade(alpha)}

    def _amber_shade(self, alpha: float) -> str:
        r = int(80 + 120 * alpha)
        g = int(50 + 80 * alpha)
        b = int(0)
        return f"#{r:02x}{g:02x}{b:02x}"

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        self.canvas.delete("particle")
        for p in self._particles:
            p["y"] += p["vy"]
            if p["y"] < -5:
                p["y"] = self.height + 5
                p["x"] = self._rng.uniform(0, self.width)
            s = p["size"]
            self.canvas.create_oval(
                p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s,
                fill=p["color"], outline="", tags="particle"
            )
        self.canvas.after(50, self._tick)


class ExecutionResultGUI:
    """
    Main STARK // CODE execution result window.

    Parameters
    ----------
    success : bool
        Whether the execution succeeded.
    stdout : str
        Captured standard output of the executed program.
    stderr : str
        Captured standard error / traceback text.
    project_name : str
        Display name of the project that was executed.
    on_close : callable | None
        Optional callback invoked when the window is dismissed.
    """

    def __init__(
        self,
        success: bool = True,
        stdout: str = "",
        stderr: str = "",
        project_name: str = "PROJECT ALPHA",
        on_close=None,
    ):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.project_name = project_name
        self.on_close = on_close

        self.root = tk.Tk()
        self.root.title("STARK // CODE — Execution Core")
        self.root.configure(bg=BG_DEEP)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        self.W = self.root.winfo_screenwidth()
        self.H = self.root.winfo_screenheight()

        self._build_ui()
        self._particles = _ParticleField(self._bg_canvas, self.W, self.H)
        self._particles.start()
        self._animate_scanline()

        self.root.bind("<Escape>", self._close)
        self.root.bind("<Return>", self._close)
        self.root.bind("<space>", self._close)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Background canvas (particles + scanlines)
        self._bg_canvas = tk.Canvas(
            self.root, width=self.W, height=self.H,
            bg=BG_DEEP, highlightthickness=0
        )
        self._bg_canvas.place(x=0, y=0)

        # Central panel (fixed size, centred)
        PW, PH = min(1100, self.W - 80), min(700, self.H - 80)
        px = (self.W - PW) // 2
        py = (self.H - PH) // 2

        panel = tk.Frame(self.root, bg=BG_PANEL, bd=0)
        panel.place(x=px, y=py, width=PW, height=PH)

        # Amber border lines (top & bottom)
        tk.Frame(panel, bg=AMBER, height=2).pack(fill="x", side="top")
        tk.Frame(panel, bg=AMBER, height=2).pack(fill="x", side="bottom")

        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(panel, bg=BG_PANEL, pady=18)
        header.pack(fill="x")

        tk.Label(
            header, text="STARK  //  CODE",
            font=("Consolas", 22, "bold"),
            fg=AMBER_BRIGHT, bg=BG_PANEL
        ).pack()

        tk.Label(
            header, text="E X E C U T I O N   C O R E",
            font=("Consolas", 11),
            fg=AMBER_DIM, bg=BG_PANEL
        ).pack(pady=(2, 0))

        # Thin separator
        tk.Frame(panel, bg=AMBER_DIM, height=1).pack(fill="x", padx=30)

        # ── Status row ────────────────────────────────────────────────────────
        status_frame = tk.Frame(panel, bg=BG_PANEL, pady=20)
        status_frame.pack(fill="x")

        if self.success:
            sym, label, clr = "✓", "EXECUTION SUCCESSFUL", SUCCESS_CLR
        else:
            sym, label, clr = "✕", "EXECUTION FAILED", ERROR_CLR

        tk.Label(
            status_frame, text=sym,
            font=("Consolas", 42, "bold"),
            fg=clr, bg=BG_PANEL
        ).pack()

        tk.Label(
            status_frame, text=label,
            font=("Consolas", 15, "bold"),
            fg=clr, bg=BG_PANEL, pady=4
        ).pack()

        tk.Label(
            status_frame, text=f"PROJECT: {self.project_name.upper()}",
            font=("Consolas", 9),
            fg=TEXT_DIM, bg=BG_PANEL
        ).pack()

        # ── Terminal output area ──────────────────────────────────────────────
        term_outer = tk.Frame(panel, bg=AMBER_DIM, padx=1, pady=1)
        term_outer.pack(fill="both", expand=True, padx=30, pady=(6, 6))

        term_header = tk.Frame(term_outer, bg="#1a1208")
        term_header.pack(fill="x")
        tk.Label(
            term_header,
            text="  ●  OUTPUT STREAM",
            font=("Consolas", 9),
            fg=AMBER_DIM, bg="#1a1208", anchor="w", pady=4
        ).pack(fill="x")

        term_frame = tk.Frame(term_outer, bg=TERMINAL_BG)
        term_frame.pack(fill="both", expand=True)

        self._term = tk.Text(
            term_frame,
            bg=TERMINAL_BG, fg=TERMINAL_FG,
            font=("Consolas", 12),
            bd=0, relief="flat",
            wrap="word",
            padx=14, pady=10,
            state="disabled",
            selectbackground=AMBER_DIM,
            insertbackground=AMBER,
            cursor="arrow",
        )
        scrollbar = tk.Scrollbar(term_frame, command=self._term.yview,
                                  bg=BG_PANEL, troughcolor=BG_PANEL,
                                  activebackground=AMBER)
        self._term.configure(yscrollcommand=scrollbar.set)
        self._term.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._write_terminal()

        # ── Footer ────────────────────────────────────────────────────────────
        tk.Frame(panel, bg=AMBER_DIM, height=1).pack(fill="x", padx=30)

        footer = tk.Frame(panel, bg=BG_PANEL, pady=14)
        footer.pack(fill="x")

        tk.Label(
            footer, text="A V E N G E R S ,   A S S E M B L E .",
            font=("Consolas", 11, "bold"),
            fg=AMBER, bg=BG_PANEL
        ).pack()

        tk.Label(
            footer, text="[ PRESS  ENTER / ESC / SPACE  TO DISMISS ]",
            font=("Consolas", 9),
            fg=TEXT_DIM, bg=BG_PANEL, pady=4
        ).pack()

    # ── Terminal content ──────────────────────────────────────────────────────

    def _write_terminal(self):
        self._term.configure(state="normal")

        if self.stdout:
            self._term.insert("end", self.stdout.rstrip() + "\n")

        if not self.success and self.stderr:
            self._term.insert("end", "\n── STDERR ─────────────────────────\n", "err")
            self._term.insert("end", self.stderr.rstrip() + "\n", "err")
            self._term.tag_config("err", foreground=ERROR_CLR)

        if not self.stdout and not self.stderr:
            self._term.insert("end", "(no output captured)\n", "dim")
            self._term.tag_config("dim", foreground=TEXT_DIM)

        self._term.configure(state="disabled")
        self._term.see("end")

    # ── Scanline animation ────────────────────────────────────────────────────

    def _animate_scanline(self):
        self._scanline_y = 0
        self._bg_canvas.delete("scanline")
        self._bg_canvas.create_line(
            0, self._scanline_y, self.W, self._scanline_y,
            fill="#ffffff", width=1, tags="scanline"
        )
        self._bg_canvas.itemconfig("scanline", stipple="gray12")
        self._tick_scanline()

    def _tick_scanline(self):
        self._scanline_y = (self._scanline_y + 4) % self.H
        self._bg_canvas.coords(
            "scanline",
            0, self._scanline_y, self.W, self._scanline_y
        )
        self.root.after(16, self._tick_scanline)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _close(self, event=None):
        self._particles.stop()
        if self.on_close:
            self.on_close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ── Public helper ─────────────────────────────────────────────────────────────

def show_result(
    success: bool,
    stdout: str = "",
    stderr: str = "",
    project_name: str = "PROJECT ALPHA",
    on_close=None,
    block: bool = True,
):
    """
    Launch the Execution Core GUI.

    Parameters
    ----------
    success : bool
    stdout  : str   — captured program output
    stderr  : str   — captured error text
    project_name : str
    on_close : callable | None  — called after window closes
    block    : bool — if True, runs the Tkinter mainloop on the calling thread
                      (call from main thread or use block=False + threading)
    """
    gui = ExecutionResultGUI(
        success=success,
        stdout=stdout,
        stderr=stderr,
        project_name=project_name,
        on_close=on_close,
    )
    if block:
        gui.run()
    else:
        t = threading.Thread(target=gui.run, daemon=True)
        t.start()
        return t


# ── Standalone demo ───────────────────────────────────────────────────────────

_DEMO_SUCCESS_OUTPUT = """\
========================================
       STARK // CODE ONLINE
========================================

  Suit systems: ONLINE
  Arc reactor:  STABLE
  JARVIS link:  ACTIVE

========================================
Developer identity: Tony Stark
========================================
"""

_DEMO_ERROR_OUTPUT = """\
Initializing STARK // CODE runtime...
Loading modules...
"""

_DEMO_STDERR = """\
Traceback (most recent call last):
  File "main.py", line 14, in <module>
    result = arc_reactor.power_up()
AttributeError: 'NoneType' object has no attribute 'power_up'

ARC REACTOR FAILURE — SYSTEM OFFLINE
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STARK // CODE Execution Core GUI demo")
    parser.add_argument(
        "--demo",
        choices=["success", "error"],
        default="success",
        help="Demo mode: 'success' or 'error'  (default: success)"
    )
    args = parser.parse_args()

    if args.demo == "success":
        show_result(
            success=True,
            stdout=_DEMO_SUCCESS_OUTPUT,
            stderr="",
            project_name="Avengers HQ Alpha",
        )
    else:
        show_result(
            success=False,
            stdout=_DEMO_ERROR_OUTPUT,
            stderr=_DEMO_STDERR,
            project_name="Arc Reactor Test",
        )
