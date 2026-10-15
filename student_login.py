# ============================================================
# student_login.py — Student Login Page  (Redesigned)
# ============================================================

import customtkinter as ctk
import tkinter as tk
import math
import random

from models.user_model import validate_student_login
from config import APP_NAME
from transitions import PageTransition, NavigationLock


# ── Colour palette ─────────────────────────────────────────────────────────────
BG          = "#0d1117"       # Main Background  — Dark Navy
CARD_BG     = "#0d121f"       # Card Background  — Dark Glass
NAV_BG      = "#161b22"       # Navbar / Secondary BG
SIDEBAR_BG  = "#0a0e1a"       # Sidebar / deep dark

ACCENT      = "#00d2ff"       # Primary Accent   — Vibrant Cyan
ACCENT_DIM  = "#005f74"       # Dim cyan for glow borders
ACCENT2     = "#7c3aed"       # Secondary Accent — Electric Purple
ACCENT3     = "#0ea5e9"       # Tertiary Accent  — Sky Blue

SUCCESS     = "#4ade80"       # Mint Green
DANGER      = "#f87171"       # Coral Red

TEXT_PRI    = "#f8fafc"       # Ghost White
TEXT_MUT    = "#94a3b8"       # Steel Blue / muted
TEXT_DIMMER = "#484f58"       # Very muted border-area text

INPUT_BG    = "#0a0e1a"
INPUT_FG    = ACCENT
INPUT_BORD  = "#1e2d3d"
INPUT_ACT   = ACCENT

BTN_BG      = ACCENT
BTN_FG      = "#0d1117"
BTN_HOV     = "#00a8cc"

PARTICLE_A  = ACCENT
PARTICLE_B  = ACCENT2
LINE_COLOR  = "#0a3040"
GRID_COLOR  = "#111820"


# ══════════════════════════════════════════════════════════════════════════════
class _Particle:
    """Floating dot for background animation."""

    def __init__(self, w, h, idx):
        self.w, self.h = w, h
        self.x  = random.uniform(0, w)
        self.y  = random.uniform(0, h)
        self.vx = random.uniform(-0.40, 0.40)
        self.vy = random.uniform(-0.40, 0.40)
        self.r  = random.uniform(1.8, 3.2)
        self.color = PARTICLE_A if idx % 4 != 0 else PARTICLE_B

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > self.w: self.vx *= -1
        if self.y < 0 or self.y > self.h: self.vy *= -1

    def resize(self, w, h):
        self.w, self.h = w, h


# ══════════════════════════════════════════════════════════════════════════════
class StudentLoginFrame(tk.Frame):
    """
    Animated background + login card — pure tkinter layer.
    All backend calls are forwarded to on_success / on_back callbacks.
    """

    CONNECT_DIST = 140
    N_PARTICLES  = 70

    def __init__(self, master, on_success=None, on_back=None, **kw):
        super().__init__(master, bg=BG, **kw)
        self.on_success     = on_success or (lambda u: None)
        self.on_back        = on_back    or (lambda: None)

        self._pulse_dir     = 1
        self._pulse_alpha   = 0.0
        self._particles     = []
        self._after_id      = None
        self._finalize_after_id = None
        self._last_w        = 0
        self._last_h        = 0
        self._scale         = 1.0
        self._checking      = False

        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    # ── responsive font ───────────────────────────────────────────────────────
    def _f(self, size, weight="normal"):
        return ("Segoe UI", max(8, int(size * self._scale)), weight)

    # ── rounded rectangle helper ──────────────────────────────────────────────
    def _rrect(self, canvas, x1, y1, x2, y2, r, fill="", tags=""):
        """
        Filled rounded rectangle via 2 overlapping rects + 4 arc corners.
        Outline intentionally omitted for clean layered stacking.
        """
        r    = max(1, r)
        opts = dict(fill=fill, outline="", tags=tags)
        canvas.create_rectangle(x1 + r, y1,     x2 - r, y2,     **opts)
        canvas.create_rectangle(x1,     y1 + r, x2,     y2 - r, **opts)
        canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90, style="pieslice", **opts)
        canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90, style="pieslice", **opts)
        canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90, style="pieslice", **opts)
        canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, style="pieslice", **opts)

    # ── layout skeleton ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Animated canvas (fills whole window, sits behind everything)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ← Back button — fixed top-left
        self.back_btn = tk.Label(
            self, text="←  Back",
            bg=BG, fg=TEXT_MUT, cursor="hand2",
            font=("Segoe UI", 11, "bold"),
        )
        self.back_btn.place(x=22, y=18)
        self.back_btn.bind("<Enter>",    lambda e: self.back_btn.config(fg=ACCENT))
        self.back_btn.bind("<Leave>",    lambda e: self.back_btn.config(fg=TEXT_MUT))
        self.back_btn.bind("<Button-1>", lambda e: self.on_back())

        # Centre overlay — card lives here, stays fixed at centre
        self.overlay = tk.Frame(self, bg=BG)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        self._build_card()
        self.after(120, self._init_particles)

    # ── card (rebuilt on resize) ──────────────────────────────────────────────
    def _build_card(self):
        for w in self.overlay.winfo_children():
            w.destroy()

        s             = self._scale
        pad_x         = int(38 * s)
        pad_y         = int(26 * s)
        bord          = 3
        self._card_r  = int(16 * s)
        self._card_px = pad_x
        self._card_py = pad_y

        # Canvas bg=BG: rounded corners cut through to main background
        self._card_cv = tk.Canvas(
            self.overlay, bg=BG, highlightthickness=0
        )
        self._card_cv.pack()

        # Content frame placed inside canvas
        content = tk.Frame(self._card_cv, bg=CARD_BG)
        self._card_content = content
        self._card_win_id  = self._card_cv.create_window(
            bord + pad_x, bord + pad_y, anchor="nw", window=content
        )

        self._populate_card(content, s)

        # Finalise after geometry settles
        if self._finalize_after_id:
            try:
                self.after_cancel(self._finalize_after_id)
            except Exception:
                pass
        self._finalize_after_id = self.after(20, self._finalize_card)

    def _finalize_card(self):
        """Measure content, size canvas, draw rounded glow layers."""
        if not self.winfo_exists():
            return
        
        if not hasattr(self, '_card_cv') or not hasattr(self, '_card_content'):
            return

        c    = self._card_cv
        cont = self._card_content
        r    = self._card_r
        px   = self._card_px
        py   = self._card_py
        bord = 3
        if not c.winfo_exists() or not cont.winfo_exists():
            return

        try:
            cont.update_idletasks()
            if not c.winfo_exists() or not cont.winfo_exists():
                return
            
            fw = cont.winfo_reqwidth()
            fh = cont.winfo_reqheight()

            cw = fw + 2 * px + 2 * bord
            ch = fh + 2 * py + 2 * bord

            c.config(width=cw, height=ch)
            c.coords(self._card_win_id, bord + px, bord + py)

            # Layered rounded rects — back to front
            c.delete("card_bg")
            self._rrect(c, 0,    0,    cw,      ch,      r+4, fill=ACCENT2,    tags="card_bg")
            self._rrect(c, 2,    2,    cw-2,    ch-2,    r+2, fill=ACCENT_DIM, tags="card_bg")
            self._rrect(c, bord, bord, cw-bord, ch-bord, r,   fill=CARD_BG,    tags="card_bg")

            c.tag_raise(self._card_win_id)
        except tk.TclError:
            pass

    # ── card content ──────────────────────────────────────────────────────────
    def _populate_card(self, card, s):

        # ── Icon ring ─────────────────────────────────────────────────────────
        ico_sz = int(60 * s)
        lc = tk.Canvas(card, width=ico_sz, height=ico_sz,
                       bg=CARD_BG, highlightthickness=0)
        lc.pack(pady=(0, int(5 * s)))
        cx = cy = ico_sz // 2
        r2 = int(27 * s)
        lc.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                       outline=ACCENT2, fill="", width=2)
        hr = int(19 * s)
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts.extend([cx + hr * math.cos(a), cy + hr * math.sin(a)])
        lc.create_polygon(pts, outline=ACCENT, fill="", width=2)
        lc.create_text(cx, cy, text="S", fill=ACCENT,
                       font=("Segoe UI", int(17 * s), "bold"))

        # ── Title ─────────────────────────────────────────────────────────────
        tk.Label(
            card, text="Student Portal",
            bg=CARD_BG, fg=TEXT_PRI,
            font=("Segoe UI", int(19 * s), "bold"),
        ).pack(pady=(0, int(2 * s)))

        tk.Label(
            card, text="Sign in with your Roll Number & Full Name",
            bg=CARD_BG, fg=TEXT_DIMMER,
            font=("Segoe UI", int(9 * s)),
        ).pack()

        # Divider
        div_frame = tk.Frame(card, bg=CARD_BG)
        div_frame.pack(fill="x", pady=(int(12 * s), int(14 * s)))
        tk.Frame(div_frame, bg=ACCENT2, height=1).pack(
            fill="x", padx=int(6 * s))

        # ── Fields ────────────────────────────────────────────────────────────
        self._build_field(card, "ROLL NUMBER", False,
                          placeholder="e.g.  2021-CS-001")
        tk.Frame(card, bg=CARD_BG, height=int(12 * s)).pack()
        self._build_field(card, "FULL NAME", False,
                          placeholder="Name used during registration",
                          is_name=True)
        tk.Frame(card, bg=CARD_BG, height=int(4 * s)).pack()

        # ── Status / error label ──────────────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        tk.Label(
            card, textvariable=self.status_var,
            bg=CARD_BG, fg=DANGER,
            font=("Segoe UI", int(9 * s)),
            wraplength=int(290 * s),
        ).pack(pady=(int(6 * s), int(6 * s)))

        # ── Rounded login button ──────────────────────────────────────────────
        self._build_rounded_btn(card, s)

        self.bind_all("<Return>", lambda e: self._attempt_login())

    # ── rounded canvas button ─────────────────────────────────────────────────
    def _build_rounded_btn(self, parent, s):
        bw = int(300 * s)
        bh = int(42 * s)
        br = int(11 * s)

        self._btn_w       = bw
        self._btn_h       = bh
        self._btn_r       = br
        self._btn_s       = s
        self._btn_label   = "Login  →"
        self._btn_bg      = BTN_BG
        self._btn_enabled = True

        btn_wrap = tk.Frame(parent, bg=CARD_BG)
        btn_wrap.pack(fill="x", pady=(0, int(2 * s)))

        self._btn_cv = tk.Canvas(
            btn_wrap, width=bw, height=bh,
            bg=CARD_BG, highlightthickness=0, cursor="hand2",
        )
        self._btn_cv.pack()

        self._redraw_btn()

        self._btn_cv.bind("<Enter>",    lambda e: self._btn_hover(True))
        self._btn_cv.bind("<Leave>",    lambda e: self._btn_hover(False))
        self._btn_cv.bind("<Button-1>", lambda e: (
            self._attempt_login() if self._btn_enabled else None
        ))

    def _redraw_btn(self, hover=False):
        if not hasattr(self, "_btn_cv"):
            return
        c  = self._btn_cv
        bw = self._btn_w
        bh = self._btn_h
        br = self._btn_r
        s  = self._btn_s

        if not self._btn_enabled:
            bg = "#1a3040"
        elif hover:
            bg = BTN_HOV
        else:
            bg = self._btn_bg

        c.delete("all")
        self._rrect(c, 0, 0, bw, bh, br, fill=bg, tags="btn")
        c.create_text(
            bw // 2, bh // 2,
            text=self._btn_label,
            fill=BTN_FG,
            font=("Segoe UI", int(12 * s), "bold"),
            tags="btn",
        )

    def _btn_hover(self, entering):
        if self._btn_enabled:
            self._redraw_btn(hover=entering)

    def _set_btn(self, text, bg=None, enabled=True):
        self._btn_label   = text
        self._btn_bg      = bg or BTN_BG
        self._btn_enabled = enabled
        self._redraw_btn()

    # ── Login logic (backend UNCHANGED) ──────────────────────────────────────
    def _attempt_login(self):
        if self._checking:
            return

        roll = self.roll_entry.get().strip()
        name = self.name_entry.get().strip()

        if roll == getattr(self, "_roll_ph", ""):
            roll = ""
        if name == getattr(self, "_name_ph", ""):
            name = ""

        if not roll or not name:
            self.status_var.set("⚠  Please enter both Roll Number and Full Name.")
            return

        self._checking = True
        self._set_btn("⏳  Checking…", BTN_BG, enabled=False)
        self.status_var.set("")

        user, err = validate_student_login(roll, name)

        if err:
            self.status_var.set(f"✖  {err}")
            self._set_btn("Login  →", BTN_BG, enabled=True)
            self._checking = False
        else:
            self.status_var.set("")
            self._set_btn("✔  Access Granted", SUCCESS, enabled=False)
            self.after(700, lambda: self.on_success(user))

    # ── Input fields (logic unchanged) ────────────────────────────────────────
    def _build_field(self, parent, label_text, is_password,
                     placeholder="", is_name=False):
        s = self._scale

        tk.Label(
            parent, text=label_text,
            bg=CARD_BG, fg=TEXT_MUT,
            font=("Segoe UI", int(9 * s), "bold"),
            anchor="w",
        ).pack(anchor="w")

        border = tk.Frame(parent, bg=INPUT_BORD, padx=1, pady=1)
        border.pack(fill="x", pady=(int(5 * s), 0))

        inner = tk.Frame(border, bg=INPUT_BG)
        inner.pack(fill="x")

        entry = tk.Entry(
            inner,
            bg=INPUT_BG, fg=INPUT_FG,
            insertbackground=ACCENT,
            relief="flat",
            font=("Segoe UI", int(12 * s)),
            show="•" if is_password else "",
            bd=int(9 * s),
            highlightthickness=0,
            width=28,
        )
        entry.pack(fill="x")

        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_DIMMER)

            def _on_focus_in(e, ph=placeholder, en=entry, bo=border):
                if en.get() == ph:
                    en.delete(0, "end")
                    en.config(fg=INPUT_FG)
                bo.config(bg=INPUT_ACT)

            def _on_focus_out(e, ph=placeholder, en=entry, bo=border):
                if not en.get():
                    en.insert(0, ph)
                    en.config(fg=TEXT_DIMMER)
                bo.config(bg=INPUT_BORD)

            entry.bind("<FocusIn>",  _on_focus_in)
            entry.bind("<FocusOut>", _on_focus_out)
        else:
            entry.bind("<FocusIn>",
                       lambda e, bo=border: bo.config(bg=INPUT_ACT))
            entry.bind("<FocusOut>",
                       lambda e, bo=border: bo.config(bg=INPUT_BORD))

        inner.bind("<Enter>", lambda e, bo=border: bo.config(bg=ACCENT3))
        inner.bind("<Leave>",
                   lambda e, bo=border: bo.config(
                       bg=INPUT_ACT if entry == self.focus_get()
                       else INPUT_BORD))
        entry.bind("<Enter>", lambda e, bo=border: bo.config(bg=ACCENT3))
        entry.bind("<Leave>",
                   lambda e, bo=border: (
                       bo.config(bg=INPUT_BORD)
                       if entry.focus_get() != entry else None
                   ))

        if is_name:
            self.name_entry = entry
            self._name_ph   = placeholder
        else:
            self.roll_entry = entry
            self._roll_ph   = placeholder

    # ── Responsive resize ─────────────────────────────────────────────────────
    def _on_resize(self, event):
        w, h = event.width, event.height
        if abs(w - self._last_w) < 6 and abs(h - self._last_h) < 6:
            return
        self._last_w, self._last_h = w, h
        self._scale = max(0.70, min(1.55, w / 1080))
        self._build_card()
        self.canvas.delete("grid")
        self._draw_grid(w, h)
        for p in self._particles:
            p.resize(w, h)

    # ── Particle / animation engine (UNCHANGED) ───────────────────────────────
    def _init_particles(self):
        w = self.winfo_width()  or 1080
        h = self.winfo_height() or 680
        self._particles = [_Particle(w, h, i) for i in range(self.N_PARTICLES)]
        self._draw_grid(w, h)
        self._animate()

    def _draw_grid(self, w, h):
        step = 48
        for x in range(0, w + step, step):
            self.canvas.create_line(x, 0, x, h,
                                    fill=GRID_COLOR, width=1, tags="grid")
        for y in range(0, h + step, step):
            self.canvas.create_line(0, y, w, y,
                                    fill=GRID_COLOR, width=1, tags="grid")

    def _animate(self):
        self.canvas.delete("particle")
        w = self.winfo_width()  or 1080
        h = self.winfo_height() or 680

        self._pulse_alpha += 0.010 * self._pulse_dir
        if self._pulse_alpha >= 1:   self._pulse_dir = -1
        elif self._pulse_alpha <= 0: self._pulse_dir =  1

        cx, cy = w // 2, h // 2
        ring_colors = [ACCENT_DIM, "#001830", "#0d0020", "#050a10", "#020508"]
        for i, col in enumerate(ring_colors, 1):
            r = 120 + i * 70
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    outline=col, width=1, tags="particle")

        for p in self._particles:
            p.move()

        pts = [(p.x, p.y, p.color) for p in self._particles]

        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx = pts[j][0] - pts[i][0]
                dy = pts[j][1] - pts[i][1]
                d  = math.hypot(dx, dy)
                if d < self.CONNECT_DIST:
                    alpha = int(180 * (1 - d / self.CONNECT_DIST))
                    self.canvas.create_line(
                        pts[i][0], pts[i][1],
                        pts[j][0], pts[j][1],
                        fill=self._blend(LINE_COLOR, alpha),
                        width=1, tags="particle",
                    )

        for p in self._particles:
            self.canvas.create_oval(
                p.x - p.r, p.y - p.r,
                p.x + p.r, p.y + p.r,
                fill=p.color, outline="", tags="particle",
            )

        self._after_id = self.after(33, self._animate)

    @staticmethod
    def _blend(hex_col, alpha):
        r1 = int(hex_col[1:3], 16)
        g1 = int(hex_col[3:5], 16)
        b1 = int(hex_col[5:7], 16)
        a  = alpha / 255
        return "#{:02x}{:02x}{:02x}".format(
            int(r1 * a + 0x0d * (1 - a)),
            int(g1 * a + 0x11 * (1 - a)),
            int(b1 * a + 0x17 * (1 - a)),
        )

    def destroy(self):
        if self._finalize_after_id:
            try:
                self.after_cancel(self._finalize_after_id)
            except Exception:
                pass
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        super().destroy()


# ══════════════════════════════════════════════════════════════════════════════
class StudentLogin(ctk.CTkToplevel):
    """
    Student Login Window — movable & minimizable via OS title bar.
    Backend logic (validate_student_login) is untouched.
    """

    def __init__(self, on_close=None):
        super().__init__()
        PageTransition.prepare_window(self)

        self.on_close = on_close
        self.title(f"{APP_NAME} — Student Login")

        # Maximized but NOT fullscreen — keeps OS title bar so the window
        # can be moved, minimized and restored with standard system controls.
        self.state("zoomed")
        self.configure(fg_color=BG)

        self.frame = StudentLoginFrame(
            self,
            on_success=self._open_dashboard,
            on_back=self._on_close,
        )
        self.frame.pack(fill="both", expand=True)

        PageTransition.fade_in(self, steps=12, ms=18)

    def _open_dashboard(self, user):
        from views.student_dashboard import StudentDashboard

        def _do_open():
            NavigationLock.release()
            self.destroy()
            win = StudentDashboard(user=user, on_close=self.on_close)

        PageTransition.fade_out(self, on_done=_do_open, steps=10, ms=15)

    def _on_close(self):
        def _do_close():
            NavigationLock.release()
            self.destroy()
            if self.on_close:
                self.on_close()

        PageTransition.fade_out(self, on_done=_do_close, steps=8, ms=18)

    def destroy(self):
        if hasattr(self, "frame"):
            self.frame.destroy()
        super().destroy()