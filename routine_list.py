# ============================================================
# routine_list.py  —  Routine List Page  (v5 - All Fixed)
# Fix 1: Edit modal — teacher_id employee ID দিয়ে save হবে
# Fix 2: Student routine — teacher name JOIN fix (t.teacher_id)
# Fix 3: Teacher search ComboBox — width কমানো হয়েছে
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from theme import ThemeManager
from models.routine_model import (
    get_all_routines, delete_routine, update_routine,
    get_routine_by_id,
    search_routines_for_student, search_routines_for_teacher,
)
from models.teacher_model import get_all_teachers

# ── Constants ─────────────────────────────────────────────────
DAY_COLOR = {
    "Monday":    "#1f6feb", "Tuesday":  "#238636",
    "Wednesday": "#6e40c9", "Thursday": "#e3b341",
    "Friday":    "#f85149", "Saturday": "#3fb950",
    "Sunday":    "#db6d28",
}
DAYS_ORDER = ["Monday", "Tuesday", "Wednesday",
              "Thursday", "Friday", "Saturday", "Sunday"]
SEMESTERS = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
SHIFTS = ["morning", "day"]
DEPARTMENTS = ["CST", "CT", "MT", "ET", "ENT", "PT", "CMT", "THT"]

C = ThemeManager.get_color

# Palette
BG = "#0d1117"
SURFACE = "#161b22"
SURFACE2 = "#21262d"
BORDER = "#30363d"
TEXT_PRI = "#e6edf3"
TEXT_SEC = "#8b949e"
TEXT_MUT = "#484f58"
BLUE = "#1f6feb"
BLUE_HV = "#388bfd"
GREEN = "#238636"
RED = "#f85149"
RED_BG = "#2d1117"
RED_BD = "#6e2020"
AMBER = "#e3b341"

# ── Student view columns
S_HDR = ["#", "Subject", "Dept", "Sem", "Teacher", "Class Time", "Shift"]
S_COL = [30,   220,       75,    48,    165,        145,          85]

# ── Teacher view columns
T_HDR = ["#", "Subject", "Dept", "Sem",
         "Teacher", "Class Time", "Shift", "", ""]
T_COL = [30,   195,       75,    48,
         155,        140,          80,      72, 72]


def _fmt_time(val):
    return str(val)[:5] if val else "—"


def _td_to_hhmm(val):
    if val is None:
        return "—"
    if hasattr(val, "total_seconds"):
        total = int(val.total_seconds())
        h, m = total // 3600, (total % 3600) // 60
    else:
        h, m = val.hour, val.minute
    return datetime(2000, 1, 1, h % 24, m % 60).strftime("%I:%M %p")


def _clean(text: str) -> str:
    return text.strip("{}").strip() if text else text


def _font(size=12, bold=False):
    return ctk.CTkFont(family="Segoe UI", size=size,
                       weight="bold" if bold else "normal")


# ══════════════════════════════════════════════════════════════
# Edit Modal
# FIX 1: Teacher ID এখন employee ID (teacher_id) দিয়ে save হবে
#         Teacher dropdown থেকে select করা যাবে
# ══════════════════════════════════════════════════════════════
class _EditRoutineModal(ctk.CTkToplevel):
    def __init__(self, parent, routine_id: int, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._routine_id = routine_id
        self._on_save = on_save
        self._teacher_map = {}   # label → teacher_id (employee id)

        self.title("Edit Routine")
        self.geometry("760x560")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()
        self._center()

        try:
            self._data = get_routine_by_id(routine_id)
        except Exception as e:
            messagebox.showerror("Error", f"Routine load error: {e}")
            self.destroy()
            return

        if not self._data:
            messagebox.showerror("Error", "Routine not found.")
            self.destroy()
            return

        self._load_teachers()
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"760x560+{(sw-760)//2}+{(sh-560)//2}")

    def _load_teachers(self):
        """Teachers load করে dropdown এর জন্য label→teacher_id map তৈরি করো"""
        try:
            teachers = get_all_teachers() or []
        except Exception:
            teachers = []

        self._teacher_map = {}
        self._teacher_labels = []

        for t in teachers:
            name = _clean(t.get("name") or "Unnamed")
            display_id = t.get("teacher_id") or t.get("id") or ""
            label = f"{name}  |  ID: {display_id}"
            # Store the database primary key 'id' in the map for routines FK consistency
            self._teacher_map[label] = t["id"]
            self._teacher_labels.append(label)

    def _find_current_teacher_label(self, current_teacher_id):
        """Current teacher_id (db id) দিয়ে dropdown label খুঁজে বের করো"""
        for label, db_id in self._teacher_map.items():
            if str(db_id) == str(current_teacher_id):
                return label
        return self._teacher_labels[0] if self._teacher_labels else ""

    def _entry(self, parent, placeholder="", initial="", width=None):
        kw = dict(placeholder_text=placeholder, height=34,
                  fg_color=SURFACE2, border_color=BORDER,
                  text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
                  font=_font(12))
        if width:
            kw["width"] = width
        e = ctk.CTkEntry(parent, **kw)
        if initial:
            e.insert(0, initial)
        return e

    def _opt(self, parent, values, initial=""):
        var = ctk.StringVar(value=initial or values[0])
        om = ctk.CTkOptionMenu(parent, variable=var, values=values,
                               fg_color=SURFACE2, button_color=BORDER,
                               button_hover_color=TEXT_MUT, text_color=TEXT_PRI,
                               dropdown_fg_color=SURFACE, font=_font(12), height=34)
        return om, var

    def _lbl(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=_font(10),
                     text_color=TEXT_MUT).pack(anchor="w", pady=(0, 2))

    def _build(self):
        d = self._data

        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="✏️  Edit Routine", font=_font(15, bold=True),
                     text_color=TEXT_PRI).place(relx=.5, rely=.5, anchor="center")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # Row 1: Dept | Semester | Shift | Day
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))

        for col_data in [
            ("Department", "_dept_e",    None, "entry",
             "e.g. CST",  d.get("department", "")),
            ("Semester",   "_sem_var",   None, "option",
             SEMESTERS,   d.get("semester", SEMESTERS[0])),
            ("Shift",      "_shift_var", None, "option",
             SHIFTS,       d.get("shift", SHIFTS[0])),
            ("Day",        "_day_var",   None, "option",
             DAYS_ORDER,   d.get("day", DAYS_ORDER[0])),
        ]:
            label, attr, _, kind, opts, val = col_data
            c = ctk.CTkFrame(row1, fg_color="transparent")
            c.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self._lbl(c, label)
            if kind == "entry":
                w = self._entry(c, opts, val)
                w.pack(fill="x")
                setattr(self, attr, w)
            else:
                om, var = self._opt(c, opts, val)
                om.pack(fill="x")
                setattr(self, attr, var)

        # Row 2: Subject | Teacher dropdown
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))

        # Subject
        c = ctk.CTkFrame(row2, fg_color="transparent")
        c.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._lbl(c, "Subject")
        self._subj_e = self._entry(c, "e.g. Mathematics", d.get("subject", ""))
        self._subj_e.pack(fill="x")

        # FIX 1: Teacher ID entry এর বদলে Teacher Dropdown
        c2 = ctk.CTkFrame(row2, fg_color="transparent")
        c2.pack(side="left", fill="x", expand=True)
        self._lbl(c2, "Teacher  (employee ID auto-fill)")

        current_tid = d.get("teacher_id") or ""
        current_label = self._find_current_teacher_label(current_tid)

        if self._teacher_labels:
            self._teacher_var = ctk.StringVar(value=current_label)
            self._teacher_om = ctk.CTkOptionMenu(
                c2,
                variable=self._teacher_var,
                values=self._teacher_labels,
                fg_color=SURFACE2, button_color=BORDER,
                button_hover_color=TEXT_MUT, text_color=TEXT_PRI,
                dropdown_fg_color=SURFACE, font=_font(11), height=34,
                dynamic_resizing=False,
            )
            self._teacher_om.pack(fill="x")
        else:
            # teacher না থাকলে manual entry
            self._teacher_var = None
            self._lbl(c2, "Teacher ID (employee id)")
            self._tid_e = self._entry(c2, "e.g. 850201", str(current_tid))
            self._tid_e.pack(fill="x")

        # Row 3: Class Start | Class End
        row3 = ctk.CTkFrame(body, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 4))

        c = ctk.CTkFrame(row3, fg_color="transparent")
        c.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._lbl(c, "Class Start  (HH:MM)")
        self._cs_e = self._entry(c, "08:00", _fmt_time(d.get("class_start")))
        self._cs_e.pack(fill="x")

        c2 = ctk.CTkFrame(row3, fg_color="transparent")
        c2.pack(side="left", fill="x", expand=True)
        self._lbl(c2, "Class End  (HH:MM)")
        self._ce_e = self._entry(c2, "09:30", _fmt_time(d.get("class_end")))
        self._ce_e.pack(fill="x")

        ctk.CTkLabel(body,
                     text="💡  Teacher dropdown থেকে select করো।  Time must be HH:MM.",
                     font=_font(10), text_color=TEXT_MUT).pack(anchor="w", pady=(4, 0))

        self._err_lbl = ctk.CTkLabel(body, text="", font=_font(11),
                                     text_color=(RED, RED))
        self._err_lbl.pack(anchor="w", pady=(6, 0))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))

        ctk.CTkButton(btn_row, text="Cancel", width=110, height=36,
                      fg_color="transparent", border_width=1,
                      border_color=BORDER, text_color=TEXT_SEC,
                      hover_color=SURFACE2, font=_font(12),
                      command=self.destroy).pack(side="right", padx=(8, 0))

        ctk.CTkButton(btn_row, text="💾  Save Changes", width=150, height=36,
                      fg_color=BLUE, hover_color=BLUE_HV,
                      text_color=TEXT_PRI, font=_font(12, bold=True),
                      corner_radius=8, command=self._save).pack(side="right")

    def _save(self):
        dept = self._dept_e.get().strip()
        semester = self._sem_var.get()
        shift = self._shift_var.get()
        day = self._day_var.get()
        subject = self._subj_e.get().strip()
        cs_raw = self._cs_e.get().strip()
        ce_raw = self._ce_e.get().strip()

        # FIX 1: Teacher ID — dropdown / manual entry থেকে auto-increment PK 'id' নাও
        if self._teacher_var is not None:
            selected_label = self._teacher_var.get()
            tid_val = self._teacher_map.get(selected_label, "")
            tid_raw = str(tid_val).strip()
        else:
            manual_tid = self._tid_e.get().strip()
            if manual_tid:
                from database.db_connection import execute_query
                t_row = execute_query(
                    "SELECT id FROM teachers WHERE teacher_id=%s OR id=%s",
                    (manual_tid, manual_tid), fetch="one"
                )
                if t_row:
                    tid_raw = str(t_row["id"])
                else:
                    tid_raw = manual_tid
            else:
                tid_raw = ""

        if not dept:
            self._err("Please enter Department.")
            return
        if not subject:
            self._err("Please enter Subject.")
            return
        if not tid_raw:
            self._err("Teacher select করো অথবা ID দাও।")
            return
        try:
            datetime.strptime(cs_raw, "%H:%M")
            datetime.strptime(ce_raw, "%H:%M")
        except ValueError:
            self._err("Class Start / End must be HH:MM.")
            return
        if cs_raw >= ce_raw:
            self._err("Class End must be after Class Start.")
            return

        try:
            update_routine(
                routine_id=self._routine_id,
                department=dept,
                semester=semester,
                day=day,
                subject=subject,
                teacher_id=int(tid_raw),   # DB auto-increment ID হিসেবে save
                class_start=cs_raw,
                class_end=ce_raw,
                shift=shift,
            )
        except Exception as e:
            self._err(f"DB Error: {e}")
            return

        self.destroy()
        if self._on_save:
            self._on_save()

    def _err(self, msg):
        self._err_lbl.configure(text=f"⚠️  {msg}")


# ══════════════════════════════════════════════════════════════
# Table header
# ══════════════════════════════════════════════════════════════
def _draw_table_header(parent, headers, col_widths):
    hdr = ctk.CTkFrame(parent, fg_color=SURFACE2, corner_radius=6,
                       border_width=1, border_color=BORDER)
    hdr.pack(fill="x", pady=(0, 2))
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        ctk.CTkLabel(hdr, text=h, width=w, font=_font(11, bold=True),
                     text_color=TEXT_SEC, anchor="w").grid(
            row=0, column=i,
            padx=(14 if i == 0 else 6, 0),
            pady=7, sticky="w")
    return hdr


# ══════════════════════════════════════════════════════════════
# Student Row
# FIX 2: teacher_name None/empty হলে "—" দেখাবে
# ══════════════════════════════════════════════════════════════
class _StudentRow(ctk.CTkFrame):
    def __init__(self, parent, idx, routine, **kwargs):
        super().__init__(parent, fg_color=C("card"), corner_radius=6,
                         border_width=1, border_color=C("card_border"), **kwargs)

        r = routine
        cs = _td_to_hhmm(r["class_start"])
        ce = _td_to_hhmm(r["class_end"])
        si = "🌅" if r.get("shift") == "morning" else "☀️"
        subj = _clean(r.get("subject", "—"))

        # FIX 2: teacher_name সঠিকভাবে handle করো
        tname_raw = r.get("teacher_name")
        tname = _clean(tname_raw) if tname_raw else "—"
        if not tname or tname in ("None", "null", ""):
            tname = "—"

        cells = [
            (str(idx),                 S_COL[0], TEXT_MUT, "center"),
            (subj,                     S_COL[1], TEXT_PRI, "w"),
            (r.get("department", "—"), S_COL[2], TEXT_SEC, "center"),
            (r.get("semester", "—"),   S_COL[3], TEXT_SEC, "center"),
            (tname,                    S_COL[4], TEXT_SEC, "w"),
            (f"{cs} – {ce}",           S_COL[5], TEXT_SEC, "center"),
            (f"{si} {r.get('shift','').title()}", S_COL[6], AMBER, "center"),
        ]

        for col_i, (val, w, color, anchor) in enumerate(cells):
            ctk.CTkLabel(self, text=val, width=w, font=_font(12),
                         text_color=(color, color), anchor=anchor,
                         wraplength=w - 8).grid(
                row=0, column=col_i,
                padx=(14 if col_i == 0 else 6, 0),
                pady=8, sticky="w")

        self._bind_hover()

    def _bind_hover(self):
        def _enter(_e):
            self.configure(fg_color=C("hover"), border_color=BLUE)

        def _leave(_e):
            self.configure(fg_color=C("card"), border_color=C("card_border"))
        for w in [self] + self.winfo_children():
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")


# ══════════════════════════════════════════════════════════════
# Teacher Row — with edit/delete buttons
# ══════════════════════════════════════════════════════════════
class _TeacherRow(ctk.CTkFrame):
    def __init__(self, parent, idx, routine,
                 edit_cb=None, delete_cb=None, **kwargs):
        super().__init__(parent, fg_color=C("card"), corner_radius=6,
                         border_width=1, border_color=C("card_border"), **kwargs)

        r = routine
        cs = _td_to_hhmm(r["class_start"])
        ce = _td_to_hhmm(r["class_end"])
        si = "🌅" if r.get("shift") == "morning" else "☀️"
        subj = _clean(r.get("subject", "—"))

        tname_raw = r.get("teacher_name")
        tname = _clean(tname_raw) if tname_raw else "—"
        if not tname or tname in ("None", "null", ""):
            tname = "—"

        cells = [
            (str(idx),                 T_COL[0], TEXT_MUT, "center"),
            (subj,                     T_COL[1], TEXT_PRI, "w"),
            (r.get("department", "—"), T_COL[2], TEXT_SEC, "center"),
            (r.get("semester", "—"),   T_COL[3], TEXT_SEC, "center"),
            (tname,                    T_COL[4], TEXT_SEC, "w"),
            (f"{cs} – {ce}",           T_COL[5], TEXT_SEC, "center"),
            (f"{si} {r.get('shift','').title()}", T_COL[6], AMBER, "center"),
        ]

        for col_i, (val, w, color, anchor) in enumerate(cells):
            ctk.CTkLabel(self, text=val, width=w, font=_font(12),
                         text_color=(color, color), anchor=anchor,
                         wraplength=w - 8).grid(
                row=0, column=col_i,
                padx=(14 if col_i == 0 else 6, 0),
                pady=8, sticky="w")

        col_e = len(cells)

        if edit_cb:
            ctk.CTkButton(self, text="✏ Edit", width=T_COL[7], height=28,
                          fg_color="transparent", border_width=1,
                          border_color=BLUE, text_color=BLUE,
                          hover_color=SURFACE2, font=_font(11), corner_radius=6,
                          command=edit_cb).grid(row=0, column=col_e,
                                                padx=(6, 3), pady=5)
            col_e += 1

        if delete_cb:
            ctk.CTkButton(self, text="🗑 Del", width=T_COL[8], height=28,
                          fg_color="transparent", border_width=1,
                          border_color=RED, text_color=RED,
                          hover_color=RED_BG, font=_font(11), corner_radius=6,
                          command=delete_cb).grid(row=0, column=col_e,
                                                  padx=(3, 10), pady=5)

        self._bind_hover()

    def _bind_hover(self):
        def _enter(_e):
            self.configure(fg_color=C("hover"), border_color=BLUE)

        def _leave(_e):
            self.configure(fg_color=C("card"), border_color=C("card_border"))
        for w in [self] + self.winfo_children():
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")


# ══════════════════════════════════════════════════════════════
# Main Page
# ══════════════════════════════════════════════════════════════
class RoutineListPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._all_teachers = []
        self._teacher_options = []
        self._teacher_option_map = {}
        self._teacher_routines = []
        self._teacher_combo_ready = False
        self._teacher_combo_updating = False
        self._after_id = None
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────
    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))
        ctk.CTkLabel(top, text="Routine List",
                     font=_font(22, bold=True),
                     text_color=C("text")).pack(side="left")
        ctk.CTkLabel(top, text=f"📅  {datetime.now().strftime('%A, %d %B %Y')}",
                     font=_font(12), text_color=C("text_dim")).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=C("sep")
                     ).pack(fill="x", padx=28, pady=14)

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_fg_color=C("bg2"))
        self._scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        self._build_search_card()
        self._build_result_area()

    # ── Search card ───────────────────────────────────────────
    def _build_search_card(self):
        card = ctk.CTkFrame(self._scroll, fg_color=SURFACE,
                            corner_radius=12, border_width=1,
                            border_color=BORDER)
        card.pack(fill="x", pady=(0, 16))

        tab_bg = ctk.CTkFrame(card, fg_color=SURFACE2, corner_radius=20)
        tab_bg.pack(anchor="center", pady=(14, 10))

        self._tab_var = ctk.StringVar(value="student")

        self._btn_student = ctk.CTkButton(
            tab_bg, text="🎓  Student", height=34, corner_radius=17,
            font=_font(12, bold=True), width=130,
            command=lambda: self._set_tab("student"))
        self._btn_student.pack(side="left", padx=2, pady=2)

        self._btn_teacher = ctk.CTkButton(
            tab_bg, text="👨‍🏫  Teacher", height=34, corner_radius=17,
            font=_font(12, bold=True), width=130,
            command=lambda: self._set_tab("teacher"))
        self._btn_teacher.pack(side="left", padx=2, pady=2)

        self._student_form = ctk.CTkFrame(card, fg_color="transparent")
        self._student_form.pack(fill="x", padx=20, pady=(0, 14))
        self._build_student_form(self._student_form)

        self._teacher_form = ctk.CTkFrame(card, fg_color="transparent")
        self._teacher_form.pack_forget()
        self._build_teacher_form(self._teacher_form)

        self._refresh_tab_style()

    def _set_tab(self, tab):
        self._tab_var.set(tab)
        self._refresh_tab_style()
        self._clear_results()
        if tab == "student":
            self._teacher_form.pack_forget()
            self._student_form.pack(fill="x", padx=20, pady=(0, 14))
        else:
            self._student_form.pack_forget()
            self._teacher_form.pack(fill="x", padx=20, pady=(0, 14))

    def _refresh_tab_style(self):
        is_s = self._tab_var.get() == "student"
        self._btn_student.configure(
            fg_color=BLUE if is_s else "transparent",
            text_color=TEXT_PRI if is_s else TEXT_SEC,
            hover_color=BLUE_HV if is_s else BORDER)
        self._btn_teacher.configure(
            fg_color=BLUE if not is_s else "transparent",
            text_color=TEXT_PRI if not is_s else TEXT_SEC,
            hover_color=BLUE_HV if not is_s else BORDER)

    # ── Student form ──────────────────────────────────────────
    def _build_student_form(self, parent):
        ctk.CTkLabel(parent,
                     text="🎓  Student Routine — Department / Semester / Shift",
                     font=_font(13, bold=True), text_color=TEXT_PRI
                     ).pack(anchor="w", pady=(14, 10))

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="s")
        row.grid_columnconfigure(3, weight=0)

        c = ctk.CTkFrame(row, fg_color="transparent")
        c.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(c, text="Department", font=_font(11),
                     text_color=TEXT_SEC).pack(anchor="w")
        self._s_dept_var = ctk.StringVar(value=DEPARTMENTS[0])
        ctk.CTkOptionMenu(c, variable=self._s_dept_var, values=DEPARTMENTS,
                          fg_color=SURFACE2, button_color=BORDER,
                          button_hover_color=TEXT_MUT, text_color=TEXT_PRI,
                          dropdown_fg_color=SURFACE, font=_font(12), height=36
                          ).pack(fill="x")

        c2 = ctk.CTkFrame(row, fg_color="transparent")
        c2.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(c2, text="Semester", font=_font(11),
                     text_color=TEXT_SEC).pack(anchor="w")
        self._s_sem_var = ctk.StringVar(value=SEMESTERS[0])
        ctk.CTkOptionMenu(c2, variable=self._s_sem_var, values=SEMESTERS,
                          fg_color=SURFACE2, button_color=BORDER,
                          button_hover_color=TEXT_MUT, text_color=TEXT_PRI,
                          dropdown_fg_color=SURFACE, font=_font(12), height=36
                          ).pack(fill="x")

        c3 = ctk.CTkFrame(row, fg_color="transparent")
        c3.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(c3, text="Shift", font=_font(11),
                     text_color=TEXT_SEC).pack(anchor="w")
        self._s_shift_var = ctk.StringVar(value=SHIFTS[0])
        ctk.CTkOptionMenu(c3, variable=self._s_shift_var, values=SHIFTS,
                          fg_color=SURFACE2, button_color=BORDER,
                          button_hover_color=TEXT_MUT, text_color=TEXT_PRI,
                          dropdown_fg_color=SURFACE, font=_font(12), height=36
                          ).pack(fill="x")

        c4 = ctk.CTkFrame(row, fg_color="transparent")
        c4.grid(row=0, column=3, sticky="s")
        ctk.CTkLabel(c4, text=" ", font=_font(11)).pack(anchor="w")
        ctk.CTkButton(c4, text="🔍  Search", height=36, width=120,
                      fg_color=BLUE, hover_color=BLUE_HV,
                      text_color=TEXT_PRI, font=_font(12, bold=True),
                      corner_radius=8,
                      command=self._search_student).pack()

    # ── Teacher form — FIX 3: ComboBox width কমানো হয়েছে ─────
    def _build_teacher_form(self, parent):
        self._load_teacher_search_data()

        ctk.CTkLabel(
            parent,
            text="👨‍🏫  Teacher Routine",
            font=_font(13, bold=True),
            text_color=TEXT_PRI,
        ).pack(anchor="w", pady=(14, 10))

        row = ctk.CTkFrame(parent, fg_color="transparent")
        # FIX 3: fill="x" এর বদলে anchor="w" — stretch বন্ধ
        row.pack(anchor="w")

        field = ctk.CTkFrame(row, fg_color="transparent")
        field.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            field,
            text="Teacher",
            font=_font(11),
            text_color=TEXT_SEC,
        ).pack(anchor="w")

        self._teacher_search_var = ctk.StringVar(value="")
        self._teacher_combo = ctk.CTkComboBox(
            field,
            variable=self._teacher_search_var,
            values=self._teacher_options or ["No teachers found"],
            width=320,          # FIX 3: fixed width — আগে full stretch ছিল
            height=38,
            fg_color=SURFACE2,
            border_color=BORDER,
            button_color=BORDER,
            button_hover_color=BLUE,
            dropdown_fg_color=SURFACE,
            dropdown_hover_color=C("hover"),
            dropdown_text_color=TEXT_PRI,
            text_color=TEXT_PRI,
            font=_font(12),
            dropdown_font=_font(12),
            command=self._on_teacher_combo_select,
            state="normal",
        )
        self._teacher_combo.pack()
        self._teacher_combo.bind("<Enter>", self._teacher_combo_enter, add="+")
        self._teacher_combo.bind("<Leave>", self._teacher_combo_leave, add="+")
        self._teacher_combo.bind(
            "<FocusIn>", self._teacher_combo_enter, add="+")
        self._teacher_combo.bind(
            "<FocusOut>", self._teacher_combo_leave, add="+")
        if hasattr(self._teacher_combo, "_entry"):
            self._teacher_combo._entry.bind(
                "<KeyRelease>", self._on_teacher_combo_key, add="+")

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="left", anchor="s")
        ctk.CTkLabel(actions, text=" ", font=_font(11)).pack(anchor="w")
        ctk.CTkButton(
            actions,
            text="Clear",
            height=38,
            width=84,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            hover_color=SURFACE2,
            text_color=TEXT_PRI,
            font=_font(12, bold=True),
            corner_radius=8,
            command=self._clear_teacher_dropdown,
        ).pack()

        self._teacher_search_var.trace_add(
            "write", self._on_teacher_combo_change)
        self._teacher_combo_ready = True

    def _teacher_combo_enter(self, _event=None):
        try:
            self._teacher_combo.configure(border_color=BLUE)
        except Exception:
            pass

    def _teacher_combo_leave(self, _event=None):
        try:
            self._teacher_combo.configure(border_color=BORDER)
        except Exception:
            pass

    def _load_teacher_search_data(self):
        try:
            self._all_teachers = get_all_teachers() or []
        except Exception:
            self._all_teachers = []

        try:
            self._teacher_routines = search_routines_for_teacher(
                teacher_id="", teacher_name="", shift="") or []
        except Exception:
            self._teacher_routines = []

        self._teacher_options = []
        self._teacher_option_map = {}

        if self._all_teachers:
            for teacher in self._all_teachers:
                label = self._teacher_label(teacher)
                self._teacher_options.append(label)
                self._teacher_option_map[label] = teacher
        else:
            seen = set()
            for row in self._teacher_routines:
                name = _clean(row.get("teacher_name") or "")
                tid = str(row.get("teacher_uid") or row.get(
                    "teacher_db_id") or "").strip()
                if not name and not tid:
                    continue
                label = f"{name or 'Unnamed Teacher'}  |  ID: {tid or 'N/A'}"
                if label in seen:
                    continue
                seen.add(label)
                self._teacher_options.append(label)
                self._teacher_option_map[label] = {
                    "id": row.get("teacher_db_id"),
                    "teacher_id": row.get("teacher_uid"),
                    "name": name,
                }

    def _teacher_label(self, teacher):
        name = _clean(teacher.get("name") or "Unnamed Teacher")
        tid = str(teacher.get("teacher_id")
                  or teacher.get("id") or "N/A").strip()
        return f"{name}  |  ID: {tid}"

    def _teacher_search_blob(self, teacher):
        return " ".join([
            str(teacher.get("name") or ""),
            str(teacher.get("teacher_id") or ""),
            str(teacher.get("id") or ""),
            self._teacher_label(teacher),
        ]).lower()

    def _routine_teacher_blob(self, routine):
        return " ".join([
            str(routine.get("teacher_name") or ""),
            str(routine.get("teacher_uid") or ""),
            str(routine.get("teacher_db_id") or ""),
        ]).lower()

    def _on_teacher_combo_key(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self._queue_teacher_dropdown_filter(open_menu=True)

    def _on_teacher_combo_change(self, *_):
        if not self._teacher_combo_ready or self._teacher_combo_updating:
            return
        self._queue_teacher_dropdown_filter(open_menu=False)

    def _queue_teacher_dropdown_filter(self, open_menu=False):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.after(
            80, lambda: self._apply_teacher_dropdown_filter(open_menu=open_menu))

    def _apply_teacher_dropdown_filter(self, open_menu=False):
        query = self._teacher_search_var.get().strip()
        q = query.lower()

        if not q:
            filtered = self._teacher_options
        else:
            filtered = [
                label for label in self._teacher_options
                if q in label.lower()
                or q in self._teacher_search_blob(self._teacher_option_map[label])
            ]

        self._teacher_combo.configure(
            values=filtered or ["No matching teacher"])

        if query in self._teacher_option_map:
            self._render_teacher_for_selection(query)
        elif q:
            rows = [
                r for r in self._teacher_routines
                if q in self._routine_teacher_blob(r)
            ]
            self._render_results(
                rows, title=f"Teacher - {query}", mode="teacher")
        else:
            self._clear_results()

        if open_menu and filtered:
            try:
                self._teacher_combo._open_dropdown_menu()
            except Exception:
                pass

    def _on_teacher_combo_select(self, value):
        if value in self._teacher_option_map:
            self._render_teacher_for_selection(value)

    def _render_teacher_for_selection(self, label):
        teacher = self._teacher_option_map.get(label)
        if not teacher:
            return

        db_id = str(teacher.get("id") or "").strip()
        teacher_uid = str(teacher.get("teacher_id") or "").strip()
        rows = [
            r for r in self._teacher_routines
            if (db_id and str(r.get("teacher_db_id") or "").strip() == db_id)
            or (teacher_uid and str(r.get("teacher_uid") or "").strip() == teacher_uid)
        ]
        self._render_results(rows, title=f"👨‍🏫  {label}", mode="teacher")

    def _clear_teacher_dropdown(self):
        self._teacher_combo_updating = True
        try:
            self._teacher_search_var.set("")
            self._teacher_combo.configure(
                values=self._teacher_options or ["No teachers found"])
        finally:
            self._teacher_combo_updating = False
        self._clear_results()

    def _on_teacher_key(self, event=None):
        self._on_teacher_combo_key(event)

    def _live_teacher_search(self):
        self._apply_teacher_dropdown_filter(open_menu=False)

    def _search_teacher_manual(self):
        self._apply_teacher_dropdown_filter(open_menu=False)

    # ── Result area ───────────────────────────────────────────
    def _build_result_area(self):
        self._result_frame = ctk.CTkFrame(
            self._scroll, fg_color="transparent")
        self._result_frame.pack(fill="x", pady=(0, 24))

    def _clear_results(self):
        for w in self._result_frame.winfo_children():
            w.destroy()

    # ── Student search ────────────────────────────────────────
    def _search_student(self):
        dept = self._s_dept_var.get()
        sem = self._s_sem_var.get()
        shift = self._s_shift_var.get()
        try:
            rows = search_routines_for_student(dept, sem, shift)
        except Exception as e:
            self._show_msg(f"❌ Error: {e}", "red")
            return
        self._render_results(
            rows,
            title=f"🎓  {dept}  |  {sem} Sem  |  {shift.title()} Shift",
            mode="student")

    # ── Teacher search ────────────────────────────────────────
    def _search_teacher_direct(self, tid, tname):
        try:
            rows = search_routines_for_teacher(
                teacher_id=tid, teacher_name=tname, shift="")
        except Exception as e:
            self._show_msg(f"❌ Error: {e}", "red")
            return
        label = tid if tid else tname
        self._render_results(rows, title=f"👨‍🏫  {label}", mode="teacher")

    # ── Render results ────────────────────────────────────────
    def _show_msg(self, msg, color="gray"):
        self._clear_results()
        cm = {"gray": TEXT_SEC, "orange": AMBER, "red": RED, "green": GREEN}
        ctk.CTkLabel(self._result_frame, text=msg, font=_font(12),
                     text_color=cm.get(color, TEXT_SEC)
                     ).pack(anchor="w", pady=8)

    def _render_results(self, rows, title="", mode="student"):
        self._clear_results()

        ctk.CTkLabel(self._result_frame, text=title,
                     font=_font(13, bold=True),
                     text_color=BLUE).pack(anchor="w", pady=(0, 8))

        if not rows:
            ctk.CTkLabel(self._result_frame, text="◌  No routines found.",
                         font=_font(12), text_color=C("text_dim")
                         ).pack(anchor="w")
            return

        headers = S_HDR if mode == "student" else T_HDR
        col_widths = S_COL if mode == "student" else T_COL

        def _draw_block(block_rows):
            _draw_table_header(self._result_frame, headers, col_widths)
            for idx, r in enumerate(block_rows, start=1):
                rid = r["id"]
                if mode == "student":
                    row_w = _StudentRow(self._result_frame, idx, r)
                else:
                    row_w = _TeacherRow(
                        self._result_frame, idx, r,
                        edit_cb=lambda _r=rid: self._open_edit(_r),
                        delete_cb=lambda _r=rid, _s=r["subject"]:
                            self._delete_result(_r, _s),
                    )
                row_w.pack(fill="x", pady=2)

        # Group by day
        grouped = {}
        for r in rows:
            grouped.setdefault(r["day"], []).append(r)

        for day in DAYS_ORDER:
            if day not in grouped:
                continue
            dc = DAY_COLOR.get(day, TEXT_SEC)
            dh = ctk.CTkFrame(self._result_frame, fg_color=SURFACE,
                              corner_radius=8, border_width=1,
                              border_color=BORDER, height=45)
            dh.pack(fill="x", pady=(6, 1))
            dh.pack_propagate(False)

            day_dot = ctk.CTkFrame(dh, fg_color=dc, width=4, corner_radius=2)
            day_dot.pack(side="left", fill="y")

            ctk.CTkLabel(dh,
                         text=f"  {day}",
                         font=_font(12, bold=True),
                         text_color=(dc, dc)).pack(side="left", padx=(8, 4), pady=4)
            ctk.CTkLabel(dh,
                         text=f"— {len(grouped[day])} class(es)",
                         font=_font(10), text_color=TEXT_MUT
                         ).pack(side="left", pady=4)

            _draw_block(grouped[day])

        ctk.CTkLabel(self._result_frame,
                     text=f"Total  {len(rows)}  class(es) found.",
                     font=_font(11), text_color=C("text_dim")
                     ).pack(anchor="w", pady=(8, 0))

    # ── Edit / Delete ─────────────────────────────────────────
    def _open_edit(self, routine_id):
        _EditRoutineModal(self, routine_id=routine_id,
                          on_save=self._refresh)

    def _delete_result(self, routine_id, subject):
        subject_clean = _clean(subject)
        if messagebox.askyesno("Delete?",
                               f"Delete routine for '{subject_clean}'?"):
            try:
                delete_routine(routine_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Refresh ───────────────────────────────────────────────
    def _refresh(self):
        self._all_teachers = []
        self._teacher_options = []
        self._teacher_option_map = {}
        self._teacher_routines = []
        self._teacher_combo_ready = False
        self._teacher_combo_updating = False
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
