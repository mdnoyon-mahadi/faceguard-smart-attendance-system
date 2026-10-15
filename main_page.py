# ============================================================
# main_page.py — FaceGuard Smart Attendance System
# ============================================================
# LEFT  (56%):
#   ① Particle network graph animation (from student_login)
#   ② Rotating camera/scanner ring animation
# RIGHT (44%):
#   ③ 3 login buttons — smooth scale-up hover, 100% accurate
# ============================================================

import customtkinter as ctk
import tkinter as tk
import math, random, time
from datetime import datetime
from config import APP_NAME, INSTITUTION, APPEARANCE_MODE, COLOR_THEME
from theme import ThemeManager
from transitions import PageTransition, NavigationLock

# ── Palette ───────────────────────────────────────────────────
BG         = "#080d16"
BG2        = "#0a1020"
PANEL_R    = "#0b1422"
CARD       = "#0e1a2e"
BORDER     = "#152840"
BORDER_LIT = "#1e4080"
ACCENT     = "#3b82f6"
ACCENT2    = "#60a5fa"
ACCENT_DIM = "#1d3a6e"
GREEN      = "#22c55e"
PURPLE     = "#7c3aed"
TEXT       = "#e2e8f0"
TEXT2      = "#94a3b8"
TEXT3      = "#475569"

# Particle colors (same as student_login)
PARTICLE_A = "#00d2ff"
PARTICLE_B = "#7c3aed"
LINE_COLOR = "#0a3040"
GRID_COLOR = "#0d1520"

# ── 3 Buttons — same color plate, unique glow ─────────────────
BUTTONS = [
    {
        "key":     "student",
        "icon":    "🎓",
        "title":   "Student Login",
        "sub":     "Portal & Registration",
        "bg":      "#0f1f42",
        "hover":   "#1a3a7a",
        "glow":    "#3b82f6",
        "command": "_open_student_portal",
    },
    {
        "key":     "scan",
        "icon":    "◈",
        "title":   "Scan Face",
        "sub":     "Mark Attendance",
        "bg":      "#0f1f42",
        "hover":   "#1a3a7a",
        "glow":    "#60a5fa",
        "primary": True,
        "command": "_open_face_scanner",
    },
    {
        "key":     "admin",
        "icon":    "⬡",
        "title":   "Admin Login",
        "sub":     "Dashboard & Reports",
        "bg":      "#0f1f42",
        "hover":   "#1a3a7a",
        "glow":    "#7c3aed",
        "command": "_open_admin_login",
    },
]


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════
def _lerp(a, b, t):
    return a + (b - a) * t

def _hex2rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _blend_hex(c1, c2, t):
    r1,g1,b1 = _hex2rgb(c1)
    r2,g2,b2 = _hex2rgb(c2)
    return "#{:02x}{:02x}{:02x}".format(
        int(_lerp(r1,r2,t)), int(_lerp(g1,g2,t)), int(_lerp(b1,b2,t)))

def _dim(hex_col, alpha_0_255):
    r1,g1,b1 = _hex2rgb(hex_col)
    a = alpha_0_255 / 255
    return "#{:02x}{:02x}{:02x}".format(
        int(r1*a + 0x08*(1-a)),
        int(g1*a + 0x0d*(1-a)),
        int(b1*a + 0x16*(1-a)))

def _darken(hex_col, factor):
    r,g,b = _hex2rgb(hex_col)
    return "#{:02x}{:02x}{:02x}".format(
        int(r*factor), int(g*factor), int(b*factor))

def _rrect(cv, x1, y1, x2, y2, r, fill="", outline="", tags=""):
    """Filled rounded rectangle on tk.Canvas."""
    r = max(1, int(r))
    kw = dict(fill=fill, outline=outline, tags=tags)
    cv.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
    cv.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)
    cv.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90, style="pieslice", **kw)
    cv.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90, style="pieslice", **kw)
    cv.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90, style="pieslice", **kw)
    cv.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, style="pieslice", **kw)


# ══════════════════════════════════════════════════════════════
# Particle (identical to student_login)
# ══════════════════════════════════════════════════════════════
class _Particle:
    def __init__(self, w, h, idx):
        self.w, self.h = w, h
        self.x     = random.uniform(0, w)
        self.y     = random.uniform(0, h)
        self.vx    = random.uniform(-0.40, 0.40)
        self.vy    = random.uniform(-0.40, 0.40)
        self.r     = random.uniform(1.8, 3.2)
        self.color = PARTICLE_A if idx % 4 != 0 else PARTICLE_B

    def move(self):
        self.x += self.vx; self.y += self.vy
        if self.x < 0 or self.x > self.w: self.vx *= -1
        if self.y < 0 or self.y > self.h: self.vy *= -1

    def resize(self, w, h):
        self.w, self.h = w, h


# ══════════════════════════════════════════════════════════════
class MainPage(ctk.CTkToplevel):

    N_PARTICLES  = 70
    CONNECT_DIST = 140

    def __init__(self, master=None):
        super().__init__(master)
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        self.title("FaceGuard — Smart Attendance System")

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.state("zoomed")
        self.resizable(True, True)
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        # State
        self._alive       = True
        self._particles   = []
        self._pulse_dir   = 1
        self._pulse_a     = 0.0
        self._after_id    = None
        self._last_w      = sw
        self._last_h      = sh
        self._scan_angle  = 0.0   # camera rotation angle

        ThemeManager.register(self._refresh_theme)
        self._build_ui()
        self._update_clock()
        self.after(150, self._init_particles)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        PageTransition.fade_in(self, steps=15, ms=18)

    # ══════════════════════════════════════════════════════════
    # BUILD UI
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        # Left canvas — particle graph + camera animation
        self.left_cv = tk.Canvas(
            self, bg=BG, highlightthickness=0)
        self.left_cv.place(relx=0, rely=0,
                           relwidth=0.56, relheight=1)

        # Right panel — buttons
        self.right_panel = ctk.CTkFrame(
            self,
            fg_color=(PANEL_R, PANEL_R),
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        self.right_panel.place(relx=0.56, rely=0,
                               relwidth=0.44, relheight=1)

        self._build_topbar()
        self._build_left_content()
        self._build_right_content()
        self._build_bottombar()
        self.bind("<Configure>", self._on_resize)

    # ── Top bar ───────────────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(
            self, fg_color=(BG2, BG2),
            corner_radius=0, height=52)
        bar.place(x=0, y=0, relwidth=1)
        bar.pack_propagate(False)
        bar.lift()

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32)

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(side="left", fill="y")
        ctk.CTkLabel(row, text="◈",
            font=ctk.CTkFont(family="Segoe UI", size=24),
            text_color=ACCENT).pack(side="left", pady=13, padx=(0, 8))
        ctk.CTkLabel(row, text="FaceGuard",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT).pack(side="left")

        self.clock_lbl = ctk.CTkLabel(inner, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT3)
        self.clock_lbl.pack(side="right")

        self.theme_btn = ctk.CTkButton(inner,
            text="☀ Light" if ThemeManager.current_mode == "dark" else "☾ Dark",
            width=88, height=30, corner_radius=15,
            fg_color=CARD, hover_color=BORDER_LIT,
            text_color=ACCENT,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=14, pady=11)

        ctk.CTkFrame(self, height=1, fg_color=BORDER,
                     corner_radius=0).place(x=0, y=52, relwidth=1)

    # ── Left branding ─────────────────────────────────────────

    def _build_left_content(self):
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.place(relx=0.28, rely=0.52, anchor="center")
        mid.lift()

        badge = ctk.CTkFrame(mid,
            fg_color=(CARD, CARD), corner_radius=20,
            border_width=1, border_color=BORDER_LIT)
        badge.pack(pady=(0, 18))
        ctk.CTkLabel(badge, text="  ◈  AI-POWERED ATTENDANCE  ",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=ACCENT).pack(padx=4, pady=7)

        ctk.CTkLabel(mid, text="FaceGuard",
            font=ctk.CTkFont(family="Segoe UI", size=56, weight="bold"),
            text_color=TEXT).pack()
        ctk.CTkLabel(mid, text="Smart Attendance System",
            font=ctk.CTkFont(family="Segoe UI", size=21),
            text_color=ACCENT).pack(pady=(4, 0))
        ctk.CTkLabel(mid,
            text="Face recognition  ·  Real-time  ·  Automated",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT3).pack(pady=(10, 0))

        ctk.CTkFrame(mid, height=2, width=200,
                     fg_color=ACCENT_DIM).pack(pady=(20, 0))

        sr = ctk.CTkFrame(mid, fg_color="transparent")
        sr.pack(pady=(18, 0))
        for val, lbl, col in [
            ("99.2%", "Accuracy", ACCENT),
            ("0.3s",  "Response", GREEN),
            ("Auto",  "Reports",  PURPLE),
        ]:
            sf = ctk.CTkFrame(sr,
                fg_color=(CARD, CARD), corner_radius=10,
                border_width=1, border_color=BORDER,
                width=108, height=64)
            sf.pack(side="left", padx=8)
            sf.pack_propagate(False)
            ctk.CTkLabel(sf, text=val,
                font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
                text_color=col).place(relx=0.5, rely=0.36, anchor="center")
            ctk.CTkLabel(sf, text=lbl,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=TEXT3).place(relx=0.5, rely=0.74, anchor="center")

    # ── Right content ─────────────────────────────────────────

    def _build_right_content(self):
        mid = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        mid.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(mid, text="Welcome Back",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT).pack(pady=(0, 4))
        ctk.CTkLabel(mid, text="Select your role to continue",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT3).pack(pady=(0, 32))

        for i, bd in enumerate(BUTTONS):
            self._make_scale_btn(mid, bd)
            if i < len(BUTTONS) - 1:
                ctk.CTkFrame(mid, height=14,
                             fg_color="transparent").pack()

        ctk.CTkFrame(mid, height=1, width=320,
                     fg_color=BORDER).pack(pady=(30, 18))
        ctk.CTkLabel(mid,
            text="◉  Secured by AI face recognition",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT3).pack()

    # ══════════════════════════════════════════════════════════
    # SCALE HOVER BUTTON — grows on hover, 100% accurate
    # ══════════════════════════════════════════════════════════

    def _make_scale_btn(self, parent, data):
        is_primary = data.get("primary", False)
        bg_c   = data["bg"]
        hov_c  = data["hover"]
        glow_c = data["glow"]

        BASE_W, BASE_H = 320, 72
        MAX_W,  MAX_H  = 336, 82
        RADIUS = 14

        # Fixed-size spacer so surrounding layout never shifts
        spacer = tk.Frame(parent, bg=PANEL_R,
                          width=MAX_W, height=MAX_H)
        spacer.pack()
        spacer.pack_propagate(False)

        # Canvas button centered inside spacer
        cv = tk.Canvas(spacer, bg=PANEL_R,
                       highlightthickness=0, cursor="hand2")
        cv.place(relx=0.5, rely=0.5, anchor="center",
                 width=BASE_W, height=BASE_H)

        _f   = [0.0]
        _aid = [None]

        # ── Draw ──────────────────────────────────────────────
        def _draw(f):
            try:
                w = int(_lerp(BASE_W, MAX_W, f))
                h = int(_lerp(BASE_H, MAX_H, f))
                r = int(_lerp(RADIUS, RADIUS + 4, f))

                cv.place(relx=0.5, rely=0.5, anchor="center",
                         width=w, height=h)
                cv.config(width=w, height=h)
                cv.delete("all")

                # Glow border
                bord_c = _blend_hex(
                    BORDER if not is_primary else glow_c,
                    glow_c, f)
                bw = int(_lerp(1, 3, f))
                _rrect(cv, 0, 0, w, h, r + 3,
                       fill=bord_c, tags="bg")

                # Main fill
                fill = _blend_hex(bg_c, hov_c, f)
                _rrect(cv, bw, bw, w - bw, h - bw,
                       r, fill=fill, tags="bg")

                # Icon badge
                bsz   = int(_lerp(40, 46, f))
                bx    = int(_lerp(16, 18, f))
                bby   = h // 2 - bsz // 2
                badge = _darken(glow_c, _lerp(0.22, 0.40, f))
                _rrect(cv, bx, bby, bx + bsz, bby + bsz,
                       9, fill=badge, tags="fg")
                cv.create_text(
                    bx + bsz // 2, h // 2,
                    text=data["icon"],
                    font=("Segoe UI", int(_lerp(14, 17, f))),
                    fill=glow_c, tags="fg")

                # Title
                tx = bx + bsz + 14
                cv.create_text(
                    tx, h // 2 - int(_lerp(10, 12, f)),
                    text=data["title"],
                    font=("Segoe UI",
                          int(_lerp(14, 16, f)), "bold"),
                    fill=_blend_hex(TEXT, "#ffffff", f * 0.35),
                    anchor="w", tags="fg")

                # Sub
                cv.create_text(
                    tx, h // 2 + int(_lerp(10, 12, f)),
                    text=data["sub"],
                    font=("Segoe UI", int(_lerp(10, 11, f))),
                    fill=_blend_hex(TEXT3, TEXT2, f),
                    anchor="w", tags="fg")

                # Arrow
                cv.create_text(
                    w - int(_lerp(20, 18, f)), h // 2,
                    text="›",
                    font=("Segoe UI", int(_lerp(20, 26, f))),
                    fill=_blend_hex(BORDER, glow_c, f),
                    tags="fg")

            except Exception:
                pass

        # ── Smooth easing engine ──────────────────────────────
        def _animate(target):
            if _aid[0]:
                try: self.after_cancel(_aid[0])
                except: pass

            def _step():
                if not self._alive: return
                diff = target - _f[0]
                if abs(diff) < 0.025:
                    _f[0] = target
                    _draw(_f[0])
                    _aid[0] = None
                    return
                _f[0] += diff * 0.22
                _draw(_f[0])
                _aid[0] = self.after(11, _step)

            _step()

        _draw(0.0)

        # ── Bindings — spacer + canvas (100% coverage) ────────
        def on_enter(e):
            if self._alive: _animate(1.0)

        def on_leave(e):
            if self._alive: _animate(0.0)

        def on_click(e):
            if self._alive: getattr(self, data["command"])()

        for w in (cv, spacer):
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)
            w.bind("<Button-1>", on_click)

    # ══════════════════════════════════════════════════════════
    # LEFT ANIMATION — particle graph + camera ring
    # ══════════════════════════════════════════════════════════

    def _init_particles(self):
        W      = self.winfo_width()  or 1366
        H      = self.winfo_height() or 768
        left_w = int(W * 0.56)
        self._particles = [_Particle(left_w, H, i)
                           for i in range(self.N_PARTICLES)]
        self._draw_grid(left_w, H)
        self._animate()

    def _draw_grid(self, w, h):
        self.left_cv.delete("grid")
        step = 48
        for x in range(0, w + step, step):
            self.left_cv.create_line(
                x, 0, x, h,
                fill=GRID_COLOR, width=1, tags="grid")
        for y in range(0, h + step, step):
            self.left_cv.create_line(
                0, y, w, y,
                fill=GRID_COLOR, width=1, tags="grid")

    def _animate(self):
        if not self._alive or not self.winfo_exists():
            return
        try:
            W      = self.winfo_width()  or 1366
            H      = self.winfo_height() or 768
            left_w = int(W * 0.56)

            # ── Camera / scanner ring (drawn first — background) ──
            self.left_cv.delete("scanner")
            scx = int(left_w * 0.78)   # right portion of left panel
            scy = int(H * 0.38)
            sr  = int(min(left_w, H) * 0.20)

            # Outer static ring
            self.left_cv.create_oval(
                scx - sr, scy - sr, scx + sr, scy + sr,
                outline=BORDER_LIT, width=1,
                fill="", tags="scanner")

            # Middle ring (slightly smaller)
            rm = int(sr * 0.78)
            self.left_cv.create_oval(
                scx - rm, scy - rm, scx + rm, scy + rm,
                outline=ACCENT_DIM, width=1,
                fill="", tags="scanner")

            # Tick marks on outer ring
            for i in range(36):
                ang = math.radians(i * 10)
                r1  = sr
                r2  = sr - (10 if i % 9 == 0 else 5)
                col = ACCENT if i % 9 == 0 else BORDER_LIT
                self.left_cv.create_line(
                    scx + r1 * math.cos(ang),
                    scy + r1 * math.sin(ang),
                    scx + r2 * math.cos(ang),
                    scy + r2 * math.sin(ang),
                    fill=col, width=1, tags="scanner")

            # Rotating sweep arc (camera rotation)
            self._scan_angle = (self._scan_angle + 1.8) % 360
            self.left_cv.create_arc(
                scx - sr + 10, scy - sr + 10,
                scx + sr - 10, scy + sr - 10,
                start=self._scan_angle - 65,
                extent=65,
                outline=ACCENT, width=2,
                style="arc", tags="scanner")

            # Rotating bright dot on ring edge
            rad = math.radians(self._scan_angle)
            rdx = scx + (sr - 8) * math.cos(rad)
            rdy = scy + (sr - 8) * math.sin(rad)
            self.left_cv.create_oval(
                rdx - 5, rdy - 5, rdx + 5, rdy + 5,
                fill=ACCENT2, outline="", tags="scanner")

            # Counter-rotating dot (opposite direction)
            rad2 = math.radians(-self._scan_angle * 0.6)
            rdx2 = scx + rm * math.cos(rad2)
            rdy2 = scy + rm * math.sin(rad2)
            self.left_cv.create_oval(
                rdx2 - 3, rdy2 - 3, rdx2 + 3, rdy2 + 3,
                fill=PARTICLE_A, outline="", tags="scanner")

            # Inner pulse ring
            t  = time.time()
            pr = int(sr * 0.42 * (0.88 + 0.12 * math.sin(t * 2.8)))
            self.left_cv.create_oval(
                scx - pr, scy - pr, scx + pr, scy + pr,
                outline=_dim(ACCENT, 90),
                width=1, fill="", tags="scanner")

            # Center camera icon
            self.left_cv.create_text(
                scx, scy, text="◈",
                font=("Segoe UI", int(sr * 0.42), "bold"),
                fill=ACCENT, tags="scanner")

            # ── Particle graph ────────────────────────────────
            self.left_cv.delete("particle")

            # Pulse update
            self._pulse_a += 0.010 * self._pulse_dir
            if self._pulse_a >= 1:   self._pulse_dir = -1
            elif self._pulse_a <= 0: self._pulse_dir =  1

            # Glow rings behind particles
            cx, cy = left_w // 2, H // 2
            ring_cols = [ACCENT_DIM, "#001830",
                         "#0d0020", "#050a10", "#020508"]
            for i, col in enumerate(ring_cols, 1):
                r = 90 + i * 60
                self.left_cv.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    outline=col, width=1, tags="particle")

            # Move particles
            for p in self._particles:
                p.move()

            pts = [(p.x, p.y, p.color) for p in self._particles]

            # Connecting lines
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    dx = pts[j][0] - pts[i][0]
                    dy = pts[j][1] - pts[i][1]
                    d  = math.hypot(dx, dy)
                    if d < self.CONNECT_DIST:
                        alpha = int(180 * (1 - d / self.CONNECT_DIST))
                        self.left_cv.create_line(
                            pts[i][0], pts[i][1],
                            pts[j][0], pts[j][1],
                            fill=_dim(LINE_COLOR, alpha),
                            width=1, tags="particle")

            # Dots
            for p in self._particles:
                self.left_cv.create_oval(
                    p.x - p.r, p.y - p.r,
                    p.x + p.r, p.y + p.r,
                    fill=p.color, outline="", tags="particle")

            self._after_id = self.after(30, self._animate)

        except Exception:
            pass

    # ── Bottom bar ────────────────────────────────────────────

    def _build_bottombar(self):
        ctk.CTkFrame(self, height=1, fg_color=BORDER,
                     corner_radius=0).place(x=0, rely=1.0, y=-40, relwidth=1)
        bar = ctk.CTkFrame(self, fg_color=(BG2, BG2),
                           corner_radius=0, height=40)
        bar.place(x=0, rely=1.0, y=-40, relwidth=1)
        bar.pack_propagate(False)
        bar.lift()
        ctk.CTkLabel(bar,
            text=f"◈  {INSTITUTION}  ·  Smart Attendance System  ·  v2.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT3).pack(expand=True)

    # ── Clock ─────────────────────────────────────────────────

    def _update_clock(self):
        if not self._alive or not self.winfo_exists(): return
        try:
            self.clock_lbl.configure(
                text=datetime.now().strftime(
                    "%A, %d %B %Y   %I:%M:%S %p"))
            self.after(1000, self._update_clock)
        except Exception:
            pass

    # ── Resize ────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget != self or not self._alive: return
        W, H = self.winfo_width(), self.winfo_height()
        if abs(W - self._last_w) < 10 and abs(H - self._last_h) < 10: return
        self._last_w, self._last_h = W, H
        left_w = int(W * 0.56)
        try:
            self._draw_grid(left_w, H)
            for p in self._particles:
                p.resize(left_w, H)
        except Exception:
            pass

    # ── Navigation ────────────────────────────────────────────

    def _open_face_scanner(self):
        if not NavigationLock.acquire(): return
        def _do():
            try:
                from views.face_scanner import FaceScanner
                self.withdraw()
                FaceScanner(on_close=self._show_self)
            except Exception as e:
                print(f"Error: {e}")
                NavigationLock.release(); self._show_self()
        PageTransition.fade_out(self, on_done=_do)

    def _open_student_portal(self):
        if not NavigationLock.acquire(): return
        def _do():
            try:
                from views.student_portal import StudentPortal
                self.withdraw()
                StudentPortal(on_close=self._show_self)
            except Exception as e:
                print(f"Error: {e}")
                NavigationLock.release(); self._show_self()
        PageTransition.fade_out(self, on_done=_do)

    def _open_admin_login(self):
        if not NavigationLock.acquire(): return
        def _do():
            try:
                from views.admin_login import AdminLogin
                self.withdraw()
                AdminLogin(on_close=self._show_self, master=self.master)
            except Exception as e:
                print(f"Error: {e}")
                NavigationLock.release(); self._show_self()
        PageTransition.fade_out(self, on_done=_do)

    def _show_self(self):
        NavigationLock.release()
        try:
            self.deiconify(); self.lift(); self.focus_force()
            PageTransition.slide_in(self, direction="left")
        except Exception:
            pass

    # ── Theme ─────────────────────────────────────────────────

    def _toggle_theme(self):
        ThemeManager.toggle()

    def _refresh_theme(self):
        if not self._alive: return
        try:
            if hasattr(self, "theme_btn") and self.theme_btn.winfo_exists():
                self.theme_btn.configure(
                    text="☀ Light" if ThemeManager.current_mode == "dark"
                    else "☾ Dark")
        except Exception:
            pass

    # ── Cleanup ───────────────────────────────────────────────

    def _cancel_all_afters(self):
        try:
            ids = self.tk.call('after', 'info')
            if isinstance(ids, str): ids = ids.split()
            for aid in ids:
                try: self.after_cancel(aid)
                except: pass
        except Exception:
            pass

    def _on_close(self):
        self._alive = False
        ThemeManager.unregister(self._refresh_theme)
        NavigationLock.release()
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except: pass
        self._cancel_all_afters()
        try:
            if self.master: self.master.destroy()
            else: self.destroy()
        except Exception:
            pass
