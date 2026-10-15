# ============================================================
# student_portal.py — Student Portal (Login / Register)
# ============================================================

import customtkinter as ctk
from config import APP_NAME
from transitions import PageTransition, NavigationLock

class StudentPortal(ctk.CTkToplevel):
    PALETTE = {
        "bg": "#0d1117",
        "navbar": "#161b22",
        "sidebar": "#0a0e1a",
        "card": "#0d121f",
        "accent_primary": "#00d2ff",
        "accent_secondary": "#7c3aed",
        "accent_tertiary": "#0ea5e9",
        "success": "#4ade80",
        "danger": "#f87171",
        "text_primary": "#f8fafc",
        "text_muted": "#94a3b8",
        "border_soft": "#1f2937",
        "hover_soft": "#1b2431",
    }

    def __init__(self, on_close=None):
        super().__init__()
        # [ANIM] Hide immediately — prevents flicker during UI construction
        PageTransition.prepare_window(self)
        
        self.on_close = on_close
        self.title(f"{APP_NAME} — Student Portal")
        self.geometry("500x400")
        self.resizable(False, False)
        self._center_window(500, 400)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._build_ui()
        
        self.lift()
        self.focus_force()
        # [ANIM] Fade in after full construction
        PageTransition.fade_in(self, steps=10, ms=18)

    def _build_ui(self):
        self.configure(fg_color=(self.PALETTE["bg"], self.PALETTE["bg"]))

        # ── Header ────────────────────────────────────────────
        header = ctk.CTkFrame(
            self, fg_color=(self.PALETTE["navbar"], self.PALETTE["navbar"]),
            corner_radius=0, height=56,
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="← Back", width=70, height=28,
            fg_color="transparent", border_width=1,
            border_color=(self.PALETTE["border_soft"], self.PALETTE["border_soft"]),
            text_color=(self.PALETTE["text_muted"], self.PALETTE["text_muted"]),
            hover_color=(self.PALETTE["hover_soft"], self.PALETTE["hover_soft"]),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._on_close,
        ).place(x=16, rely=0.5, anchor="w")

        ctk.CTkLabel(
            header, text="Student Portal",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=(self.PALETTE["text_primary"], self.PALETTE["text_primary"]),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Body ──────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=40)

        # Main card gives the portal a cleaner and more professional focal point.
        card = ctk.CTkFrame(
            body,
            fg_color=(self.PALETTE["card"], self.PALETTE["card"]),
            corner_radius=16,
            border_width=1,
            border_color=(self.PALETTE["border_soft"], self.PALETTE["border_soft"]),
        )
        card.pack(fill="both", expand=True, padx=4, pady=4)

        accent_line = ctk.CTkFrame(
            card,
            fg_color=(self.PALETTE["accent_primary"], self.PALETTE["accent_primary"]),
            height=3,
            corner_radius=8,
        )
        accent_line.pack(fill="x", padx=24, pady=(20, 10))
        accent_line.pack_propagate(False)

        # Welcome Text
        ctk.CTkLabel(
            card, text="Welcome to Student Portal",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=(self.PALETTE["text_primary"], self.PALETTE["text_primary"]),
        ).pack(pady=(6, 10))

        ctk.CTkLabel(
            card, text="If you do not have an account, register first.\nIf you already have one, log in.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=(self.PALETTE["text_muted"], self.PALETTE["text_muted"]),
            justify="center"
        ).pack(pady=(0, 32))

        # Buttons Container
        btn_container = ctk.CTkFrame(card, fg_color="transparent")
        btn_container.pack(fill="x", padx=24, pady=(0, 24))

        # Login Button
        self.login_btn = ctk.CTkButton(
            btn_container,
            text="Login",
            height=60,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=(self.PALETTE["accent_primary"], self.PALETTE["accent_primary"]),
            hover_color=(self.PALETTE["accent_tertiary"], self.PALETTE["accent_tertiary"]),
            text_color=("#041820", "#041820"),
            corner_radius=12,
            command=self._open_login
        )
        self.login_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Register Button
        self.reg_btn = ctk.CTkButton(
            btn_container,
            text="Register",
            height=60,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=(self.PALETTE["accent_secondary"], self.PALETTE["accent_secondary"]),
            hover_color=("#6d28d9", "#6d28d9"),
            text_color=(self.PALETTE["text_primary"], self.PALETTE["text_primary"]),
            border_width=1,
            border_color=(self.PALETTE["border_soft"], self.PALETTE["border_soft"]),
            corner_radius=12,
            command=self._open_register
        )
        self.reg_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _open_login(self):
        if not NavigationLock.acquire():
            return
        def _do_open():
            from views.student_login import StudentLogin
            self.destroy()
            # on_close will handle showing main page when Login window closes
            win = StudentLogin(on_close=self.on_close)
            # win handles its own fade_in (usually, if not, I'll check)
        PageTransition.fade_out(self, on_done=_do_open)

    def _open_register(self):
        if not NavigationLock.acquire():
            return
        def _do_open():
            from views.student_register import StudentRegister
            self.destroy()
            win = StudentRegister(on_close=self.on_close)
        PageTransition.fade_out(self, on_done=_do_open)

    def _on_close(self):
        def _do_close():
            NavigationLock.release()
            self.destroy()
            if self.on_close:
                self.on_close()
        PageTransition.fade_out(self, on_done=_do_close, steps=8, ms=18)

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")