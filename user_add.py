# ============================================================
# user_add.py — Admin User Add Page
# ============================================================
# FIX:
# Comment translated to English.
# Comment translated to English.

import customtkinter as ctk
from services.face_capture_widget import FaceCaptureWidget
from models.user_model import add_user_by_admin
from theme import ThemeManager

C = ThemeManager.get_color
# Light mode uses clean, soft inputs; dark mode keeps deep navy.
INPUT_BG = ("#f8fafc", "#0f172a")
INPUT_TEXT = ("#1e293b", "#e2e8f0")
INPUT_BORDER = ("#cbd5e1", "#1e293b")
INPUT_FOCUS = ("#3b82f6", "#38bdf8")


class UserAddPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._encoding = None
        self._warn_bg = ctk.StringVar(value=C("bg2"))
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Add Student",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=C("sep")).pack(
            fill="x", padx=28, pady=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(
            body, fg_color="transparent",
            scrollbar_fg_color=C("bg2"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

# Comment translated to English.
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
            parent, text="Student Information",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text")
        ).pack(anchor="w", pady=(10, 10))

        self._entries = {}
        for label, key, ph in [
            ("Roll Number *", "roll",  "e.g. 2021-CS-001"),
            ("Full Name *",   "name",  "Enter student's full name"),
            ("Phone",         "phone", "01XXXXXXXXX"),
        ]:
            self._lbl(parent, label)
            e = ctk.CTkEntry(
                parent, placeholder_text=ph, height=38,
                fg_color=INPUT_BG,
                border_color=INPUT_BORDER,
                text_color=INPUT_TEXT,
                placeholder_text_color=C("text_dim"),
            )
            e.pack(fill="x", pady=(0, 4))
            self._entries[key] = e
            self._bind_entry_focus(e)

        # Department
        self._lbl(parent, "Department *")
        self.dept_var = ctk.StringVar(value="Select Department")
        ctk.CTkOptionMenu(
            parent, variable=self.dept_var,
            values=["CST", "ET", "CT", "MT", "PT", "EMT", "ENT"],
            fg_color=INPUT_BG, button_color=INPUT_BORDER,
            button_hover_color=C("hover"),
            text_color=INPUT_TEXT,
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            height=38, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Semester
        self._lbl(parent, "Semester *")
        self.sem_var = ctk.StringVar(value="1st")
        ctk.CTkOptionMenu(
            parent, variable=self.sem_var,
            values=["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"],
            fg_color=INPUT_BG, button_color=INPUT_BORDER,
            button_hover_color=C("hover"),
            text_color=INPUT_TEXT,
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            height=38, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Shift
        ctk.CTkFrame(parent, height=1, fg_color=C("sep")).pack(
            fill="x", pady=(14, 10))

        ctk.CTkLabel(
            parent, text="Shift",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"), anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self._lbl(parent, "Shift *")
        self.shift_var = ctk.StringVar(value="")

        shift_frame = ctk.CTkFrame(parent, fg_color="transparent")
        shift_frame.pack(fill="x", pady=(0, 4))

        for val, label in [("day", "☀  Day"), ("morning", "🌅  Morning")]:
            btn = ctk.CTkButton(
                shift_frame, text=label, height=38,
                fg_color=C("bg2"),
                hover_color=C("hover"),
                border_width=1, border_color=C("card_border"),
                text_color=C("text_dim"),
                font=ctk.CTkFont(family="Segoe UI", size=13), corner_radius=8,
                command=lambda v=val: self._select_shift(v),
            )
            btn.pack(side="left", expand=True, fill="x",
                     padx=(0, 6) if val == "day" else (0, 0))
            if val == "day":
                self._btn_day = btn
            else:
                self._btn_morning = btn

        # Submit
        ctk.CTkFrame(parent, height=1, fg_color=C("sep")).pack(
            fill="x", pady=(14, 10))

        self.status_box = ctk.CTkFrame(
            parent,
            fg_color=C("bg2"),
            corner_radius=8,
            border_width=1,
            border_color=C("card_border")
        )
        self.status_box.pack(fill="x", pady=(0, 8))

        self.status_lbl = ctk.CTkLabel(
            self.status_box, text="Ready to add a student record.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C("text_dim"),
            wraplength=340,
            anchor="w",
            justify="left"
        )
        self.status_lbl.pack(fill="x", padx=10, pady=8)

        self.save_btn = ctk.CTkButton(
            parent, text="💾  Save Student",
            height=46,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=C("accent3"),
            hover_color=C("accent"),
            corner_radius=10,
            command=self._save,
        )
        self.save_btn.pack(fill="x")
        self._bind_button_hover(self.save_btn, C("accent3"), C("accent"))

    def _select_shift(self, value):
        self.shift_var.set(value)
        sel_fg = C("btn_active")
        sel_bd = C("accent3")
        sel_tc = C("text")
        unsel_fg = C("bg2")
        unsel_bd = C("card_border")
        unsel_tc = C("text_dim")
        if value == "day":
            self._btn_day.configure(
                fg_color=sel_fg, border_color=sel_bd, text_color=sel_tc)
            self._btn_morning.configure(
                fg_color=unsel_fg, border_color=unsel_bd, text_color=unsel_tc)
        else:
            self._btn_morning.configure(
                fg_color=sel_fg, border_color=sel_bd, text_color=sel_tc)
            self._btn_day.configure(
                fg_color=unsel_fg, border_color=unsel_bd, text_color=unsel_tc)

    def _build_face_panel(self, parent):
        ctk.CTkLabel(
            parent, text="Face Scan",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"),
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            parent, text="Face scan is mandatory\nfor all students",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"), justify="center",
        ).pack(pady=(0, 12))

        self.face_widget = FaceCaptureWidget(
            parent, on_complete=self._on_face_done,
            fg_color="transparent",
        )
        self.face_widget.pack(padx=12, pady=(0, 12))

        self.face_lbl = ctk.CTkLabel(
            parent, text="⚠  Please scan face",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#e3b341", "#e3b341"),
        )
        self.face_lbl.pack()
        self._set_warning_style("warning", "Face scan is required before saving.")

    def _on_face_done(self, enc, err):
        if err:
            self.face_lbl.configure(
                text=f"❌ {err}", text_color=("#f85149", "#f85149"))
            self._set_warning_style("error", "Face scan failed. Please retry with proper lighting.")
            self._encoding = None
        else:
            self._encoding = enc
            self.face_lbl.configure(
                text="✅ Face captured!", text_color=("#3fb950", "#3fb950"))
            self._set_warning_style("success", "Face data captured successfully.")

    def _save(self):
        roll = self._entries["roll"].get().strip()
        name = self._entries["name"].get().strip()
        phone = self._entries["phone"].get().strip()
        dept = self.dept_var.get()
        sem = self.sem_var.get()
        shift = self.shift_var.get()

        errs = []
        if not roll:
            errs.append("Roll Number is required")
        if not name:
            errs.append("Name is required")
        if dept == "Select Department":
            errs.append("Please select a Department")
        if not shift:
            errs.append("Please select a Shift")
        if self._encoding is None:
            errs.append("Face scan is required")

        if errs:
            self.status_lbl.configure(
                text="❌ " + " | ".join(errs),
                text_color=("#f85149", "#f85149"))
            self.status_box.configure(fg_color=("#2d1117", "#2d1117"), border_color=("#f85149", "#f85149"))
            return

        try:
            self.save_btn.configure(state="disabled", text="⏳ Saving...")
            add_user_by_admin(roll, name, dept, sem,shift,
                              phone, self._encoding)
            self.status_lbl.configure(
                text=f"✅ '{name}' added successfully!",
                text_color=("#3fb950", "#3fb950"))
            self._set_warning_style("success", f"'{name}' was added successfully.")
            self.save_btn.configure(state="normal", text="💾  Save Student")
            self._clear()
        except ValueError as e:
            self.status_lbl.configure(
                text=f"❌ {e}", text_color=("#f85149", "#f85149"))
            self._set_warning_style("error", str(e))
            self.save_btn.configure(state="normal", text="💾  Save Student")
        except Exception as e:
            self.status_lbl.configure(
                text=f"❌ Error: {e}", text_color=("#f85149", "#f85149"))
            self._set_warning_style("error", f"Error: {e}")
            self.save_btn.configure(state="normal", text="💾  Save Student")

    def _clear(self):
        for e in self._entries.values():
            e.delete(0, "end")
        self.dept_var.set("Select Department")
        self.sem_var.set("1st")
        self.shift_var.set("")
        self._btn_day.configure(
            fg_color=C("bg2"), border_color=C("card_border"),
            text_color=C("text_dim"))
        self._btn_morning.configure(
            fg_color=C("bg2"), border_color=C("card_border"),
            text_color=C("text_dim"))
        self._encoding = None
        self.face_widget._reset()
        self.face_lbl.configure(text="⚠  Please scan face",
                                text_color=("#e3b341", "#e3b341"))
        self._set_warning_style("warning", "Face scan is required before saving.")

    def _lbl(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"), anchor="w",
        ).pack(anchor="w", pady=(10, 3))

    # UI-only interaction polish (no logic changes)
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

    def _set_warning_style(self, level, message):
        styles = {
            "warning": (("#fff7ed", "#2a230d"), ("#f59e0b", "#e3b341"), ("#b45309", "#e3b341")),
            "error":   (("#fef2f2", "#2d1117"), ("#ef4444", "#f85149"), ("#b91c1c", "#f85149")),
            "success": (("#f0fdf4", "#0d2a0f"), ("#22c55e", "#238636"), ("#15803d", "#3fb950")),
        }
        bg, bd, tc = styles.get(level, styles["warning"])
        self.status_box.configure(fg_color=bg, border_color=bd)
        self.status_lbl.configure(text=message, text_color=tc)