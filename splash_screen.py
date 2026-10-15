# ============================================================
# splash_screen.py — Animated Splash Screen (Redesigned)
# ============================================================

import customtkinter as ctk
import tkinter as tk
import math
import time
import threading
from config import APP_NAME, INSTITUTION, SPLASH_DURATION_MS, APPEARANCE_MODE, COLOR_THEME


class SplashScreen(ctk.CTkToplevel):

    def __init__(self, master=None):
        super().__init__(master)

        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title("")
        self.resizable(False, False)
        self.overrideredirect(True)

        # ── Responsive window size ────────────────────────────
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # Responsive: min 600x480, max 800x600, scale with screen
        W = max(700, min(800, int(sw * 0.45)))
        H = max(500, min(600, int(sh * 0.60)))
        self._W = W
        self._H = H
        x = (sw - W) // 2
        y = (sh - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")

        self._progress_value = 0.0
        self._particles = []
        self._anim_frame = 0
        self._is_alive = True
        self._destroyed = False
        self._after_ids = set()

        self._build_ui()
        self._animate_progress()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        W, H = self._W, self._H

        # Root bg
        self.configure(fg_color="#050810")

        # Outer border glow frame
        outer = ctk.CTkFrame(
            self,
            fg_color="#050810",
            corner_radius=20,
            border_width=1,
            border_color="#0f1f3d",
        )
        outer.place(x=0, y=0, relwidth=1, relheight=1)

        # ── Canvas for particle + geometric background ────────
        self.canvas = tk.Canvas(
            outer,
            bg="#050810",
            highlightthickness=0,
            width=W, height=H,
        )
        self.canvas.place(x=0, y=0)

        # Draw static geometric grid lines
        self._draw_grid()

        # Accent lines
        self._draw_accent_lines()

        # ── Scan line effect (horizontal animated) ────────────
        self.scan_line = self.canvas.create_rectangle(
            0, 0, W, 2,
            fill="#0d4f8c", outline="", stipple="gray25"
        )

        # ── Center glow circle ────────────────────────────────
        cx, cy = W // 2, int(H * 0.35)
        r = int(min(W, H) * 0.13)

        # Outer glow rings
        for i, (radius, alpha) in enumerate([
            (r + 50, "#050f1f"),
            (r + 35, "#071428"),
            (r + 20, "#0a1f3d"),
            (r + 8,  "#0d2d5c"),
        ]):
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=alpha, outline="", tags="glow"
            )

        # Main circle
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill="#071628", outline="#1a4a8a", width=2,
            tags="circle"
        )

        # Inner circle
        ri = int(r * 0.65)
        self.canvas.create_oval(
            cx - ri, cy - ri, cx + ri, cy + ri,
            fill="#050d1a", outline="#0d3a6e", width=1,
        )

        # Face icon — geometric lines suggesting a face
        self._draw_face_icon(cx, cy, ri)

        # Corner brackets
        self._draw_corner_brackets(cx, cy, r + 14)

        # ── Text overlays ─────────────────────────────────────
        # Main title
        title_y = cy + r + int(H * 0.06)
        self.canvas.create_text(
            W // 2, title_y,
            text="FACE RECOGNITION",
            font=("Segoe UI", int(W * 0.036), "bold"),
            fill="#e8f4ff",
            tags="title"
        )

        # Subtitle
        self.canvas.create_text(
            W // 2, title_y + int(H * 0.065),
            text="ATTENDANCE  SYSTEM",
            font=("Segoe UI", int(W * 0.022)),
            fill="#4a8abf",
            tags="subtitle"
        )

        # Letter-spacing dots
        self.canvas.create_text(
            W // 2, title_y + int(H * 0.115),
            text="· · · · · · · · · · · · · · · · · · · ·",
            font=("Segoe UI", int(W * 0.012)),
            fill="#1a3a5c",
        )

        # Institution
        self.canvas.create_text(
            W // 2, title_y + int(H * 0.155),
            text=INSTITUTION.upper(),
            font=("Segoe UI", int(W * 0.013)),
            fill="#2a5a8a",
            tags="inst"
        )

        # ── Progress bar (custom canvas) ──────────────────────
        bar_y = int(H * 0.80)
        bar_w = int(W * 0.68)
        bar_h = 3
        bx = (W - bar_w) // 2

        # Track
        self.canvas.create_rectangle(
            bx, bar_y, bx + bar_w, bar_y + bar_h,
            fill="#0a1f3d", outline="", tags="bar_track"
        )

        # Fill (will be updated)
        self.bar_fill = self.canvas.create_rectangle(
            bx, bar_y, bx, bar_y + bar_h,
            fill="#1a6abf", outline="", tags="bar_fill"
        )

        # Glow fill
        self.bar_glow = self.canvas.create_rectangle(
            bx, bar_y - 1, bx, bar_y + bar_h + 1,
            fill="#3a9aef", outline="", tags="bar_glow"
        )

        # Percentage
        self.pct_text = self.canvas.create_text(
            W // 2, bar_y + int(H * 0.045),
            text="0%",
            font=("Segoe UI", int(W * 0.018)),
            fill="#1a5a9a",
            tags="pct"
        )

        # Status text
        self.status_text = self.canvas.create_text(
            W // 2, bar_y + int(H * 0.09),
            text="INITIALIZING SYSTEM...",
            font=("Segoe UI", int(W * 0.014)),
            fill="#1a4a7a",
            tags="status"
        )

        # Bottom tech stack
        self.canvas.create_text(
            W // 2, H - int(H * 0.04),
            text="Python  ·  MySQL  ·  OpenCV  ·  face_recognition",
            font=("Segoe UI", int(W * 0.011)),
            fill="#0f2a4a",
        )

        # Corner version
        self.canvas.create_text(
            W - 12, H - 12,
            text="v2.0",
            font=("Segoe UI", int(W * 0.011)),
            fill="#0f2a4a",
            anchor="se"
        )

        # Store bar info
        self._bx = bx
        self._bar_y = bar_y
        self._bar_w = bar_w
        self._bar_h = bar_h
        self._cx = cx
        self._cy = cy
        self._r = r

        # Drag binding
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_motion)

        # Start animations
        self._animate_scan_line()
        self._animate_circle_pulse()
        self._spawn_particles()

    def _draw_grid(self):
        W, H = self._W, self._H
        step = int(W * 0.08)
        color = "#080f1e"
        for x in range(0, W, step):
            self.canvas.create_line(x, 0, x, H, fill=color, width=1)
        for y in range(0, H, step):
            self.canvas.create_line(0, y, W, y, fill=color, width=1)

    def _draw_accent_lines(self):
        W, H = self._W, self._H
        # Top-left diagonal accent
        self.canvas.create_line(
            0, int(H * 0.12), int(W * 0.18), 0,
            fill="#0a2040", width=1)
        # Bottom-right diagonal
        self.canvas.create_line(
            W, int(H * 0.88), int(W * 0.82), H,
            fill="#0a2040", width=1)
        # Left vertical accent
        self.canvas.create_line(
            int(W * 0.06), int(H * 0.1),
            int(W * 0.06), int(H * 0.9),
            fill="#0a2040", width=1)
        # Right vertical accent
        self.canvas.create_line(
            int(W * 0.94), int(H * 0.1),
            int(W * 0.94), int(H * 0.9),
            fill="#0a2040", width=1)

    def _draw_face_icon(self, cx, cy, r):
        """Geometric face scan icon."""
        s = int(r * 0.45)
        c = "#1a6abf"
        lw = 1

        # Eyes
        ew = int(s * 0.3)
        eh = int(s * 0.15)
        ex_off = int(s * 0.35)
        ey = cy - int(s * 0.15)

        for sign in (-1, 1):
            ex = cx + sign * ex_off
            self.canvas.create_rectangle(
                ex - ew, ey - eh, ex + ew, ey + eh,
                outline=c, width=lw, fill=""
            )
            # Eye scan line
            self.canvas.create_line(
                ex - ew, ey, ex + ew, ey,
                fill="#0d4f8c", width=1)

        # Nose dot
        nd = int(s * 0.06)
        self.canvas.create_oval(
            cx - nd, cy - nd, cx + nd, cy + nd,
            fill=c, outline=""
        )

        # Mouth
        my = cy + int(s * 0.35)
        mw = int(s * 0.45)
        self.canvas.create_line(
            cx - mw, my, cx + mw, my,
            fill=c, width=lw
        )
        # Mouth corners
        mc = int(s * 0.1)
        self.canvas.create_line(
            cx - mw, my, cx - mw, my - mc, fill=c, width=lw)
        self.canvas.create_line(
            cx + mw, my, cx + mw, my - mc, fill=c, width=lw)

        # Face outline box
        fw = int(s * 0.85)
        fh = int(s * 1.1)
        self.canvas.create_rectangle(
            cx - fw, cy - fh, cx + fw, cy + fh,
            outline="#0d3a6e", width=1, fill=""
        )

        # Scan target dots (4 corners of face box)
        dot = 3
        dot_color = "#1a6abf"
        for dx, dy in [(-fw, -fh), (fw, -fh), (-fw, fh), (fw, fh)]:
            self.canvas.create_oval(
                cx + dx - dot, cy + dy - dot,
                cx + dx + dot, cy + dy + dot,
                fill=dot_color, outline=""
            )

    def _draw_corner_brackets(self, cx, cy, r):
        """Corner bracket decorations around circle."""
        size = int(r * 0.28)
        gap = int(r * 0.06)
        c = "#1a5a9a"
        lw = 2

        for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            bx = cx + sx * (r + gap)
            by = cy + sy * (r + gap)

            # Horizontal
            self.canvas.create_line(
                bx, by, bx + sx * size, by,
                fill=c, width=lw)
            # Vertical
            self.canvas.create_line(
                bx, by, bx, by + sy * size,
                fill=c, width=lw)

    # ── Animations ────────────────────────────────────────────

    def safe_after(self, ms, callback, *args):
        """Schedule after() and track the ID for cleanup."""
        if self._destroyed or not self.winfo_exists(): return None
        aid = self.after(ms, callback, *args)
        self._after_ids.add(aid)
        return aid

    def _animate_scan_line(self):
        if self._destroyed or not self._is_alive or not self.winfo_exists():
            return
        W, H = self._W, self._H
        speed = int(H * 0.008)
        try:
            coords = self.canvas.coords(self.scan_line)
            y = coords[3] + speed
            if y > H:
                y = 0
            self.canvas.coords(self.scan_line, 0, y - 2, W, y)
            
            if not self._destroyed:
                self.safe_after(30, self._animate_scan_line)
        except Exception:
            pass

    def _animate_circle_pulse(self):
        if self._destroyed or not self._is_alive or not self.winfo_exists():
            return
        self._anim_frame += 1
        t = self._anim_frame * 0.06
        pulse = int(math.sin(t) * 3)
 
        cx, cy, r = self._cx, self._cy, self._r
        try:
            # Outer glow pulse
            glow_items = self.canvas.find_withtag("glow")
            offsets = [50 + pulse, 35 + pulse, 20 + pulse, 8 + pulse]
            for item, off in zip(glow_items, offsets):
                self.canvas.coords(
                    item,
                    cx - off, cy - off, cx + off, cy + off)
            
            if not self._destroyed:
                self.safe_after(50, self._animate_circle_pulse)
        except Exception:
            pass

    def _spawn_particles(self):
        """Floating data particles."""
        if self._destroyed or not self._is_alive or not self.winfo_exists():
            return
        W, H = self._W, self._H
        import random

        # Spawn new particle occasionally
        if random.random() < 0.3:
            x = random.randint(0, W)
            y = H
            size = random.randint(1, 3)
            speed = random.uniform(0.5, 2.0)
            alpha = random.choice(["#0a2040", "#0d3060", "#0a4080"])
            p = self.canvas.create_oval(
                x, y, x + size, y + size,
                fill=alpha, outline="", tags="particle"
            )
            self._particles.append([p, x, y, speed])

        # Move particles
        dead = []
        for pt in self._particles:
            pid, px, py, spd = pt
            py -= spd
            pt[2] = py
            try:
                self.canvas.move(pid, 0, -spd)
                if py < 0:
                    self.canvas.delete(pid)
                    dead.append(pt)
            except Exception:
                dead.append(pt)

        for pt in dead:
            if pt in self._particles:
                self._particles.remove(pt)

        if not self._destroyed:
            self.safe_after(40, self._spawn_particles)

    # ── Progress ──────────────────────────────────────────────

    _STATUS_STEPS = [
        (0.00, "INITIALIZING SYSTEM..."),
        (0.15, "CONNECTING TO DATABASE..."),
        (0.30, "LOADING FACE RECOGNITION ENGINE..."),
        (0.50, "FETCHING USER ENCODINGS..."),
        (0.65, "CALIBRATING DETECTION MODEL..."),
        (0.80, "PREPARING INTERFACE..."),
        (0.92, "ALMOST READY..."),
        (1.00, "SYSTEM READY"),
    ]

    def _animate_progress(self):
        step_ms = 30
        total_steps = SPLASH_DURATION_MS // step_ms
        increment = 1.0 / total_steps

        def tick():
            if self._destroyed or not self._is_alive or not self.winfo_exists():
                return
            if self._progress_value >= 1.0:
                self._launch()
                return
 
            self._progress_value = min(
                self._progress_value + increment, 1.0)
            self._update_progress_bar()
            
            if not self._destroyed:
                self.safe_after(step_ms, tick)

        self.safe_after(120, tick)

    def _update_progress_bar(self):
        bx = self._bx
        bar_y = self._bar_y
        bar_w = self._bar_w
        bar_h = self._bar_h
        W = self._W

        filled = int(bar_w * self._progress_value)
        pct = int(self._progress_value * 100)

        try:
            # Main fill
            self.canvas.coords(
                self.bar_fill,
                bx, bar_y, bx + filled, bar_y + bar_h)

            # Glow (slightly larger, brighter at tip)
            glow_w = min(filled + 4, bar_w)
            self.canvas.coords(
                self.bar_glow,
                bx, bar_y - 1,
                bx + glow_w, bar_y + bar_h + 1)

            # Color shift: blue → cyan as fills
            r_c = int(26 + self._progress_value * 14)
            g_c = int(106 + self._progress_value * 50)
            b_c = int(191 + self._progress_value * 50)
            color = f"#{r_c:02x}{g_c:02x}{min(b_c, 255):02x}"
            self.canvas.itemconfig(self.bar_fill, fill=color)

            glow_color = f"#{min(r_c+20,255):02x}{min(g_c+40,255):02x}{min(b_c+30,255):02x}"
            self.canvas.itemconfig(self.bar_glow, fill=glow_color)

            # Percentage
            self.canvas.itemconfig(
                self.pct_text, text=f"{pct}%",
                fill=color)

            # Status
            for threshold, msg in reversed(self._STATUS_STEPS):
                if self._progress_value >= threshold:
                    self.canvas.itemconfig(self.status_text, text=msg)
                    break

        except Exception:
            pass

    # ── Launch ────────────────────────────────────────────────

    def _launch(self):
        self.safe_after(300, self._open_main)

    def _open_main(self):
        from views.main_page import MainPage
        self._is_alive = False
        self._destroyed = True
        
        self._cancel_all_afters()

        self.destroy()
        app = MainPage(master=self.master)


    def _cancel_all_afters(self):
        """Cancel every pending after() callback to prevent
        'invalid command name' errors on destroy."""
        try:
            # First clean our tracked IDs
            for aid in list(self._after_ids):
                try: self.after_cancel(aid)
                except: pass
            self._after_ids.clear()
            
            # Then aggressively clean all Tkinter internal after tasks
            after_ids = self.tk.call('after', 'info')
            if isinstance(after_ids, str):
                after_ids = after_ids.split()
            for aid in after_ids:
                try: self.after_cancel(aid)
                except: pass
        except Exception:
            pass

    # ── Drag ──────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_motion(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")