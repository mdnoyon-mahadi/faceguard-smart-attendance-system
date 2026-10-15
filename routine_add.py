# ============================================================
# routine_add.py — Admin Routine Add Page
# ============================================================
# Comment translated to English.
#   - Department: free-text entry → fixed dropdown (CST, CT, MT…)
# Comment translated to English.
# Comment translated to English.
# ============================================================

import customtkinter as ctk
from models.routine_model import add_routine
from models.teacher_model import get_all_teachers
from datetime import datetime, timedelta
from theme import ThemeManager

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

DEPARTMENTS = ["CST", "CT", "MT", "ET", "ENT", "PT", "CMT", "THT"]

ENTRY_WINDOW = 10
EXIT_WINDOW = 10
C = ThemeManager.get_color


def _time_options():
    opts = []
    for h in range(7, 21):
        for m in (0, 15, 30, 45):
            opts.append(f"{h:02d}:{m:02d}")
    return opts


def _calc(time_str, delta_min):
    dt = datetime.strptime(time_str, "%H:%M") + timedelta(minutes=delta_min)
    return dt.strftime("%I:%M %p")


def _build_teacher_options(teachers):
    """
       teacher  
    "Name (ID: X)" format   .
    Return: display_label → teacher_id dict
    """
    from collections import Counter
    name_count = Counter(t["name"] for t in teachers)

    label_map = {}   # display label → teachers.id  (INT auto-increment PK)
                     # routines.teacher_id is INT FK → teachers.id
                     # storing teachers.teacher_id (VARCHAR) here causes MySQL
                     # to coerce the string → 0, breaking the JOIN and teacher scan

    for t in teachers:
        name = t["name"]
        if name_count[name] > 1:
            # show the custom teacher_id in the label (for human readability)
            # but store the int PK as the FK value
            display_id = t.get("teacher_id") or t["id"]
            label = f"{name} (ID: {display_id})"
        else:
            label = name
        label_map[label] = t["id"]   # ← INT PK, not the custom varchar teacher_id

    return label_map


class RoutineAddPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Add Routine",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).pack(side="left")

        ctk.CTkFrame(
            self, height=1, fg_color=C("sep"),
        ).pack(fill="x", padx=28, pady=14)

        info = ctk.CTkFrame(
            self, fg_color=C("bg2"),
            corner_radius=8, border_width=1,
            border_color=C("accent3"),
        )
        info.pack(fill="x", padx=28, pady=(0, 14))

        ctk.CTkLabel(
            info,
            text="ℹ️  Entry = Class Start + 10 min  |  Exit = Class End - 10 min → Class End",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C("accent3"),
        ).pack(pady=10, padx=16)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        form_card = ctk.CTkScrollableFrame(
            content,
            fg_color=C("card"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
            scrollbar_fg_color=C("bg2"),
        )
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        preview_panel = ctk.CTkFrame(
            content,
            fg_color=C("card"),
            corner_radius=12,
            border_width=1,
            border_color=C("card_border"),
        )
        preview_panel.grid(row=0, column=1, sticky="nsew")
        preview_panel.grid_columnconfigure(0, weight=1)

        times = _time_options()
        ctk.CTkLabel(
            form_card, text="Routine Configuration",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=C("text"),
        ).pack(anchor="w", padx=14, pady=(12, 6))

        basic_sec = self._make_section(form_card, "Basic Info")
        schedule_sec = self._make_section(form_card, "Schedule")
        time_sec = self._make_section(form_card, "Time")

        self._make_label(basic_sec, "Shift *")
        self.shift_var = ctk.StringVar(value="morning")
        shift_frame = ctk.CTkFrame(basic_sec, fg_color="transparent")
        shift_frame.pack(fill="x", pady=(0, 4))

        for idx, (label, val) in enumerate([("🌅  Morning", "morning"), ("☀️  Day", "day")]):
            ctk.CTkRadioButton(
                shift_frame, text=label,
                variable=self.shift_var, value=val,
                fg_color=C("accent3"),
                hover_color=C("accent"),
                text_color=C("text"),
                font=ctk.CTkFont(family="Segoe UI", size=13),
            ).pack(side="left", padx=(0 if idx == 0 else 10, 0), pady=4)

        self._make_label(basic_sec, "Department *")
        self.dept_var = ctk.StringVar(value=DEPARTMENTS[0])
        self._make_option(basic_sec, self.dept_var, DEPARTMENTS)

        self._make_label(basic_sec, "Semester *")
        self.sem_var = ctk.StringVar(value="1st")
        self._make_option(basic_sec, self.sem_var,
                          ["1st", "2nd", "3rd", "4th",
                           "5th", "6th", "7th"])

        self._make_label(schedule_sec, "Day *")
        self.day_var = ctk.StringVar(value="Monday")
        self._make_option(schedule_sec, self.day_var, DAYS)

        self._make_label(schedule_sec, "Subject *")
        self.subject_entry = self._make_entry(
            schedule_sec, "e.g. Data Structures")

        # Teacher dropdown  +  Teacher ID (read-only)
        teachers = get_all_teachers()
        if teachers:
            self._teacher_map = _build_teacher_options(teachers)
            names = list(self._teacher_map.keys())
        else:
            self._teacher_map = {}
            names = ["— No teachers added yet —"]

        self._make_label(schedule_sec, "Teacher *")
        self.teacher_var = ctk.StringVar(value=names[0])
        self.teacher_var.trace_add(
            "write", lambda *_: self._update_teacher_id())
        self._make_option(schedule_sec, self.teacher_var, names)

        self._make_label(schedule_sec, "Teacher ID",
                         hint="(auto-fill)")
        self.teacher_id_entry = ctk.CTkEntry(
            schedule_sec, height=38,
            fg_color=C("bg2"),
            border_color=C("card_border"),
            text_color=C("accent3"),
            state="disabled",
            corner_radius=8,
        )
        self.teacher_id_entry.pack(fill="x")
        self._update_teacher_id()

        time_range_card = ctk.CTkFrame(
            time_sec,
            fg_color=C("bg2"),
            corner_radius=10,
            border_width=1,
            border_color=C("card_border"),
        )
        time_range_card.pack(fill="x", pady=(4, 2))

        self._make_label(time_range_card, "Class Start Time *",
                         hint="(Scan begins from here)")
        self.class_start_var = ctk.StringVar(value="08:00")
        self.class_start_menu = self._make_time_option(
            time_range_card, self.class_start_var, times)

        self._make_label(time_range_card, "Class End Time *",
                         hint="(Scan ends here)")
        self.class_end_var = ctk.StringVar(value="09:00")
        self.class_end_menu = self._make_time_option(
            time_range_card, self.class_end_var, times)

        ctk.CTkLabel(
            preview_panel, text="Scan Window Preview",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"),
        ).pack(anchor="w", padx=16, pady=(16, 6))
        ctk.CTkLabel(
            preview_panel,
            text="Auto-calculated from selected class time",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"),
        ).pack(anchor="w", padx=16, pady=(0, 10))

        preview = ctk.CTkFrame(
            preview_panel, fg_color=C("bg2"),
            corner_radius=10, border_width=1,
            border_color=C("card_border"),
        )
        preview.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            preview, text="Scan Range Preview",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=C("text_dim"),
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self.preview_entry_lbl = ctk.CTkLabel(
            preview, text="🟢 Entry:  —",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#3fb950", "#3fb950"), anchor="w",
        )
        self.preview_entry_lbl.pack(anchor="w", padx=12, pady=2)

        self.preview_exit_lbl = ctk.CTkLabel(
            preview, text="🔵 Exit:    —",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#58a6ff", "#58a6ff"), anchor="w",
        )
        self.preview_exit_lbl.pack(anchor="w", padx=12, pady=(2, 10))

        self.class_start_var.trace_add(
            "write", lambda *_: self._update_preview())
        self.class_end_var.trace_add(
            "write", lambda *_: self._update_preview())
        self._update_preview()

        self._bind_hover_card(preview, base_color=C(
            "bg2"), hover_color=C("hover"))

        self.status_box = ctk.CTkFrame(
            form_card,
            fg_color=C("bg2"),
            corner_radius=8,
            border_width=1,
            border_color=C("card_border"),
        )
        self.status_box.pack(fill="x", padx=14, pady=(12, 8))

        self.status_lbl = ctk.CTkLabel(
            self.status_box, text="Ready to save routine.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C("text_dim"),
            anchor="w",
            justify="left",
        )
        self.status_lbl.pack(fill="x", padx=10, pady=8)

        self.save_btn = ctk.CTkButton(
            form_card,
            text="💾  Save Routine",
            height=46,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=C("accent3"),
            hover_color=C("accent"),
            corner_radius=10,
            command=self._save,
        )
        self.save_btn.pack(fill="x", padx=14, pady=(0, 12))
        self._bind_primary_hover(self.save_btn)

    # ──────────────────────────────────────────────────────────
    # Teacher ID auto-fill
    # ──────────────────────────────────────────────────────────

    def _update_teacher_id(self):
        label = self.teacher_var.get()
        tid = self._teacher_map.get(label, "")
        display = str(tid) if tid else "—"

        self.teacher_id_entry.configure(state="normal")
        self.teacher_id_entry.delete(0, "end")
        self.teacher_id_entry.insert(0, display)
        self.teacher_id_entry.configure(state="disabled")

    # ──────────────────────────────────────────────────────────
    # Preview
    # ──────────────────────────────────────────────────────────

    def _update_preview(self):
        try:
            cs = self.class_start_var.get()
            ce = self.class_end_var.get()
            entry_e = _calc(cs,  ENTRY_WINDOW)
            exit_s = _calc(ce, -EXIT_WINDOW)
            cs_fmt = _calc(cs,  0)
            ce_fmt = _calc(ce,  0)
            self.preview_entry_lbl.configure(
                text=f"🟢 Entry:  {cs_fmt}  →  {entry_e}")
            self.preview_exit_lbl.configure(
                text=f"🔵 Exit:    {exit_s}  →  {ce_fmt}")
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def _make_label(self, parent, text, hint=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(anchor="w", pady=(12, 2))
        ctk.CTkLabel(
            row, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C("text_dim"),
        ).pack(side="left")
        if hint:
            ctk.CTkLabel(
                row, text=hint,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=C("text_dim"),
            ).pack(side="left", padx=6)

    def _make_entry(self, parent, placeholder):
        e = ctk.CTkEntry(
            parent, placeholder_text=placeholder, height=38,
            fg_color=C("bg2"),
            border_color=C("card_border"),
            text_color=C("text"),
            placeholder_text_color=C("text_dim"),
            corner_radius=8,
        )
        e.pack(fill="x")
        self._bind_entry_focus(e)
        return e

    def _make_option(self, parent, var, values):
        """Standard dropdown for short lists (department, semester, day, teacher)."""
        menu = ctk.CTkOptionMenu(
            parent, variable=var, values=values,
            fg_color=C("bg2"),
            button_color=C("card_border"),
            button_hover_color=C("hover"),
            text_color=C("text"),
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            height=38, anchor="w",
            corner_radius=8,
        )
        menu.pack(fill="x")
        return menu

    def _make_time_option(self, parent, var, values):
        """
        Scrollable CTkComboBox for time selection.
        - Dropdown height সীমিত (OS native scroll সহ)
        - Mouse wheel দিয়ে সরাসরি value পরিবর্তন করা যাবে
        """
        combo = ctk.CTkComboBox(
            parent, variable=var, values=values,
            fg_color=C("bg2"),
            border_color=C("card_border"),
            button_color=C("card_border"),
            button_hover_color=C("hover"),
            text_color=C("text"),
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            dropdown_text_color=C("text"),
            height=36,
            corner_radius=8,
            state="readonly",
        )
        combo.pack(fill="x")

        # Mouse scroll দিয়ে time বাড়ানো/কমানো
        def _on_scroll(event):
            current = var.get()
            try:
                idx = values.index(current)
                if event.delta > 0 or event.num == 4:   # scroll up → earlier time
                    idx = max(0, idx - 1)
                else:                                     # scroll down → later time
                    idx = min(len(values) - 1, idx + 1)
                var.set(values[idx])
            except ValueError:
                pass

        combo.bind("<MouseWheel>", _on_scroll)  # Windows / macOS
        combo.bind("<Button-4>", _on_scroll)    # Linux scroll up
        combo.bind("<Button-5>", _on_scroll)    # Linux scroll down

        return combo

    def _make_section(self, parent, title):
        sec = ctk.CTkFrame(
            parent,
            fg_color=C("bg"),
            corner_radius=10,
            border_width=1,
            border_color=C("card_border"),
        )
        sec.pack(fill="x", padx=14, pady=(6, 8))
        ctk.CTkLabel(
            sec, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=C("text"),
        ).pack(anchor="w", padx=12, pady=(10, 0))
        inner = ctk.CTkFrame(sec, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(4, 10))
        return inner

    def _bind_entry_focus(self, entry):
        def _focus_in(_e):
            entry.configure(border_color=C("accent3"))

        def _focus_out(_e):
            entry.configure(border_color=C("card_border"))
        entry.bind("<FocusIn>", _focus_in)
        entry.bind("<FocusOut>", _focus_out)

    def _bind_primary_hover(self, btn):
        def _enter(_e):
            btn.configure(
                fg_color=C("accent"),
                border_width=1,
                border_color=C("accent"),
                font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
            )

        def _leave(_e):
            btn.configure(
                fg_color=C("accent3"),
                border_width=0,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
            )
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    def _bind_input_hover(self, widget):
        def _enter(_e):
            widget.configure(fg_color=C("hover"), button_color=C("accent3"))

        def _leave(_e):
            widget.configure(fg_color=C("bg2"), button_color=C("card_border"))

        widget.bind("<Enter>", _enter, add="+")
        widget.bind("<Leave>", _leave, add="+")

    def _bind_hover_card(self, frame, base_color, hover_color):
        def _is_descendant_of(widget, ancestor):
            cur = widget
            while cur is not None:
                if cur == ancestor:
                    return True
                cur = cur.master
            return False

        def _set_hover(active):
            frame.configure(
                fg_color=hover_color if active else base_color,
                border_color=C("accent3") if active else C("card_border")
            )

        def _on_enter(_event):
            _set_hover(True)

        def _on_leave(_event):
            px, py = frame.winfo_pointerxy()
            hovered_widget = frame.winfo_containing(px, py)
            if hovered_widget is not None and _is_descendant_of(hovered_widget, frame):
                return
            _set_hover(False)

        frame.bind("<Enter>", _on_enter, add="+")
        frame.bind("<Leave>", _on_leave, add="+")
        for child in frame.winfo_children():
            child.bind("<Enter>", _on_enter, add="+")
            child.bind("<Leave>", _on_leave, add="+")

    # ──────────────────────────────────────────────────────────
    # Save
    # ──────────────────────────────────────────────────────────

    def _save(self):
        dept = self.dept_var.get()
        sem = self.sem_var.get()
        day = self.day_var.get()
        subject = self.subject_entry.get().strip()
        teacher_name = self.teacher_var.get()
        teacher_id = self._teacher_map.get(teacher_name)
        c_start = self.class_start_var.get()
        c_end = self.class_end_var.get()
        shift = self.shift_var.get()

        errors = []
        if not subject:
            errors.append("Subject is required")
        if not teacher_id:
            errors.append("Please select a Teacher")
        if c_start >= c_end:
            errors.append("Class end time must be after start time")

        if errors:
            self.status_lbl.configure(
                text="❌ " + " | ".join(errors),
                text_color=("#f85149", "#f85149"),
            )
            self.status_box.configure(
                fg_color=("#2d1117", "#2d1117"),
                border_color=("#f85149", "#f85149"),
            )
            return

        try:
            self.save_btn.configure(state="disabled", text="⏳ Saving...")
            add_routine(dept, sem, day, subject, teacher_id,
                        c_start, c_end, shift)
            self.status_lbl.configure(
                text="✅ Routine saved!",
                text_color=("#3fb950", "#3fb950"),
            )
            self.status_box.configure(
                fg_color=("#0d2a0f", "#0d2a0f"),
                border_color=("#238636", "#238636"),
            )
            self.save_btn.configure(state="normal", text="💾  Save Routine")
            self._clear_form()
        except Exception as e:
            self.status_lbl.configure(
                text=f"❌ Error: {e}",
                text_color=("#f85149", "#f85149"),
            )
            self.status_box.configure(
                fg_color=("#2d1117", "#2d1117"),
                border_color=("#f85149", "#f85149"),
            )
            self.save_btn.configure(state="normal", text="💾  Save Routine")

    # ──────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────

    def _clear_form(self):
        self.subject_entry.delete(0, "end")
        self.shift_var.set("morning")
        self.dept_var.set(DEPARTMENTS[0])
        self.sem_var.set("1st")
        self.day_var.set("Monday")
        self.class_start_var.set("08:00")
        self.class_end_var.set("09:00")
        self.status_box.configure(
            fg_color=C("bg2"), border_color=C("card_border"))
        self.status_lbl.configure(
            text="Ready to save routine.", text_color=C("text_dim"))
        if self._teacher_map:
            self.teacher_var.set(list(self._teacher_map.keys())[0])