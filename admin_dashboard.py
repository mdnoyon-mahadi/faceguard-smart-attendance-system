# ============================================================
# admin_dashboard.py — Admin Dashboard (Futuristic Redesign)
# ============================================================
# Redesigned with Antigravity UI:
#   - Floating Cards & Neon Glows
#   - Collapsible Sidebar with glassmorphism
#   - Smooth Hover Animations
# ── [THEME] Updated to use centralized ThemeManager ──────────
# ============================================================

import customtkinter as ctk
import tkinter as tk
import sys
import os
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

# ✅ Fix path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.admin_model import get_dashboard_stats
from database.db_connection import execute_query
from config import APP_NAME
from theme import ThemeManager   # [THEME] Central theme manager

# ── Sidebar Menu Config ───────────────────────────────────────
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


def _get_last7_attendance():
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


class GlowCard(ctk.CTkFrame):
    """Futuristic floating card with neon glow border + hover effect."""

    def __init__(self, master, label, value, icon, color, sub_text, **kwargs):
        super().__init__(
            master,
            fg_color=C("card"),           # [THEME] card background
            corner_radius=20,
            border_width=2,
            border_color=color,
            **kwargs
        )
        self.default_color = color
        # [THEME] Hover cycles to secondary accent
        self.hover_color = C("accent") if color != C("accent") else C("accent2")

        self.grid_columnconfigure(0, weight=1)

        self.icon_lbl = ctk.CTkLabel(
            self, text=icon, font=ctk.CTkFont(family="Segoe UI", size=26), text_color=color
        )
        self.icon_lbl.grid(row=0, column=0, sticky="nw", padx=20, pady=(20, 0))

        self.val_lbl = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color=C("text")           # [THEME] primary text
        )
        self.val_lbl.grid(row=1, column=0, sticky="nw", padx=20, pady=(5, 0))

        self.label_lbl = ctk.CTkLabel(
            self, text=label, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=C("text")           # [THEME] primary text
        )
        self.label_lbl.grid(row=2, column=0, sticky="nw", padx=20)

        self.sub_lbl = ctk.CTkLabel(
            self, text=sub_text, font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim")       # [THEME] muted text
        )
        self.sub_lbl.grid(row=3, column=0, sticky="nw", padx=20, pady=(0, 20))

        # Animation state
        self._current_factor = 0.0
        self._anim_id = None

        # Hover bindings
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)

    def _animate_hover_fx(self, target_factor):
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            
        def step():
            if not self.winfo_exists(): return
            diff = target_factor - self._current_factor
            if abs(diff) < 0.05:
                self._current_factor = target_factor
                self._apply_fx(target_factor)
                self._anim_id = None
                return
            
            self._current_factor += diff * 0.25
            self._apply_fx(self._current_factor)
            self._anim_id = self.after(16, step)
            
        step()

    def _resolve_color(self, c):
        if isinstance(c, tuple) or isinstance(c, list):
            mode = ctk.get_appearance_mode()
            return c[1] if mode.lower() == "dark" else c[0]
        return c

    def _hex_blend(self, c1, c2, factor):
        c1 = self._resolve_color(c1)
        c2 = self._resolve_color(c2)
        if str(c1).startswith("#") and str(c2).startswith("#") and len(c1) == 7 and len(c2) == 7:
            r = int(int(c1[1:3], 16) * (1 - factor) + int(c2[1:3], 16) * factor)
            g = int(int(c1[3:5], 16) * (1 - factor) + int(c2[3:5], 16) * factor)
            b = int(int(c1[5:7], 16) * (1 - factor) + int(c2[5:7], 16) * factor)
            return f"#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}"
        return c2

    def _apply_fx(self, factor):
        try:
            # 1. Multi-axis layout shift
            self.icon_lbl.grid_configure(padx=int(20 + (12 * factor)))
            self.val_lbl.grid_configure(pady=(int(5 - (5 * factor)), 0))
            
            # 2. Border Expansion
            new_bw = int(2 + (2 * factor))
            
            # 3. Dynamic Background Color Glow
            base_bg = self._resolve_color(C("card"))
            target_bg = self._hex_blend(base_bg, self.default_color, 0.15) # Subtle neon tint
            current_bg = self._hex_blend(base_bg, target_bg, factor)
            
            # 4. Smooth Border Color Transition
            border_start = self._resolve_color(self.default_color)
            border_end = self._resolve_color(self.hover_color)
            current_border = self._hex_blend(border_start, border_end, factor)
            
            self.configure(fg_color=current_bg, border_color=current_border, border_width=new_bw)
        except Exception:
            pass

    def _on_enter(self, event):
        if not self.winfo_exists(): return
        self._animate_hover_fx(1.0)

    def _on_leave(self, event):
        if not self.winfo_exists(): return
        self._animate_hover_fx(0.0)

    def update_scaling(self, width):
        """Scale fonts and padding based on window width."""
        if width < 1100:
            self.icon_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=22))
            self.val_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"))
            self.label_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        else:
            self.icon_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=26))
            self.val_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"))
            self.label_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))


class AdminDashboard(ctk.CTkToplevel):

    def __init__(self, admin: dict, on_logout=None, master=None):
        super().__init__(master)

        self.admin = admin
        self.on_logout = on_logout
        self._active_key = "dashboard"
        self._sidebar_btns = {}
        self._sidebar_expanded = True
        self._charts = []
        self._closing = False
        self._tick_id = None

        self.title(f"{APP_NAME} — Admin Dashboard")
        self.geometry("1200x750")
        self.minsize(600, 500)
        self._center_window(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Responsive state
        self._last_width = 1200
        self._manual_sidebar_toggle = False
        self._resize_after_id = None
        self.bind("<Configure>", self._on_resize)

        # [THEME] Register refresh callback so theme toggle re-renders
        ThemeManager.register(self._refresh_theme)

        self._build_ui()
        self._load_page("dashboard")

    # ── Main Layout ───────────────────────────────────────────

    def _build_ui(self):
        self.configure(fg_color=C("bg"))                # [THEME] root bg
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=240,
            fg_color=C("sidebar"),                      # [THEME] sidebar bg
            corner_radius=0,
            border_width=1,
            border_color=C("card_border")               # [THEME] border
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # ── Navbar ────────────────────────────────────────────
        self.navbar = ctk.CTkFrame(
            self, height=70,
            fg_color=C("bg2"),                          # [THEME] navbar bg
            corner_radius=0,
            border_width=1,
            border_color=C("card_border")               # [THEME] border
        )
        self.navbar.grid(row=0, column=1, sticky="ew")
        self.navbar.grid_propagate(False)

        # ── Content Area ──────────────────────────────────────
        self.content_area = ctk.CTkFrame(
            self, fg_color=C("bg"),                     # [THEME] content bg
            corner_radius=0
        )
        self.content_area.grid(row=1, column=1, sticky="nsew")

        self._build_sidebar()
        self._build_navbar()

    def _build_sidebar(self):
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(25, 20))

        self.logo_lbl = ctk.CTkLabel(
            logo_frame, text="◈",
            font=ctk.CTkFont(family="Segoe UI", size=38),
            text_color=C("accent")                      # [THEME] neon accent
        )
        self.logo_lbl.pack()

        self.title_lbl = ctk.CTkLabel(
            logo_frame, text="Face Recognition\nAttendance System",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=C("text"),                       # [THEME] primary text
            justify="center"
        )
        self.title_lbl.pack()

        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=C("sep")   # [THEME] separator
        ).pack(fill="x", padx=20, pady=10)

        # Menu container
        self.menu_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_container.pack(fill="both", expand=True, padx=12)

        for key, icon, label in MENU_ITEMS:
            if icon is None:
                ctk.CTkFrame(
                    self.menu_container, height=1, fg_color=C("sep")  # [THEME]
                ).pack(fill="x", padx=10, pady=5)
                continue

            btn = ctk.CTkButton(
                self.menu_container,
                text=f"  {icon}   {label}",
                anchor="w",
                height=42,
                corner_radius=12,
                fg_color="transparent",
                hover_color=C("hover"),                 # [THEME] hover bg
                text_color=C("text_dim"),               # [THEME] dim text
                font=ctk.CTkFont(family="Segoe UI", size=14),
                command=lambda k=key: self._load_page(k),
            )
            btn.pack(fill="x", pady=2)
            self._sidebar_btns[key] = btn

        # Logout at bottom
        self.logout_btn = ctk.CTkButton(
            self.sidebar,
            text="  ⏻   Logout",
            anchor="w",
            height=42,
            corner_radius=12,
            fg_color="transparent",
            hover_color=C("hover"),                     # [THEME]
            text_color=C("danger"),                     # [THEME] danger red
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self._logout,
        )
        self.logout_btn.pack(fill="x", padx=12, pady=(0, 20), side="bottom")

        # Sidebar Toggle Button
        self.toggle_btn = ctk.CTkButton(
            self.sidebar, text="«", width=30, height=30, corner_radius=15,
            fg_color="transparent",
            text_color=C("accent"),                     # [THEME]
            font=ctk.CTkFont(family="Segoe UI", size=18),
            command=self._toggle_sidebar
        )
        self.toggle_btn.place(relx=0.9, rely=0.03, anchor="center")

    def _build_navbar(self):
        # Path / Breadcrumb
        self.path_lbl = ctk.CTkLabel(
            self.navbar, text="Admin / Dashboard",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim")                    # [THEME]
        )
        self.path_lbl.pack(side="left", padx=25)

        # Right-side: Theme toggle + admin info
        self.admin_info_frame = ctk.CTkFrame(self.navbar, fg_color="transparent")
        self.admin_info_frame.pack(side="right", padx=25)

        self.welcome_lbl = ctk.CTkLabel(
            self.admin_info_frame,
            text=f"Welcome, {self.admin['username']}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=C("text")                        # [THEME]
        )
        self.welcome_lbl.pack(side="right", padx=(10, 0))

        self.clock_lbl = ctk.CTkLabel(
            self.admin_info_frame, text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("accent")                      # [THEME]
        )
        self.clock_lbl.pack(side="right", padx=20)
        self._tick()

        # [THEME] Dark/Light toggle button in navbar
        self.theme_btn = ctk.CTkButton(
            self.admin_info_frame,
            text="☀ Light" if ThemeManager.current_mode == "dark" else "☾ Dark",
            width=90, height=32,
            corner_radius=16,
            fg_color=C("btn_active"),                   # [THEME]
            hover_color=C("hover"),                     # [THEME]
            text_color=C("accent"),                     # [THEME]
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="right", padx=10)

    # ── Theme Toggle ─────────────────────────────────────────

    def _toggle_theme(self):
        """Toggle dark ↔ light mode and refresh the entire UI."""
        ThemeManager.toggle()
        # [THEME] refresh_theme is called via the registered callback

    def _refresh_theme(self):
        """
        [THEME] Called by ThemeManager whenever theme changes.
        Destroys and rebuilds the full UI to apply new colors instantly.
        """
        for fig, canvas in self._charts:
            plt.close(fig)
        self._charts.clear()

        # Destroy all children cleanly
        for w in self.winfo_children():
            w.destroy()

        self._sidebar_btns = {}
        self._sidebar_expanded = True

        # Rebuild with new theme colors
        self._build_ui()
        self._load_page(self._active_key)

    # ── Sidebar Toggle ────────────────────────────────────────

    def _toggle_sidebar(self, manual=True):
        if not self.winfo_exists() or not hasattr(self, 'sidebar') or not self.sidebar.winfo_exists():
            return
            
        if manual:
            self._manual_sidebar_toggle = True

        try:
            if self._sidebar_expanded:
                self.sidebar.configure(width=60)
                self.title_lbl.pack_forget()
                self.logo_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=28))
                self.toggle_btn.configure(text="»")
                self.toggle_btn.place(relx=0.5, rely=0.03, anchor="center")
                for btn in self._sidebar_btns.values():
                    original_text = btn.cget("text")
                    # Extract only the icon (first part)
                    icon = original_text.strip().split()[0]
                    btn.configure(text=icon, anchor="center")
                self.logout_btn.configure(text="⏻", anchor="center")
                self.menu_container.pack_configure(padx=0)
            else:
                self.sidebar.configure(width=240)
                self.title_lbl.pack(after=self.logo_lbl)
                self.logo_lbl.configure(font=ctk.CTkFont(family="Segoe UI", size=38))
                self.toggle_btn.configure(text="«")
                self.toggle_btn.place(relx=0.9, rely=0.03, anchor="center")
                for key, btn in self._sidebar_btns.items():
                    item = next(x for x in MENU_ITEMS if x[0] == key)
                    btn.configure(text=f"  {item[1]}   {item[2]}", anchor="w")
                self.logout_btn.configure(text="  ⏻   Logout", anchor="w")
                self.menu_container.pack_configure(padx=12)
        except tk.TclError:
            # Ignore invalid widget state if the sidebar is already destroyed or in the process of closing.
            return

        self._sidebar_expanded = not self._sidebar_expanded

    # ── Page Router ───────────────────────────────────────────

    def _load_page(self, key: str):
        for fig, canvas in self._charts:
            plt.close(fig)
        self._charts.clear()

        # Update sidebar active state
        for k, btn in self._sidebar_btns.items():
            if k == key:
                btn.configure(
                    fg_color=C("btn_active"),           # [THEME]
                    text_color=C("accent"),             # [THEME]
                    border_width=1,
                    border_color=C("accent3")           # [THEME]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=C("text_dim"),           # [THEME]
                    border_width=0
                )

        self._active_key = key
        self.path_lbl.configure(text=f"Admin / {key.replace('_', ' ').title()}")

        # Clear content area
        for w in self.content_area.winfo_children():
            w.destroy()

        # Page map
        page_map = {
            "dashboard":        self._page_dashboard,
            "user_add":         self._page_user_add,
            "user_list":        self._page_user_list,
            "teacher_add":      self._page_teacher_add,
            "teacher_list":     self._page_teacher_list,
            "routine_add":      self._page_routine_add,
            "routine_list":     self._page_routine_list,
            "pending_requests": self._page_pending,
            "report":           self._page_report,
            "unknown_faces":    self._page_unknown_faces,
        }
        loader = page_map.get(key)
        if loader:
            loader()

    # ── Page Loaders ──────────────────────────────────────────

    def _page_dashboard(self):
        """Redesigned Dashboard Home with Responsive Antigravity Cards."""
        self._dashboard_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._dashboard_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self._welcome_frame = ctk.CTkFrame(self._dashboard_container, fg_color="transparent")
        self._welcome_frame.pack(fill="x", pady=(0, 20))

        # Scale font based on width
        current_width = self.winfo_width()
        font_size = 28 if current_width > 1200 else 22

        self._dashboard_title = ctk.CTkLabel(
            self._welcome_frame, text="System Overview",
            font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"),
            text_color=C("text")
        )
        self._dashboard_title.pack(side="left")

        # Stats
        try:
            stats = get_dashboard_stats()
        except Exception:
            stats = {"total_students": 0, "total_teachers": 0,
                     "pending_requests": 0, "todays_classes": 0}

        self._cards_frame = ctk.CTkFrame(self._dashboard_container, fg_color="transparent")
        self._cards_frame.pack(fill="x")

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

        # Initial grid
        self._regrid_cards(current_width)

        graph_wrap = ctk.CTkFrame(
            self._dashboard_container,
            fg_color=C("card"),
            corner_radius=14,
            border_width=1,
            border_color=C("card_border")
        )
        graph_wrap.pack(fill="both", expand=True, pady=(16, 0))

        ctk.CTkLabel(
            graph_wrap,
            text="Attendance (Last 7 Days)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=C("text_dim")
        ).pack(anchor="w", padx=16, pady=(12, 0))

        self._build_attendance_graph(graph_wrap)

    def _build_attendance_graph(self, parent):
        try:
            data = _get_last7_attendance()
        except Exception:
            data = []

        fig, ax = plt.subplots(figsize=(8.2, 2.7))
        fig.patch.set_facecolor(C("card"))
        ax.set_facecolor(C("bg"))

        if data:
            labels = [str(r["session_date"])[5:] for r in data]
            values = [r["cnt"] for r in data]
            bars = ax.bar(
                labels, values,
                color=C("accent3"),
                edgecolor=C("card_border"),
                linewidth=0.6,
                width=0.55
            )
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    str(val), ha="center", va="bottom", fontsize=8, color=C("text_dim")
                )
            ax.set_ylim(0, max(values) * 1.3 + 1)
        else:
            ax.text(
                0.5, 0.5, "No attendance data yet",
                ha="center", va="center", transform=ax.transAxes,
                color=C("text_dim"), fontsize=10
            )

        ax.tick_params(colors=C("text_dim"), labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(C("card_border"))
        ax.spines["bottom"].set_color(C("card_border"))
        ax.set_ylabel("Students", color=C("text_dim"), fontsize=8)
        fig.tight_layout(pad=0.8)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(4, 12))
        self._charts.append((fig, canvas))

    def _regrid_cards(self, width):
        """Dynamic grid for cards."""
        if not hasattr(self, "_dashboard_cards") or not self._dashboard_cards:
            return

        if width >= 1200:
            cols = 4
        elif width >= 768:
            cols = 2
        else:
            cols = 1

        # Clear existing grid config
        for i in range(4):
            self._cards_frame.grid_columnconfigure(i, weight=0)

        # Set new grid
        for i, card in enumerate(self._dashboard_cards):
            card.grid_forget()
            r = i // cols
            c = i % cols
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            card.update_scaling(width)

        for i in range(cols):
            self._cards_frame.grid_columnconfigure(i, weight=1, minsize=200)

        # Scale font
        font_size = 28 if width > 1200 else 22
        if hasattr(self, "_dashboard_title"):
            self._dashboard_title.configure(font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"))

    def _page_user_add(self):
        from views.admin_pages.user_add import UserAddPage
        UserAddPage(self.content_area).pack(fill="both", expand=True)

    def _page_user_list(self):
        from views.admin_pages.user_list import UserListPage
        UserListPage(self.content_area, on_edit=lambda: self._load_page("user_list")).pack(fill="both", expand=True)

    def _page_teacher_add(self):
        from views.admin_pages.teacher_add import TeacherAddPage
        TeacherAddPage(self.content_area).pack(fill="both", expand=True)

    def _page_teacher_list(self):
        from views.admin_pages.teacher_list import TeacherListPage
        TeacherListPage(self.content_area).pack(fill="both", expand=True)

    def _page_routine_add(self):
        from views.admin_pages.routine_add import RoutineAddPage
        RoutineAddPage(self.content_area).pack(fill="both", expand=True)

    def _page_routine_list(self):
        from views.admin_pages.routine_list import RoutineListPage
        RoutineListPage(self.content_area).pack(fill="both", expand=True)

    def _page_pending(self):
        from views.admin_pages.pending_requests import PendingRequestsPage
        PendingRequestsPage(
            self.content_area,
            on_refresh=lambda: self._load_page("pending_requests")
        ).pack(fill="both", expand=True)

    def _page_report(self):
        from views.admin_pages.report_view import ReportViewPage
        ReportViewPage(self.content_area).pack(fill="both", expand=True)

    def _page_unknown_faces(self):
        from views.admin_pages.unknown_faces import UnknownFacesPage
        UnknownFacesPage(self.content_area).pack(fill="both", expand=True)

    # ── Helpers ───────────────────────────────────────────────

    def _tick(self):
        if not self.winfo_exists():
            return
        try:
            now = datetime.now()
            self.clock_lbl.configure(text=now.strftime("%I:%M:%S %p"))
            self._tick_id = self.after(1000, self._tick)  # store ID for cancellation
        except Exception:
            pass

    def _cancel_all_afters(self):
        """Cancel dashboard-owned after() callbacks before destroy."""
        command_names = set()

        def _cancel_for(widget):
            for cmd in getattr(widget, "_tclCommands", []) or []:
                command_names.add(str(cmd))

            for attr in ("_tick_id", "_resize_after_id", "_anim_id"):
                aid = getattr(widget, attr, None)
                if not aid:
                    continue
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
                try:
                    setattr(widget, attr, None)
                except Exception:
                    pass

            try:
                children = widget.winfo_children()
            except Exception:
                children = []
            for child in children:
                _cancel_for(child)

        _cancel_for(self)

        try:
            after_ids = self.tk.call("after", "info")
            if isinstance(after_ids, str):
                after_ids = after_ids.split()

            for aid in after_ids:
                try:
                    info = self.tk.call("after", "info", aid)
                    script = info[0] if isinstance(info, tuple) and info else info
                    command = str(script).split()[0]
                except Exception:
                    continue

                if command in command_names:
                    try:
                        self.after_cancel(aid)
                    except Exception:
                        pass
        except Exception:
            pass

    def _logout(self):
        """Close only the dashboard and return to the login/home page."""
        self._close_dashboard()

    def _on_close(self):
        """Handle X button close without exiting the application."""
        self._close_dashboard()

    def _close_dashboard(self):
        """Destroy this Toplevel, then safely restore the caller window."""
        if self._closing:
            return
        self._closing = True

        callback = self.on_logout
        self.on_logout = None

        try:
            self.protocol("WM_DELETE_WINDOW", lambda: None)
            self.withdraw()
        except Exception:
            pass

        ThemeManager.unregister(self._refresh_theme)    # [THEME] clean up
        self._cancel_all_afters()                       # stop clock + any after loops
        for fig, canvas in self._charts:
            plt.close(fig)
        self._charts.clear()
        try:
            self.destroy()
        except Exception:
            pass

        if callback:
            try:
                callback()
            except Exception:
                pass

    # ── Responsiveness ────────────────────────────────────────
    def _on_resize(self, event):
        """Handle window resize and adjust layout."""
        if event.widget != self:
            return

        curr_w = self.winfo_width()
        if abs(curr_w - self._last_width) < 10:
            return  # ignore small fluctuations

        self._last_width = curr_w

        # Debounce the heavy layout changes
        if self._resize_after_id:
            try:
                self.after_cancel(self._resize_after_id)
            except Exception:
                pass
        
        # Only set an after event if the widget still exists
        if self.winfo_exists():
            self._resize_after_id = self.after(50, lambda: self._apply_responsive_fixes(curr_w))

    def _apply_responsive_fixes(self, width):
        """Apply all responsiveness rules based on current width."""
        if not self.winfo_exists() or not hasattr(self, 'sidebar') or not self.sidebar.winfo_exists():
            return

        # 1. Sidebar auto-collapse
        if width < 1100 and self._sidebar_expanded and not self._manual_sidebar_toggle:
            self._toggle_sidebar(manual=False)
        elif width >= 1100 and not self._sidebar_expanded and not self._manual_sidebar_toggle:
            self._toggle_sidebar(manual=False)

        # 2. Navbar scaling
        if width < 950:
            self.welcome_lbl.pack_forget()
        else:
            self.welcome_lbl.pack(side="right", padx=(10, 0))

        if width < 750:
            self.clock_lbl.pack_forget()
        else:
            self.clock_lbl.pack(side="right", padx=20)

        # 3. Regrid cards if on dashboard
        if self._active_key == "dashboard":
            self._regrid_cards(width)

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


if __name__ == "__main__":
    admin_data = {"username": "Admin_Test"}
    root = ctk.CTk()
    root.withdraw()
    app = AdminDashboard(admin=admin_data, on_logout=root.destroy, master=root)
    root.mainloop()
