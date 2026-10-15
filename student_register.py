# ============================================================
# student_register.py — Student Registration Page
# ============================================================
# FIX:
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.

import customtkinter as ctk
from services.face_capture_widget import FaceCaptureWidget
from models.user_model import create_registration_request
from config import APP_NAME
from transitions import PageTransition, NavigationLock
from theme import ThemeManager

C = ThemeManager.get_color
INPUT_BG = ("#f8fafc", "#0f172a")
INPUT_TEXT = ("#1e293b", "#e2e8f0")
INPUT_BORDER = ("#cbd5e1", "#1e293b")
INPUT_FOCUS = ("#3b82f6", "#38bdf8")


class StudentRegister(ctk.CTkToplevel):

    def __init__(self, on_close=None):
        super().__init__()
        # [ANIM] Hide immediately — prevents flicker during UI construction
        PageTransition.prepare_window(self)

        self.on_close = on_close
        self._encoding = None

        self.title(f"{APP_NAME} — Student Registration")
        self.geometry("900x680")
        self.resizable(False, False)
        self._center_window(900, 680)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.lift()
        self.focus_force()
        # [ANIM] Fade in after full construction
        PageTransition.fade_in(self, steps=10, ms=18)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(fg_color=C("bg"))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Student Registration",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).pack(side="left")

        ctk.CTkButton(
            top, text="← Back",
            width=92, height=34,
            fg_color="transparent",
            border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._on_close,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=C("sep")).pack(
            fill="x", padx=28, pady=14
        )

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(
            body,
            fg_color="transparent",
            scrollbar_fg_color=C("bg2"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

# Comment translated to English.
        right = ctk.CTkFrame(
            body,
            fg_color=C("card"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
        )
        right.grid(row=0, column=1, sticky="nsew")

        self._build_form(left)
        self._build_face_panel(right)

    def _build_form(self, parent):
        ctk.CTkLabel(
            parent,
            text="Personal Information",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"),
            anchor="w",
        ).pack(anchor="w", pady=(10, 10))

        fields = [
            ("Roll Number *", "roll",  "e.g. 2021-CS-001"),
            ("Full Name *",   "name",  "Your full name"),
            ("Phone Number",  "phone", "01XXXXXXXXX"),
        ]

        self._entries = {}
        for label, key, placeholder in fields:
            self._make_field(parent, label, key, placeholder)

        # Department
        ctk.CTkLabel(
            parent, text="Department *",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"), anchor="w",
        ).pack(anchor="w", pady=(10, 4))

        self.dept_var = ctk.StringVar(value="Select Department")
        ctk.CTkOptionMenu(
            parent,
            variable=self.dept_var,
            values=["CST", "ET", "CT", "MT", "PT", "EMT", "ENT"],
            fg_color=INPUT_BG,
            button_color=INPUT_BORDER,
            button_hover_color=C("hover"),
            text_color=INPUT_TEXT,
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            height=38, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Semester
        ctk.CTkLabel(
            parent, text="Semester *",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"), anchor="w",
        ).pack(anchor="w", pady=(10, 4))

        self.sem_var = ctk.StringVar(value="Select Semester")
        ctk.CTkOptionMenu(
            parent,
            variable=self.sem_var,
            values=["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"],
            fg_color=INPUT_BG,
            button_color=INPUT_BORDER,
            button_hover_color=C("hover"),
            text_color=INPUT_TEXT,
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            height=38, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Shift
        ctk.CTkFrame(
            parent, height=1, fg_color=C("sep"),
        ).pack(fill="x", pady=(16, 12))

        ctk.CTkLabel(
            parent, text="Shift",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"), anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            parent, text="Shift *",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"), anchor="w",
        ).pack(anchor="w", pady=(4, 4))

        self.shift_var = ctk.StringVar(value="Select Shift")

        shift_frame = ctk.CTkFrame(parent, fg_color="transparent")
        shift_frame.pack(fill="x", pady=(0, 4))

        for shift_val, shift_label in [("day", "☀  Day"), ("morning", "🌅  Morning")]:
            btn = ctk.CTkButton(
                shift_frame,
                text=shift_label, height=38,
                fg_color=C("bg2"),
                hover_color=C("hover"),
                border_width=1, border_color=C("card_border"),
                text_color=C("text_dim"),
                font=ctk.CTkFont(family="Segoe UI", size=13), corner_radius=8,
                command=lambda v=shift_val: self._select_shift(v),
            )
            btn.pack(side="left", expand=True, fill="x",
                     padx=(0, 6) if shift_val == "day" else (0, 0))
            if shift_val == "day":
                self._shift_day_btn = btn
            else:
                self._shift_morning_btn = btn

        # Submit
        ctk.CTkFrame(
            parent, height=1, fg_color=C("sep"),
        ).pack(fill="x", pady=(16, 12))

        self.status_box = ctk.CTkFrame(
            parent,
            fg_color=C("bg2"),
            corner_radius=8,
            border_width=1,
            border_color=C("card_border")
        )
        self.status_box.pack(fill="x", pady=(0, 8))

        self.form_status = ctk.CTkLabel(
            self.status_box, text="Ready to submit your registration request.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C("text_dim"),
            wraplength=340,
            anchor="w",
            justify="left",
        )
        self.form_status.pack(fill="x", padx=10, pady=8)

        self.submit_btn = ctk.CTkButton(
            parent,
            text="📤  Submit Registration Request",
            height=46,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=C("accent3"),
            hover_color=C("accent"),
            corner_radius=10,
            command=self._submit,
        )
        self.submit_btn.pack(fill="x")
        self._bind_button_hover(self.submit_btn, C("accent3"), C("accent"))

        ctk.CTkLabel(
            parent,
            text="After submission, wait for admin approval",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"),
        ).pack(pady=(8, 0))

    def _select_shift(self, value):
        self.shift_var.set(value)
        sel_fg = C("btn_active")
        sel_bd = C("accent3")
        sel_tc = C("text")
        unsel_fg = C("bg2")
        unsel_bd = C("card_border")
        unsel_tc = C("text_dim")

        if value == "day":
            self._shift_day_btn.configure(
                fg_color=sel_fg, border_color=sel_bd, text_color=sel_tc)
            self._shift_morning_btn.configure(
                fg_color=unsel_fg, border_color=unsel_bd, text_color=unsel_tc)
        else:
            self._shift_morning_btn.configure(
                fg_color=sel_fg, border_color=sel_bd, text_color=sel_tc)
            self._shift_day_btn.configure(
                fg_color=unsel_fg, border_color=unsel_bd, text_color=unsel_tc)

    def _make_field(self, parent, label_text, key, placeholder):
        ctk.CTkLabel(
            parent, text=label_text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"), anchor="w",
        ).pack(anchor="w", pady=(10, 4))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=38,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            text_color=INPUT_TEXT,
            placeholder_text_color=C("text_dim"),
        )
        entry.pack(fill="x", pady=(0, 2))
        self._entries[key] = entry
        self._bind_entry_focus(entry)

    def _build_face_panel(self, parent):
        ctk.CTkLabel(
            parent, text="Face Scan",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"),
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            parent,
            text="Face scan is required\nfor registration",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"),
            justify="center",
        ).pack(pady=(0, 12))

        self.face_widget = FaceCaptureWidget(
            parent,
            on_complete=self._on_face_captured,
            fg_color="transparent",
        )
        self.face_widget.pack(padx=16, pady=(0, 16))

        self.face_status_lbl = ctk.CTkLabel(
            parent,
            text="⚠  Please complete face scan",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#e3b341", "#e3b341"),
        )
        self.face_status_lbl.pack(pady=(0, 12))

    # ── Callbacks ─────────────────────────────────────────────

    def _on_face_captured(self, encoding_bytes, error):
# Comment translated to English.
# Comment translated to English.
        if error:
            self._encoding = None
            self.face_status_lbl.configure(
                text=f"❌ {error}",
                text_color=("#f85149", "#f85149"))
            return

        self._encoding = encoding_bytes
        print(
            f"[DEBUG] Encoding received: size={len(encoding_bytes) if encoding_bytes else 0}")
        self.face_status_lbl.configure(
            text="✅ Face captured successfully!",
            text_color=("#3fb950", "#3fb950"))

    def _submit(self):
        roll = self._entries["roll"].get().strip()
        name = self._entries["name"].get().strip()
        phone = self._entries["phone"].get().strip()
        dept = self.dept_var.get()
        sem = self.sem_var.get()
        shift = self.shift_var.get()

        errors = []
        if not roll:
            errors.append("Enter Roll Number")
        if not name:
            errors.append("Enter name")
        if dept == "Select Department":
            errors.append("Select department")
        if sem == "Select Semester":
            errors.append("Select semester")
        if shift == "Select Shift":
            errors.append("Select shift")
        if self._encoding is None:
            errors.append("Complete face scan")

        if errors:
            self.form_status.configure(
                text="❌ " + " | ".join(errors),
                text_color=("#f85149", "#f85149"))
            self.status_box.configure(
                fg_color=("#2d1117", "#2d1117"),
                border_color=("#f85149", "#f85149")
            )
            return

        self.submit_btn.configure(state="disabled", text="⏳ Submitting...")
        self.form_status.configure(text="", text_color=C("text_dim"))

        try:
            create_registration_request(
                roll, name, dept, sem, shift, phone, self._encoding)
            self._show_success(name)
        except ValueError as e:
            self.form_status.configure(
                text=f"❌ {e}", text_color=("#f85149", "#f85149"))
            self.status_box.configure(
                fg_color=("#2d1117", "#2d1117"),
                border_color=("#f85149", "#f85149")
            )
            self.submit_btn.configure(
                state="normal", text="📤  Submit Registration Request")
        except Exception as e:
            self.form_status.configure(
                text=f"❌ Database error: {e}",
                text_color=("#f85149", "#f85149"))
            self.status_box.configure(
                fg_color=("#2d1117", "#2d1117"),
                border_color=("#f85149", "#f85149")
            )
            self.submit_btn.configure(
                state="normal", text="📤  Submit Registration Request")

    def _show_success(self, name):
        for widget in self.winfo_children():
            widget.destroy()

        self.configure(fg_color=C("bg"))
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="✅", font=ctk.CTkFont(family="Segoe UI", size=60)).pack()

        ctk.CTkLabel(
            frame, text="Registration successful!",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=("#3fb950", "#3fb950"),
        ).pack(pady=(12, 6))

        ctk.CTkLabel(
            frame,
            text=f"{name}, your registration request has been submitted.\n"
                 f"You can log in after admin approval.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"),
            justify="center",
        ).pack(pady=(0, 24))

        ctk.CTkButton(
            frame, text="← Back to Portal",
            height=42,
            fg_color=C("accent3"),
            hover_color=C("accent"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=8,
            command=self._on_close,
        ).pack()

    def _bind_entry_focus(self, entry):
        def _focus_in(_e):
            entry.configure(border_color=INPUT_FOCUS)
        def _focus_out(_e):
            entry.configure(border_color=INPUT_BORDER)
        entry.bind("<FocusIn>", _focus_in)
        entry.bind("<FocusOut>", _focus_out)

    def _bind_button_hover(self, btn, normal_color, hover_color):
        def _enter(_e):
            btn.configure(
                fg_color=hover_color,
                border_width=1,
                border_color=C("accent"),
                font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
            )
        def _leave(_e):
            btn.configure(
                fg_color=normal_color,
                border_width=0,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
            )
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    # ── Helpers ───────────────────────────────────────────────

    def _on_close(self):
        if hasattr(self, "face_widget"):
            try:
                self.face_widget.destroy()
            except Exception:
                pass
        
        # [ANIM] Fade out before returning
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