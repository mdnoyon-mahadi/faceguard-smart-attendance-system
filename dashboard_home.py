# ============================================================
# admin_dashboard.py — Admin Dashboard (Futuristic Redesign + Charts)
# ============================================================
# Integrated matplotlib attendance graphs from dashboard_home.py
# ============================================================

import customtkinter as ctk
import sys
import os
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

# Fix path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.admin_model import get_dashboard_stats
from database.db_connection import execute_query
from config import APP_NAME
from theme import ThemeManager

# ── Chart Data Helpers (copied from dashboard_home.py) ───────

def _get_last7_attendance():
    """Last 7 days attendance count."""
    rows = execute_query(
        """SELECT session_date, COUNT(DISTINCT r.user_id) AS cnt
           FROM attendance_sessions s
           LEFT JOIN attendance_records r
               ON r.session_id = s.id AND r.status = 'complete'
           WHERE s.status = 'closed'
             AND s.session_date >= CURDATE() - INTERVAL 7 DAY
           GROUP BY session_date
           ORDER BY session_date""",
        fetch="all"
    ) or []
    return rows

def _get_subject_distribution():
    """Subject-wise total attendance."""
    rows = execute_query(
        """SELECT s.subject,
                  COUNT(DISTINCT CASE WHEN r.status='complete' THEN r.id END) AS attended
           FROM attendance_sessions s
           LEFT JOIN attendance_records r ON r.session_id = s.id
           WHERE s.status = 'closed'
           GROUP BY s.subject
           ORDER BY attended DESC
           LIMIT 6""",
        fetch="all"
    ) or []
    return rows

# ── Sidebar Menu Config ──────────────────────────────────────
MENU_ITEMS = [
    ("dashboard",        "⊞",  "Dashboard"),
    ("sep1",             None, None),
    ("user_add",         "＋", "Student Add"),
    ("user_list",        "≡",  "Student List"),
    ("sep2",             None, None),
    ("teacher_add",      "＋", "Teacher Add"),
    ("teacher_list",     "≡",  "Teacher List"),
    ("sep3",             None, None),
    ("routine_add",      "＋", "Routine Add"),
    ("routine_list",     "≡",  "Routine List"),
    ("sep4",             None, None),
    ("pending_requests", "◌",  "Pending Requests"),
    ("report",           "▦",  "Attendance Reports"),
    ("unknown_faces",    "◉",  "Unknown Faces"),
]

# Shorthand for theme color lookup
C = ThemeManager.get_color

# ========== GlowCard class (unchanged from your code) ==========
class GlowCard(ctk.CTkFrame):
    """Futuristic floating card with neon glow border + hover effect."""
    # ... (keep your exact GlowCard implementation) ...
    # (Due to length, I omit it here, but you must keep your existing GlowCard code)
    # For completeness in this answer, I'm summarizing – but in your final file, keep your full GlowCard class.

# ========== AdminDashboard class with charts integration ==========
class AdminDashboard(ctk.CTkToplevel):

    def __init__(self, admin: dict, on_logout=None, master=None):
        super().__init__(master)

        self.admin = admin
        self.on_logout = on_logout
        self._active_key = "dashboard"
        self._sidebar_btns = {}
        self._sidebar_expanded = True
        self._charts = []          # Store (fig, canvas) for cleanup

        self.title(f"{APP_NAME} — Admin Dashboard")
        self.geometry("1200x750")
        self.minsize(600, 500)
        self._center_window(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._last_width = 1200
        self._manual_sidebar_toggle = False
        self._resize_after_id = None
        self.bind("<Configure>", self._on_resize)

        ThemeManager.register(self._refresh_theme)

        self._build_ui()
        self._load_page("dashboard")

    # ── Main Layout (same as yours, keep everything) ────────────
    def _build_ui(self):
        # ... your existing _build_ui code ...
        pass

    def _build_sidebar(self):
        # ... your existing sidebar code ...
        pass

    def _build_navbar(self):
        # ... your existing navbar code ...
        pass

    # ── Page Router ───────────────────────────────────────────
    def _load_page(self, key: str):
        # ... your existing page loading logic ...
        pass

    # ─── MODIFIED: Dashboard Page with Charts ───────────────────
    def _page_dashboard(self):
        """Dashboard with stats cards + matplotlib attendance charts."""
        # Clear previous charts if any
        for fig, canvas in self._charts:
            plt.close(fig)
        self._charts.clear()

        # Main container
        self._dashboard_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._dashboard_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self._welcome_frame = ctk.CTkFrame(self._dashboard_container, fg_color="transparent")
        self._welcome_frame.pack(fill="x", pady=(0, 20))

        current_width = self.winfo_width()
        font_size = 28 if current_width > 1200 else 22
        self._dashboard_title = ctk.CTkLabel(
            self._welcome_frame, text="System Overview",
            font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"),
            text_color=C("text")
        )
        self._dashboard_title.pack(side="left")

        # Refresh button (also refreshes charts)
        refresh_btn = ctk.CTkButton(
            self._welcome_frame, text="↻ Refresh", width=90, height=30,
            fg_color="transparent", border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(size=12),
            command=self._refresh_dashboard
        )
        refresh_btn.pack(side="right")

        # Stats cards
        try:
            stats = get_dashboard_stats()
        except Exception:
            stats = {"total_students": 0, "total_teachers": 0,
                     "pending_requests": 0, "todays_classes": 0}

        self._cards_frame = ctk.CTkFrame(self._dashboard_container, fg_color="transparent")
        self._cards_frame.pack(fill="x", pady=(0, 20))

        self._dashboard_cards = []
        cards_data = [
            ("Total Students",   str(stats["total_students"]),   "◎", C("accent3"),  "Verified Students"),
            ("Total Teachers",   str(stats["total_teachers"]),   "◈", C("accent2"),  "Registered Faculty"),
            ("Pending",          str(stats["pending_requests"]), "◌", C("accent"),   "Action Required"),
            ("Reports",          "Active",                       "▦", C("success"),  "System Healthy"),
        ]
        for lbl, val, icon, color, sub in cards_data:
            card = GlowCard(self._cards_frame, lbl, val, icon, color, sub)
            self._dashboard_cards.append(card)
        self._regrid_cards(current_width)

        # ── CHARTS SECTION (two columns) ─────────────────────────
        charts_row = ctk.CTkFrame(self._dashboard_container, fg_color="transparent")
        charts_row.pack(fill="both", expand=True, pady=(10, 0))

        # Left: Last 7 days bar chart
        left_frame = ctk.CTkFrame(
            charts_row,
            fg_color=C("card"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border")
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            left_frame, text="Last 7 Days Attendance",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C("text_dim"),
            anchor="w"
        ).pack(padx=16, pady=(12, 0), anchor="w")

        self._build_bar_chart(left_frame)

        # Right: Subject distribution horizontal bar chart
        right_frame = ctk.CTkFrame(
            charts_row,
            fg_color=C("card"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
            width=260
        )
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)

        ctk.CTkLabel(
            right_frame, text="Subject Attendance",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C("text_dim"),
            anchor="w"
        ).pack(padx=16, pady=(12, 0), anchor="w")

        self._build_subject_chart(right_frame)

    def _build_bar_chart(self, parent):
        """Embed last 7 days bar chart."""
        try:
            data = _get_last7_attendance()
        except Exception:
            data = []

        # Use theme-aware colors
        bg_color = C("card")
        ax_bg = C("bg")
        text_color = C("text_dim")
        bar_color = C("accent3")   # use a nice accent color
        border_color = C("card_border")

        fig, ax = plt.subplots(figsize=(5.2, 2.6))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(ax_bg)

        if data:
            labels = [str(r["session_date"])[5:] for r in data]  # MM-DD
            values = [r["cnt"] for r in data]
            bars = ax.bar(labels, values, color=bar_color, width=0.5,
                          edgecolor=border_color, linewidth=0.5)

            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(val), ha="center", va="bottom",
                        fontsize=8, color=text_color)
            ax.set_ylim(0, max(values) * 1.3 + 1)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    transform=ax.transAxes, color=text_color, fontsize=11)

        ax.tick_params(colors=text_color, labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color(border_color)
        ax.yaxis.label.set_color(text_color)
        ax.set_ylabel("Students", color=text_color, fontsize=8)
        fig.tight_layout(pad=0.8)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(4, 12))
        self._charts.append((fig, canvas))

    def _build_subject_chart(self, parent):
        """Embed subject distribution horizontal bar chart."""
        try:
            data = _get_subject_distribution()
        except Exception:
            data = []

        bg_color = C("card")
        ax_bg = C("bg")
        text_color = C("text_dim")
        border_color = C("card_border")
        colors = [C("accent3"), C("accent2"), C("accent"), C("success"), C("danger"), "#3fb950"]

        fig, ax = plt.subplots(figsize=(2.8, 2.6))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(ax_bg)

        if data:
            labels = [r["subject"][:14] for r in data]
            values = [r["attended"] for r in data]
            bar_colors = colors[:len(labels)]
            bars = ax.barh(labels, values, color=bar_colors,
                           edgecolor=border_color, linewidth=0.5, height=0.55)
            for bar, val in zip(bars, values):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                        str(val), va="center", fontsize=7, color=text_color)
            ax.set_xlim(0, max(values) * 1.25 + 1)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    transform=ax.transAxes, color=text_color, fontsize=10)

        ax.tick_params(colors=text_color, labelsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ["bottom", "left"]:
            ax.spines[spine].set_color(border_color)
        fig.tight_layout(pad=0.6)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))
        self._charts.append((fig, canvas))

    def _refresh_dashboard(self):
        """Refresh the dashboard page (cards + charts)."""
        if self._active_key == "dashboard":
            self._load_page("dashboard")

    def _regrid_cards(self, width):
        """Responsive grid for stat cards (unchanged)."""
        # ... keep your existing _regrid_cards method ...
        pass

    # ── Theme & Cleanup ──────────────────────────────────────
    def _refresh_theme(self):
        """Rebuild UI when theme toggles, including charts."""
        # Clear charts
        for fig, canvas in self._charts:
            plt.close(fig)
        self._charts.clear()
        # Rebuild everything
        for w in self.winfo_children():
            w.destroy()
        self._sidebar_btns = {}
        self._sidebar_expanded = True
        self._build_ui()
        self._load_page(self._active_key)

    def _on_close(self):
        ThemeManager.unregister(self._refresh_theme)
        for fig, canvas in self._charts:
            plt.close(fig)
        self._cancel_all_afters()
        try:
            if self.master:
                self.master.destroy()
            else:
                self.destroy()
        except Exception:
            pass

    # ── (Include all your other methods: _toggle_sidebar, _tick,
    #    _cancel_all_afters, _logout, _on_resize, _apply_responsive_fixes,
    #    _center_window, and all page loader stubs) ─────────────────
    # (Keep them exactly as in your original admin_dashboard.py)