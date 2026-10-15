# ============================================================
# student_dashboard.py — Animated Student Dashboard
# ============================================================

import customtkinter as ctk
import tkinter as tk
import random
import threading
import time
from database.db_connection import execute_query
from models.routine_model import search_routines_for_student
from config import APP_NAME


# ── Day ordering & accent colors ─────────────────────────────
DAY_COLOR = {
    "Sunday":    "#28db5e",
    "Monday":    "#3b82f6",
    "Tuesday":   "#10b981",
    "Wednesday": "#8b5cf6",
    "Thursday":  "#f59e0b",
    "Friday":    "#ef4444",
    "Saturday":  "#06b6d4",
}
DAYS_ORDER = ["Sunday", "Monday", "Tuesday", "Wednesday",
              "Thursday", "Friday", "Saturday"]

# ── Palette ──────────────────────────────────────────────────
BG = "#0a0e1a"
SURFACE = "#111827"
SURFACE2 = "#1a2235"
BORDER = "#1e3058"
TEXT_PRI = "#e2e8f0"
TEXT_SEC = "#94a3b8"
TEXT_MUT = "#475569"
BLUE = "#3b82f6"
BLUE_DIM = "#1d4ed8"
BLUE_TXT = "#93c5fd"
AMBER = "#f59e0b"
GREEN = "#10b981"
RED = "#ef4444"
HOVER_GLOW = "#38bdf8"
HOVER_SURFACE = "#1f2a40"
HOVER_ROW = "#162033"

STAR_COLORS = ["#93c5fd", "#c4b5fd", "#6ee7b7", "#fde68a", "#f9a8d4"]
GLOW_COLORS = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981"]

# ── Fixed column widths ───────────────────────────────────────
# Attendance table
ATT_COLS = ["Subject",  "Total", "Attended", "%",   "Dates Attended"]
ATT_WIDTHS = [200,         60,      70,          55,    280]
ATT_PAD0 = 14   # left-most column left-pad
ATT_PADX = 8    # rest

# Routine table
ROU_COLS = ["#", "Subject",  "Teacher",  "Class Time",  "Shift"]
ROU_WIDTHS = [28,   220,        160,         160,           80]
ROU_PAD0 = 10
ROU_PADX = 6


# ══════════════════════════════════════════════════════════════
# DB helpers
# ══════════════════════════════════════════════════════════════

def get_student_attendance(user_id: int, department: str, semester: str, shift: str):
    rows = execute_query(
        """SELECT s.subject,
               COUNT(DISTINCT s.id) AS total_classes,
               COUNT(DISTINCT CASE WHEN r.status='complete' THEN r.id END) AS attended,
               GROUP_CONCAT(
                   DISTINCT CASE WHEN r.status='complete'
                   THEN DATE_FORMAT(s.session_date,'%%d %%b') END
                   ORDER BY s.session_date SEPARATOR ', '
               ) AS attended_dates
           FROM attendance_sessions s
           JOIN routines ro ON s.routine_id = ro.id
           LEFT JOIN attendance_records r
               ON r.session_id=s.id AND r.user_id=%s
           WHERE s.status='closed'
             AND ro.department=%s
             AND ro.semester=%s
             AND ro.shift=%s
           GROUP BY s.subject ORDER BY s.subject""",
        (user_id, department, semester, shift), fetch="all"
    )
    return rows or []


def _td_to_hhmm(val):
    if val is None:
        return "—"
    if hasattr(val, "total_seconds"):
        t = int(val.total_seconds())
        h, m = t // 3600, (t % 3600) // 60
    else:
        h, m = val.hour, val.minute
    from datetime import datetime as _dt
    return _dt(2000, 1, 1, h % 24, m % 60).strftime("%I:%M %p")


# ══════════════════════════════════════════════════════════════
# Helpers — fixed-width grid row builder
# ══════════════════════════════════════════════════════════════

def _grid_row(parent, cells, widths, pad0, padx, pady=7):
    """
    Place labels in a grid row with strictly fixed column widths.
    cells  : list of (text, text_color)
    widths : list of int pixel widths
    """
    for col_idx, ((text, color), width) in enumerate(zip(cells, widths)):
        lx = pad0 if col_idx == 0 else padx
        ctk.CTkLabel(
            parent,
            text=text,
            width=width,
            font=ctk.CTkFont(family="Segoe UI",
                             size=11 if col_idx == 0 and width < 40 else 12),
            text_color=(color, color),
            anchor="w",
            wraplength=width - 4,
        ).grid(row=0, column=col_idx,
               padx=(lx, 0), pady=pady, sticky="w")


def _grid_header(parent, cols, widths, pad0, padx):
    """Header row — bold, TEXT_MUT color."""
    for col_idx, (h, width) in enumerate(zip(cols, widths)):
        lx = pad0 if col_idx == 0 else padx
        ctk.CTkLabel(
            parent,
            text=h,
            width=width,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUT,
            anchor="w",
        ).grid(row=0, column=col_idx,
               padx=(lx, 0), pady=8, sticky="w")


# ══════════════════════════════════════════════════════════════
# Starfield canvas
# ══════════════════════════════════════════════════════════════

def _blend(hex_fg: str, alpha: float) -> str:
    def p(h):
        h = h.lstrip("#")
        return int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    fr, fg_, fb = p(hex_fg)
    br, bg_, bb = p(BG)
    return "#{:02x}{:02x}{:02x}".format(
        int(br + (fr - br) * alpha),
        int(bg_ + (fg_ - bg_) * alpha),
        int(bb + (fb - bb) * alpha),
    )


class StarCanvas(tk.Canvas):
    N_STARS = 130
    INTERVAL = 36

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self._stars = []
        self._glows = []
        self._active = False
        self.bind("<Configure>", self._on_resize)

    def start(self):
        if self._active:
            return
        self._active = True
        self._init_stars()
        self._tick()

    def stop(self):
        self._active = False

    def _init_stars(self):
        w = max(self.winfo_width(), 860)
        h = max(self.winfo_height(), 700)
        self._stars = [{
            "x":  random.uniform(0, w),
            "y":  random.uniform(0, h),
            "r":  random.uniform(0.5, 1.6),
            "a":  random.random(),
            "da": random.uniform(0.005, 0.015) * random.choice([-1, 1]),
            "vy": random.uniform(0.04, 0.20),
            "c":  random.choice(STAR_COLORS),
        } for _ in range(self.N_STARS)]

    def _on_resize(self, _e):
        self._init_stars()

    def _tick(self):
        if not self._active or not self.winfo_exists():
            return
        w = max(self.winfo_width(), 860)
        h = max(self.winfo_height(), 700)
        self.delete("all")

        for s in self._stars:
            s["a"] += s["da"]
            if s["a"] > 1 or s["a"] < 0:
                s["da"] *= -1
            s["y"] -= s["vy"]
            if s["y"] < 0:
                s["y"] = h
                s["x"] = random.uniform(0, w)
            a = max(0.0, min(1.0, s["a"]))
            col = _blend(s["c"], a)
            r = s["r"]
            self.create_oval(s["x"] - r, s["y"] - r,
                             s["x"] + r, s["y"] + r,
                             fill=col, outline="")

        if random.random() < 0.12:
            self._glows.append({
                "x":    random.uniform(0, w), "y": h + 4,
                "r":    random.uniform(1.2, 2.6), "life": 1.0,
                "vy":   random.uniform(0.35, 0.8),
                "vx":   random.uniform(-0.18, 0.18),
                "c":    random.choice(GLOW_COLORS),
            })

        nxt = []
        for g in self._glows:
            g["x"] += g["vx"]
            g["y"] -= g["vy"]
            g["life"] -= 0.006
            if g["life"] <= 0:
                continue
            col = _blend(g["c"], g["life"] * 0.65)
            r = g["r"]
            self.create_oval(g["x"] - r, g["y"] - r,
                             g["x"] + r, g["y"] + r,
                             fill=col, outline="")
            nxt.append(g)
        self._glows = nxt
        self.after(self.INTERVAL, self._tick)


# ══════════════════════════════════════════════════════════════
# Student Dashboard Window
# ══════════════════════════════════════════════════════════════

class StudentDashboard(ctk.CTkToplevel):

    def __init__(self, user: dict, on_close=None):
        super().__init__()
        self.user = user
        self.on_close = on_close
        self._star_cv = None
        self._pulse_step = 0

        self.title(f"{APP_NAME} — Student Dashboard")
        self.geometry("860x700")
        self.minsize(720, 540)
        self.resizable(True, True)
        self._center_window(860, 700)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.lift()
        self.focus_force()

    # ── hover binders ─────────────────────────────────────────

    def _bind_card_hover(self, widget, base_bg,
                         hover_bg=HOVER_SURFACE,
                         base_border=BORDER,
                         hover_border=HOVER_GLOW):
        def _enter(_e): widget.configure(
            fg_color=hover_bg, border_color=hover_border)

        def _leave(_e): widget.configure(
            fg_color=base_bg,  border_color=base_border)
        widget.bind("<Enter>", _enter)
        widget.bind("<Leave>", _leave)

    def _bind_button_hover(self, btn, normal_fg, hover_fg,
                           normal_text=TEXT_SEC, hover_text=TEXT_PRI):
        def _enter(_e): btn.configure(fg_color=hover_fg,
                                      text_color=hover_text,  border_color=HOVER_GLOW)

        def _leave(_e): btn.configure(fg_color=normal_fg,
                                      text_color=normal_text, border_color=BORDER)
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    def _bind_nav_hover(self, widget,
                        normal_bg=SURFACE, hover_bg=SURFACE2,
                        normal_text=TEXT_SEC, hover_text=TEXT_PRI):
        def _enter(_e): widget.configure(fg_color=hover_bg,
                                         text_color=hover_text,  border_color=HOVER_GLOW)
        def _leave(_e): widget.configure(fg_color=normal_bg,
                                         text_color=normal_text, border_color=BORDER)
        widget.bind("<Enter>", _enter)
        widget.bind("<Leave>", _leave)

    def _bind_row_hover(self, row_frame, normal_bg, hover_bg=HOVER_ROW):
        def _enter(_e): row_frame.configure(fg_color=(hover_bg, hover_bg))
        def _leave(_e): row_frame.configure(fg_color=(normal_bg, normal_bg))
        row_frame.bind("<Enter>", _enter)
        row_frame.bind("<Leave>", _leave)
        return _enter, _leave

    # ── layout ────────────────────────────────────────────────

    def _build_ui(self):
        # Starfield
        self._star_cv = StarCanvas(self)
        self._star_cv.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        tk.Misc.lower(self._star_cv)
        self._star_cv.start()

        # Header
        hdr_wrap = tk.Frame(self, bg=BG, height=60)
        hdr_wrap.pack(fill="x", padx=14, pady=(10, 0))
        hdr_wrap.pack_propagate(False)

        hdr = ctk.CTkFrame(hdr_wrap, fg_color=SURFACE,
                           corner_radius=12, border_width=1, border_color=BORDER)
        hdr.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        logout_btn = ctk.CTkButton(
            hdr, text="← Logout", width=84, height=30,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=TEXT_SEC, hover_color=SURFACE2,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._on_close,
        )
        logout_btn.place(x=14, rely=0.5, anchor="w")
        self._bind_nav_hover(
            logout_btn, normal_bg="transparent", hover_bg=SURFACE2)

        ctk.CTkLabel(
            hdr, text="My Dashboard",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRI,
        ).place(relx=0.5, rely=0.5, anchor="center")

        refresh_btn = ctk.CTkButton(
            hdr, text="↻  Refresh", width=90, height=30,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=TEXT_SEC, hover_color=SURFACE2,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._refresh,
        )
        refresh_btn.place(relx=1.0, x=-14, rely=0.5, anchor="e")
        self._bind_button_hover(
            refresh_btn, normal_fg="transparent", hover_fg=SURFACE2)

        # Scroll body
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_fg_color=SURFACE2)
        self._scroll.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        self._populate_body()

    def _populate_body(self):
        self._build_info_card()
        self._section_label("📊  Subject-wise Attendance")
        self._build_attendance_table()
        self._section_label(
            f"📅  My Class Routine  "
            f"({self.user.get('department','—')}  •  "
            f"{self.user.get('semester','—')} Semester  •  "
            f"{str(self.user.get('shift','')).title()} Shift)"
        )
        self._build_routine_section()

    def _section_label(self, text: str):
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=(16, 6))
        ctk.CTkLabel(
            row, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_PRI, anchor="w",
        ).pack(side="left")
        ctk.CTkFrame(row, height=1, fg_color=BORDER,
                     ).pack(side="left", fill="x", expand=True, padx=(10, 0))

    # ── Info Card ─────────────────────────────────────────────

    def _build_info_card(self):
        card = ctk.CTkFrame(self._scroll, fg_color=SURFACE,
                            corner_radius=14, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=2, pady=(10, 4))
        self._bind_card_hover(card, base_bg=SURFACE)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # Avatar + pulse ring
        av_wrap = ctk.CTkFrame(inner, width=60, height=60,
                               fg_color="transparent", corner_radius=30)
        av_wrap.pack(side="left", padx=(0, 18))
        av_wrap.pack_propagate(False)

        self._ring = ctk.CTkFrame(av_wrap, width=60, height=60,
                                  fg_color=SURFACE2, corner_radius=30,
                                  border_width=2, border_color=BLUE)
        self._ring.place(relx=0.5, rely=0.5, anchor="center")

        av = ctk.CTkFrame(av_wrap, width=52, height=52,
                          fg_color="#1e3a8a", corner_radius=26)
        av.place(relx=0.5, rely=0.5, anchor="center")
        av.pack_propagate(False)

        initials = "".join(w[0].upper() for w in self.user["name"].split()[:2])
        ctk.CTkLabel(
            av, text=initials,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=BLUE_TXT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        self._pulse_ring()

        fields = [
            ("Name",       self.user["name"]),
            ("Roll",       self.user.get("roll", "—")),
            ("Department", self.user.get("department", "—")),
            ("Semester",   self.user.get("semester", "—")),
            ("Shift",      str(self.user.get("shift", "—")).title()),
        ]
        for label, value in fields:
            col = ctk.CTkFrame(inner, fg_color="transparent")
            col.pack(side="left", padx=12)
            ctk.CTkLabel(col, text=label,
                         font=ctk.CTkFont(family="Segoe UI", size=10),
                         text_color=TEXT_MUT).pack(anchor="w")
            ctk.CTkLabel(col, text=value,
                         font=ctk.CTkFont(family="Segoe UI",
                                          size=13, weight="bold"),
                         text_color=TEXT_PRI).pack(anchor="w", pady=(1, 0))

    def _pulse_ring(self):
        if not self.winfo_exists():
            return
        try:
            colors = [BLUE, BORDER, BLUE_DIM, BORDER]
            self._ring.configure(border_color=colors[self._pulse_step % 4])
            self._pulse_step += 1
        except Exception:
            return
        self.after(600, self._pulse_ring)

    # ── Attendance Table ──────────────────────────────────────

    def _build_attendance_table(self):
        try:
            data = get_student_attendance(
                self.user["id"],
                self.user.get("department", ""),
                self.user.get("semester", ""),
                self.user.get("shift", ""),
            )
        except Exception:
            data = []

        outer = ctk.CTkFrame(self._scroll, fg_color="transparent")
        outer.pack(fill="x", padx=2, pady=(0, 4))

        if not data:
            ctk.CTkLabel(outer, text="No attendance records yet.",
                         font=ctk.CTkFont(family="Segoe UI", size=13),
                         text_color=TEXT_MUT).pack(pady=14, anchor="w")
            return

        # ── Header row
        hdr = ctk.CTkFrame(outer, fg_color=SURFACE2, corner_radius=8)
        hdr.pack(fill="x", pady=(0, 4))
        self._bind_card_hover(hdr, base_bg=SURFACE2, hover_bg="#22304a")
        _grid_header(hdr, ATT_COLS, ATT_WIDTHS, ATT_PAD0, ATT_PADX)

        # ── Data rows
        for idx, row in enumerate(data):
            total = row["total_classes"] or 0
            attended = row["attended"] or 0
            pct = round((attended / total * 100) if total > 0 else 0)
            pc = GREEN if pct >= 75 else (RED if pct < 60 else AMBER)

            bg = SURFACE
            rf = ctk.CTkFrame(outer, fg_color=(bg, bg), corner_radius=8)
            on_enter, on_leave = self._bind_row_hover(rf, normal_bg=bg)

            cells = [
                (row["subject"],               TEXT_PRI),
                (str(total),                   TEXT_SEC),
                (str(attended),                TEXT_PRI),
                (f"{pct}%",                    pc),
                (row["attended_dates"] or "—", TEXT_SEC),
            ]
            _grid_row(rf, cells, ATT_WIDTHS, ATT_PAD0, ATT_PADX)

            for child in rf.winfo_children():
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)

            self.after(idx * 70, lambda f=rf: f.pack(fill="x", pady=1))

        # ── Summary bar
        total_all = sum(r["total_classes"] or 0 for r in data)
        attended_all = sum(r["attended"] or 0 for r in data)
        op = round((attended_all / total_all * 100) if total_all > 0 else 0)
        oc = GREEN if op >= 75 else (RED if op < 60 else AMBER)

        summary = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10,
                               border_width=1, border_color=BORDER)
        summary.pack(fill="x", pady=(8, 0))
        self._bind_card_hover(summary, base_bg=SURFACE)
        ctk.CTkLabel(
            summary,
            text=f"Overall Attendance:  {attended_all} / {total_all} classes  —  ",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_SEC,
        ).pack(side="left", padx=(16, 0), pady=10)
        ctk.CTkLabel(
            summary, text=f"{op}%",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=(oc, oc),
        ).pack(side="left", pady=10)

    # ── Routine Section ───────────────────────────────────────

    def _build_routine_section(self):
        dept = self.user.get("department", "")
        semester = self.user.get("semester", "")
        shift = self.user.get("shift", "")

        outer = ctk.CTkFrame(self._scroll, fg_color="transparent")
        outer.pack(fill="x", padx=2, pady=(0, 24))

        try:
            rows = search_routines_for_student(dept, semester, shift)
        except Exception as e:
            ctk.CTkLabel(outer, text=f"❌  Routine load error: {e}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=RED).pack(anchor="w", pady=10)
            return

        if not rows:
            ctk.CTkLabel(outer,
                         text="⚠️  No routine found for this semester/shift.",
                         font=ctk.CTkFont(family="Segoe UI", size=13),
                         text_color=(AMBER, AMBER)).pack(anchor="w", pady=10)
            return

        grouped: dict[str, list] = {}
        for r in rows:
            grouped.setdefault(r["day"], []).append(r)

        for day_idx, day in enumerate(DAYS_ORDER):
            if day not in grouped:
                continue

            day_rows = grouped[day]
            day_color = DAY_COLOR.get(day, TEXT_SEC)

            # Day badge header
            day_hdr = ctk.CTkFrame(
                outer, fg_color=SURFACE, corner_radius=10,
                border_width=1, border_color=(day_color, day_color),
            )
            self._bind_card_hover(day_hdr, base_bg=SURFACE,
                                  hover_bg=HOVER_SURFACE,
                                  base_border=day_color,
                                  hover_border=HOVER_GLOW)
            ctk.CTkLabel(
                day_hdr,
                text=f"  {day}   —   {len(day_rows)} class{'es' if len(day_rows)>1 else ''}",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=(day_color, day_color),
            ).pack(anchor="w", padx=14, pady=7)

            # Class table
            tbl = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10,
                               border_width=1, border_color=BORDER)
            self._bind_card_hover(tbl, base_bg=SURFACE)

            # Header
            hdr_row = ctk.CTkFrame(tbl, fg_color=SURFACE2, corner_radius=6)
            hdr_row.pack(fill="x", padx=8, pady=(8, 2))
            _grid_header(hdr_row, ROU_COLS, ROU_WIDTHS, ROU_PAD0, ROU_PADX)

            # Data rows
            for idx, r in enumerate(day_rows):
                bg = SURFACE
                rf = ctk.CTkFrame(tbl, fg_color=(bg, bg), corner_radius=4)
                rf.pack(fill="x", padx=8, pady=1)

                def _enter(e, f=rf): f.configure(
                    fg_color=(HOVER_ROW, HOVER_ROW))

                def _leave(e, f=rf, ob=(bg, bg)): f.configure(fg_color=ob)
                rf.bind("<Enter>", _enter)
                rf.bind("<Leave>", _leave)

                cs = _td_to_hhmm(r.get("class_start"))
                ce = _td_to_hhmm(r.get("class_end"))
                si = "🌅" if r.get("shift") == "morning" else "☀️"

                cells = [
                    (str(idx + 1),                          TEXT_MUT),
                    (r["subject"],                          TEXT_PRI),
                    (r.get("teacher_name") or "—",          TEXT_SEC),
                    (f"{cs} – {ce}",                        BLUE_TXT),
                    (f"{si} {r.get('shift','').title()}",   AMBER),
                ]
                _grid_row(rf, cells, ROU_WIDTHS, ROU_PAD0, ROU_PADX)

                for child in rf.winfo_children():
                    child.bind("<Enter>", _enter)
                    child.bind("<Leave>", _leave)

            delay = day_idx * 110
            self.after(delay, lambda h=day_hdr: h.pack(fill="x", pady=(8, 2)))
            self.after(
                delay+50, lambda t=tbl:     t.pack(fill="x", pady=(0, 4)))

        ctk.CTkLabel(
            outer,
            text=f"Total {len(rows)} classes in this Week.",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color=TEXT_MUT,
        ).pack(anchor="w", pady=(6, 0))

    # ── Helpers ───────────────────────────────────────────────

    def _refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._populate_body()

    def _on_close(self):
        if self._star_cv:
            self._star_cv.stop()
        self.destroy()
        if self.on_close:
            self.on_close()

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
