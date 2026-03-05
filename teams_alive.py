"""
TeamsAlive - Keep Microsoft Teams active with minimal mouse movements.
Moves the mouse by 2px and back every 60 seconds + Use F15.
"""

import sys
import time
import threading
import platform
import os
import io
import tkinter as tk
import ctypes
from PIL import Image, ImageTk

# ── Helper for PyInstaller Paths ─────────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ── Tray & Mouse Backends ────────────────────────────────────────────────────
try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    MOUSE_AVAILABLE = True
except ImportError:
    MOUSE_AVAILABLE = False

# ── ADJUSTED FOR PERSONAL TEAMS & WINDOWS IDLE ───────────────────────────────
INTERVAL = 60  # Faster heartbeat (60 seconds)

def _nudge():
    if MOUSE_AVAILABLE:
        # 1. Use F15 - It resets the idle timer but doesn't affect typing
        pyautogui.press('f15')
        
        # 2. Get current position to ensure we don't drift
        curr_x, curr_y = pyautogui.position()
        
        # 3. Perform a 'Jitter' (Move 2px and back instantly)
        # We use moveTo to be more forceful than moveRel
        pyautogui.moveTo(curr_x + 2, curr_y)
        pyautogui.moveTo(curr_x, curr_y)

# ── Worker Thread ────────────────────────────────────────────────────────────
class Worker(threading.Thread):
    def __init__(self, on_tick):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
        self._on_tick = on_tick
        self.nudge_count = 0

    def run(self):
        while not self._stop_event.wait(INTERVAL):
            _nudge()
            self.nudge_count += 1
            self._on_tick(self.nudge_count)

    def stop(self):
        self._stop_event.set()

# ── Main Application ─────────────────────────────────────────────────────────
class App(tk.Tk):
    BG      = "#1e1e2e"
    SURFACE = "#2a2a3d"
    ACCENT  = "#5b9bd5"
    ACCENT_H= "#4a8cc4"
    TEXT    = "#e0e0f0"
    SUBTEXT = "#8888aa"
    RED     = "#f28b82"
    GREEN   = "#81c995"
    BORDER  = "#3a3a55"

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        self.configure(bg=self.BG)

        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: pass

        self.ico_file = resource_path("icon.ico")
        self.png_file = resource_path("icon.png")

        try:
            if os.path.exists(self.ico_file):
                self.iconbitmap(self.ico_file)
            if os.path.exists(self.png_file):
                self.img_main = Image.open(self.png_file)
        except Exception as e:
            print(f"Icon load error: {e}")

        self._worker = None
        self._running = False
        self._last_tick_label = tk.StringVar(value="—")
        self._count_var = tk.IntVar(value=0)
        self._status_var = tk.StringVar(value="Idle")

        self._build_ui()
        self._center_window(360, 340)

        self._tray = None
        if TRAY_AVAILABLE:
            self._setup_tray()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        header = tk.Frame(self, bg=self.SURFACE, height=64)
        header.pack(fill="x")

        if os.path.exists(self.png_file):
            try:
                hdr_img = self.img_main.resize((36, 36), Image.LANCZOS)
                self._hdr_icon = ImageTk.PhotoImage(hdr_img)
                tk.Label(header, image=self._hdr_icon, bg=self.SURFACE).pack(side="left", padx=(16, 4), pady=14)
            except: pass

        tk.Label(header, text="TeamsAlive", font=("Segoe UI", 16, "bold"), bg=self.SURFACE, fg=self.ACCENT).pack(side="left", pady=14)
        tk.Label(header, text="v1.1", font=("Segoe UI", 9), bg=self.SURFACE, fg=self.SUBTEXT).pack(side="right", padx=20)

        status_frame = tk.Frame(self, bg=self.BG)
        status_frame.pack(fill="x", padx=20, pady=(18, 4))
        self._status_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 14), bg=self.BG, fg=self.SUBTEXT)
        self._status_dot.pack(side="left")
        tk.Label(status_frame, textvariable=self._status_var, font=("Segoe UI", 12, "bold"), bg=self.BG, fg=self.TEXT).pack(side="left", padx=6)

        grid = tk.Frame(self, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        grid.pack(fill="x", padx=20, pady=10)
        self._make_stat(grid, "Interval", f"{INTERVAL}s", 0)
        self._make_stat(grid, "Nudges", "", 1, var=self._count_var)
        self._make_stat(grid, "Last", "", 2, strvar=self._last_tick_label)

        self._btn = tk.Button(self, text="▶  Start", font=("Segoe UI", 11, "bold"), bg=self.ACCENT, fg="white", 
                              bd=0, cursor="hand2", padx=20, pady=10, command=self._toggle)
        self._btn.pack(pady=(16, 6))

    def _make_stat(self, parent, label, value, col, var=None, strvar=None):
        cell = tk.Frame(parent, bg=self.SURFACE)
        cell.grid(row=0, column=col, padx=18, pady=12, sticky="ew")
        parent.columnconfigure(col, weight=1)
        tk.Label(cell, text=label, font=("Segoe UI", 8), bg=self.SURFACE, fg=self.SUBTEXT).pack()
        target = strvar if strvar else (var if var else None)
        if target:
            tk.Label(cell, textvariable=target, font=("Segoe UI", 13, "bold"), bg=self.SURFACE, fg=self.TEXT).pack()
        else:
            tk.Label(cell, text=value, font=("Segoe UI", 13, "bold"), bg=self.SURFACE, fg=self.TEXT).pack()

    def _make_tray_image(self, active=False):
        if not os.path.exists(self.png_file):
            return Image.new('RGB', (64, 64), color=(255, 0, 0))
        img = Image.open(self.png_file).convert("RGBA")
        if not active: return img.convert("LA").convert("RGBA")
        return img

    def _setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_window, default=True),
            pystray.MenuItem("Quit", self._quit_app),
        )
        self._tray = pystray.Icon(APP_NAME, self._make_tray_image(), APP_NAME, menu)
        threading.Thread(target=self._tray.run, daemon=True).start()

    def _toggle(self):
        if self._running: self._stop()
        else: self._start()

    def _start(self):
        self._running = True
        self._status_var.set("Active")
        self._status_dot.config(fg=self.GREEN)
        self._btn.config(text="⏹  Stop", bg=self.RED)
        if self._tray: self._tray.icon = self._make_tray_image(active=True)
        self._worker = Worker(on_tick=self._on_tick)
        self._worker.start()

    def _stop(self):
        if self._worker: self._worker.stop()
        self._running = False
        self._status_var.set("Idle")
        self._status_dot.config(fg=self.SUBTEXT)
        self._btn.config(text="▶  Start", bg=self.ACCENT)
        if self._tray: self._tray.icon = self._make_tray_image(active=False)

    def _on_tick(self, count):
        now = time.strftime("%H:%M:%S")
        self.after(0, lambda: self._count_var.set(count))
        self.after(0, lambda: self._last_tick_label.set(now))

    def _on_close(self):
        if TRAY_AVAILABLE and self._tray: self.withdraw()
        else: self._quit_app()

    def _show_window(self, *_):
        self.deiconify()
        self.lift()

    def _quit_app(self, *_):
        self._stop()
        if self._tray: self._tray.stop()
        self.destroy()

if __name__ == "__main__":
    APP_NAME = "TeamsAlive"
    App().mainloop()