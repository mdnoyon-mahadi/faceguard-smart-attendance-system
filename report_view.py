# ============================================================
# report_view.py — Admin Report Page  (Redesigned v4)
# ============================================================
# Changes:
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# ============================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import os

from models.report_model import (
    get_departments, get_semesters_by_dept,
    get_subjects_by_dept_sem, get_shifts_by_dept_sem,
    get_filtered_reports, get_report_detail,
    get_teacher_attendance_detail, delete_report,
    get_absent_students,
)
from services.report_service import (
    export_session_pdf, export_filtered_pdf,
)


# ── Color constants ───────────────────────────────────────────
BG = ("#0d1117", "#0d1117")
SURFACE = ("#161b22", "#161b22")
SURFACE2 = ("#1c2128", "#1c2128")
BORDER = ("#21262d", "#21262d")
TEXT_PRI = ("#e6edf3", "#e6edf3")
TEXT_SEC = ("#8b949e", "#8b949e")
TEXT_MUT = ("#484f58", "#484f58")
BLUE = ("#1f6feb", "#1f6feb")
BLUE_HV = ("#0d2a4a", "#0d2a4a")
BLUE_TXT = ("#58a6ff", "#58a6ff")
GREEN = ("#238636", "#238636")
GREEN_HV = ("#2ea043", "#2ea043")
GREEN_TXT = ("#3fb950", "#3fb950")
GREEN_BG = ("#0d2a0f", "#0d2a0f")
GREEN_BD = ("#238636", "#238636")
RED = ("#f85149", "#f85149")
RED_BG = ("#2d1117", "#2d1117")
RED_BD = ("#6e2020", "#6e2020")
AMBER = ("#e3b341", "#e3b341")
AMBER_BG = ("#2d2006", "#2d2006")
AMBER_BD = ("#4d3a07", "#4d3a07")
PDF_BTN = ("#6e40c9", "#6e40c9")
PDF_HV = ("#5a32a3", "#5a32a3")
PURPLE = ("#6e40c9", "#6e40c9")
PURPLE_BG = ("#1a0d2e", "#1a0d2e")
PURPLE_BD = ("#3d1f6e", "#3d1f6e")

PENDING_CLR = ("#e3b341", "#e3b341")
PENDING_BG = ("#2d2006", "#2d2006")
PENDING_BD = ("#4d3a07", "#4d3a07")
COMPLETE_CLR = ("#3fb950", "#3fb950")
COMPLETE_BG = ("#0d2a0f", "#0d2a0f")
COMPLETE_BD = ("#238636", "#238636")
NULL_CLR = ("#484f58", "#484f58")
NULL_BG = ("#161b22", "#161b22")
NULL_BD = ("#21262d", "#21262d")

ABSENT_CLR = ("#f85149", "#f85149")
ABSENT_BG = ("#2d1117", "#2d1117")
ABSENT_BD = ("#6e2020", "#6e2020")

ROW_HOVER = ("#1c2128", "#1c2128")
ROW_HOVER_PENDING = ("#322500", "#322500")
ROW_HOVER_COMPLETE = ("#0f2b0f", "#0f2b0f")


class ReportViewPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._current_reports = []
        self._build_ui()

    # ── Top-level UI ──────────────────────────────────────────

    def _build_ui(self):
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            title_bar, text="Attendance Reports",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_PRI,
        ).pack(side="left")

        ctk.CTkButton(
            title_bar, text="↻  Refresh", width=90, height=32,
            fg_color="transparent", border_width=1,
            border_color=BORDER, text_color=TEXT_SEC,
            hover_color=SURFACE, font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._refresh,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=28, pady=12)

        self._build_filter_form()

        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.pack(
            fill="both", expand=True, padx=28, pady=(0, 16))

        self._status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=(GREEN_TXT[0], GREEN_TXT[0]))
        self._status_lbl.pack(anchor="e", padx=28, pady=(0, 8))

    # ── Filter Form ───────────────────────────────────────────

    def _build_filter_form(self):
        form = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=10)
        form.pack(fill="x", padx=28, pady=(0, 16))

        ctk.CTkLabel(
            form, text="Filter Reports",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_SEC,
        ).grid(row=0, column=0, columnspan=5, sticky="w",
               padx=16, pady=(12, 8))

        for col, lbl in enumerate(["Department", "Semester", "Subject", "Shift"]):
            ctk.CTkLabel(form, text=lbl,
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=TEXT_MUT).grid(
                row=1, column=col,
                padx=(16 if col == 0 else 12, 4),
                pady=(0, 4), sticky="w")

        try:
            depts = get_departments()
        except Exception:
            depts = []

        cb_kw = dict(fg_color=BG, border_color=BORDER,
                     button_color=BORDER, button_hover_color=SURFACE,
                     text_color=TEXT_PRI, dropdown_fg_color=BG,
                     font=ctk.CTkFont(family="Segoe UI", size=12), state="readonly")

        self._dept_cb = ctk.CTkComboBox(
            form, values=["-- Select --"] + depts,
            width=180, height=32,
            command=self._on_dept_change, **cb_kw)
        self._dept_cb.set("-- Select --")
        self._dept_cb.grid(row=2, column=0, padx=(16, 4),
                           pady=(0, 14), sticky="w")

        self._sem_cb = ctk.CTkComboBox(
            form, values=["-- Select --"], width=140, height=32,
            command=self._on_sem_change,
            **{**cb_kw, "state": "disabled"})
        self._sem_cb.set("-- Select --")
        self._sem_cb.grid(row=2, column=1, padx=(12, 4),
                          pady=(0, 14), sticky="w")

        self._subj_cb = ctk.CTkComboBox(
            form, values=["-- Select --"], width=200, height=32,
            command=self._on_subj_change,
            **{**cb_kw, "state": "disabled"})
        self._subj_cb.set("-- Select --")
        self._subj_cb.grid(row=2, column=2, padx=(12, 4),
                           pady=(0, 14), sticky="w")

        self._shift_cb = ctk.CTkComboBox(
            form, values=["-- Select --"], width=130, height=32,
            **{**cb_kw, "state": "disabled"})
        self._shift_cb.set("-- Select --")
        self._shift_cb.grid(row=2, column=3, padx=(12, 4),
                            pady=(0, 14), sticky="w")

        self._submit_btn = ctk.CTkButton(
            form, text="Show Reports", width=120, height=34,
            fg_color=BLUE, hover_color=GREEN_HV,
            text_color=TEXT_PRI,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=8, command=self._on_submit)
        self._submit_btn.grid(row=2, column=4, padx=(16, 16),
                              pady=(0, 14), sticky="w")

    # ── Cascading dropdown callbacks ──────────────────────────

    def _on_dept_change(self, val):
        if val == "-- Select --":
            self._reset_from("semester")
            return
        try:
            sems = get_semesters_by_dept(val)
        except Exception:
            sems = []
        self._sem_cb.configure(
            values=["-- Select --"] + sems,
            state="readonly" if sems else "disabled")
        self._sem_cb.set("-- Select --")
        self._reset_from("subject")

    def _on_sem_change(self, val):
        if val == "-- Select --":
            self._reset_from("subject")
            return
        dept = self._dept_cb.get()
        try:
            subjs = get_subjects_by_dept_sem(dept, val)
        except Exception:
            subjs = []
        self._subj_cb.configure(
            values=["-- Select --"] + subjs,
            state="readonly" if subjs else "disabled")
        self._subj_cb.set("-- Select --")
        self._reset_from("shift")

    def _on_subj_change(self, val):
        if val == "-- Select --":
            self._reset_from("shift")
            return
        dept = self._dept_cb.get()
        sem = self._sem_cb.get()
        try:
            shifts = get_shifts_by_dept_sem(dept, sem)
        except Exception:
            shifts = ["morning"]
        if not shifts:
            shifts = ["morning"]
        self._shift_cb.configure(
            values=["-- Select --"] + shifts,
            state="readonly")
        self._shift_cb.set(
            shifts[0] if len(shifts) == 1 else "-- Select --")

    def _reset_from(self, level):
        if level == "semester":
            self._sem_cb.configure(
                values=["-- Select --"], state="disabled")
            self._sem_cb.set("-- Select --")
            level = "subject"
        if level == "subject":
            self._subj_cb.configure(
                values=["-- Select --"], state="disabled")
            self._subj_cb.set("-- Select --")
            level = "shift"
        if level == "shift":
            self._shift_cb.configure(
                values=["-- Select --"], state="disabled")
            self._shift_cb.set("-- Select --")

    # ── Submit ────────────────────────────────────────────────

    def _on_submit(self):
        dept = self._dept_cb.get()
        sem = self._sem_cb.get()
        subj = self._subj_cb.get()
        shift = self._shift_cb.get()

        if "-- Select --" in (dept, sem, subj, shift):
            messagebox.showwarning(
                "Filter Incomplete",
                "Please select all 4 fields:\n"
                "Department → Semester → Subject → Shift")
            return

        for w in self._results_frame.winfo_children():
            w.destroy()
        self._status_lbl.configure(text="")

        try:
            reports = get_filtered_reports(dept, sem, subj, shift)
        except Exception as e:
            reports = []
            self._status_lbl.configure(
                text=f"❌ DB Error: {e}",
                text_color=(RED[0], RED[0]))

        self._current_reports = reports or []

        if not reports:
            ctk.CTkLabel(
                self._results_frame,
                text="No attendance records found for this filter.",
                font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUT,
            ).pack(pady=40)
            return

        self._build_results(reports, dept, sem, subj, shift)

    # ── Results Area ──────────────────────────────────────────

    def _build_results(self, reports, dept, sem, subj, shift):
        pending_reports = [r for r in reports
                           if r.get("report_status") == "pending"]
        complete_reports = [r for r in reports
                            if r.get("report_status") == "complete"]
        null_reports = [r for r in reports
                        if r.get("report_status") is None]

        # ── Action bar ────────────────────────────────────────
        action_bar = ctk.CTkFrame(
            self._results_frame, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 10))

        # Summary badges
        badge_row = ctk.CTkFrame(action_bar, fg_color="transparent")
        badge_row.pack(side="left")

        ctk.CTkLabel(
            badge_row,
            text=f"{len(reports)} session  ·  "
                 f"{subj}  ·  {dept} / {sem} / {shift}",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_SEC,
        ).pack(side="left", padx=(0, 12))

        if pending_reports:
            self._mini_badge(badge_row,
                             f"⏳ {len(pending_reports)} Pending",
                             PENDING_CLR[0], PENDING_BG[0], PENDING_BD[0])
        if complete_reports:
            self._mini_badge(badge_row,
                             f"✅ {len(complete_reports)} Complete",
                             COMPLETE_CLR[0], COMPLETE_BG[0], COMPLETE_BD[0])
        
        # Calculate overall absent count for the badge
        total_absent = 0
        for r in reports:
            try:
                abs_list = get_absent_students(r["session_id"])
                total_absent += len(abs_list)
            except:
                pass
        
        if total_absent > 0:
            self._mini_badge(badge_row,
                             f"✖ {total_absent} Absent",
                             ABSENT_CLR[0], ABSENT_BG[0], ABSENT_BD[0])

        if null_reports:
            self._mini_badge(badge_row,
                             f"— {len(null_reports)} No Status",
                             NULL_CLR[0], NULL_BG[0], NULL_BD[0])

# Comment translated to English.
        ctk.CTkButton(
            action_bar,
            text="🗑  Delete All",
            width=110, height=30,
            fg_color="transparent",
            border_width=1, border_color=RED,
            text_color=RED,
            hover_color=RED_BG,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8,
            command=lambda: self._delete_all(reports),
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            action_bar, text="📄 Download All PDF",
            width=160, height=30,
            fg_color=PDF_BTN, hover_color=PDF_HV,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8,
            command=lambda: self._export_filtered_pdf(reports),
        ).pack(side="right", padx=(4, 0))

        # ── Scrollable list ───────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self._results_frame, fg_color="transparent",
            scrollbar_fg_color=BG)
        scroll.pack(fill="both", expand=True)

        # ── SECTION A — PENDING ───────────────────────────────
        if pending_reports:
            self._section_header(
                scroll,
                "⏳  Pending Reports  —  Entry scanned, Exit scan remaining",
                len(pending_reports),
                PENDING_CLR[0], PENDING_BG[0], PENDING_BD[0],
                compact=True)
            self._table_header(scroll, mode="pending", compact=True)
            for idx, rep in enumerate(pending_reports):
                self._build_row(
                    scroll, rep, mode="pending", idx=idx, compact=True)
            ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(
                fill="x", pady=(6, 12))

        # ── SECTION B — COMPLETE ──────────────────────────────
        if complete_reports:
            self._section_header(
                scroll,
                "✅  Complete Reports  —  Both Entry + Exit scans completed",
                len(complete_reports),
                COMPLETE_CLR[0], COMPLETE_BG[0], COMPLETE_BD[0],
                compact=True)
            self._table_header(scroll, mode="complete", compact=True)
            for idx, rep in enumerate(complete_reports):
                self._build_row(
                    scroll, rep, mode="complete", idx=idx, compact=True)
            if null_reports:
                ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(
                    fill="x", pady=(6, 12))

        # ── SECTION C — NULL STATUS ───────────────────────────
        if null_reports:
            self._section_header(
                scroll,
                "—  Legacy Reports  —  Sessions without status tracking",
                len(null_reports),
                NULL_CLR[0], NULL_BG[0], NULL_BD[0],
                compact=True)
            self._table_header(scroll, mode="null", compact=True)
            for idx, rep in enumerate(null_reports):
                self._build_row(
                    scroll, rep, mode="null", idx=idx, compact=True)

        if not (pending_reports or complete_reports or null_reports):
            ctk.CTkLabel(
                scroll,
                text="No sessions found.",
                font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_MUT,
            ).pack(pady=20)

    # ── Section Header helper ─────────────────────────────────

    def _section_header(self, parent, text, count,
                        clr, bg, bd, compact=False):
        f = ctk.CTkFrame(parent, fg_color=(bg, bg),
                         border_color=(bd, bd),
                         border_width=1, corner_radius=8)
        f.pack(fill="x", pady=(0, 2 if compact else 4))
        py = 5 if compact else 8
        ctk.CTkLabel(
            f, text=text,
            font=ctk.CTkFont(
                family="Segoe UI", size=11 if compact else 12, weight="bold"),
            text_color=(clr, clr),
        ).pack(side="left", anchor="w", padx=12 if compact else 14, pady=py)
        ctk.CTkLabel(
            f, text=f"{count} session(s)",
            font=ctk.CTkFont(family="Segoe UI", size=10 if compact else 11),
            text_color=(clr, clr),
        ).pack(side="right", anchor="e", padx=12 if compact else 14, pady=py)

    # ── Mini badge helper ─────────────────────────────────────

    def _mini_badge(self, parent, text, text_color, bg, border):
        f = ctk.CTkFrame(parent,
                         fg_color=(bg, bg),
                         border_color=(border, border),
                         border_width=1, corner_radius=5)
        f.pack(side="left", padx=3)
        ctk.CTkLabel(
            f, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=(text_color, text_color),
        ).pack(padx=8, pady=3)

    # ── Table Header ──────────────────────────────────────────

    def _table_header(self, parent, mode="complete", compact=False):
        if mode == "pending":
            bg = ("#241a00", "#241a00")
            accent = PENDING_CLR[0]
        elif mode == "complete":
            bg = ("#0a1f0a", "#0a1f0a")
            accent = COMPLETE_CLR[0]
        else:
            bg = SURFACE
            accent = TEXT_MUT[0]

        hdr = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
        hdr.pack(fill="x", pady=(0, 2 if compact else 3))

# Comment translated to English.
        cols = [
            ("Date",    95),
            ("Teacher", 145),
            ("Attended", 110),
            ("Pending", 85),
            ("Absent",  85),
            ("Total",   65),
            ("Report",  90),
            ("",        58),   # Detail
            ("",        74),   # PDF
            ("",        58),   # Delete
        ]
        hp = 2 if compact else 4
        hf = 10 if compact else 11
        for i, (h, w) in enumerate(cols):
            tc = accent if h in ("Pending", "Report") else TEXT_MUT[0]
            ctk.CTkLabel(
                hdr, text=h, width=w,
                font=ctk.CTkFont(family="Segoe UI", size=hf, weight="bold"),
                text_color=(tc, tc), anchor="w",
            ).grid(row=0, column=i,
                   padx=(12 if compact and i == 0 else (14 if i == 0 else 6)),
                   pady=hp, sticky="w")

    # ── Table Row ─────────────────────────────────────────────

    def _build_row(self, parent, rep, mode="complete", idx=0, compact=False):
        pending = rep.get("pending_count") or 0
        attended = rep.get("attended") or 0
        total = rep.get("total_scanned") or 0
        pct = round(attended / total * 100) if total > 0 else 0
        pct_color = (GREEN_TXT[0], GREEN_TXT[0]) if pct >= 75 else \
                    (RED[0], RED[0]) if pct < 60 else \
                    (AMBER[0], AMBER[0])

        if mode == "pending":
            bg = PENDING_BG if idx % 2 == 0 else ("#1c1400", "#1c1400")
        elif mode == "complete":
            bg = COMPLETE_BG if idx % 2 == 0 else ("#081508", "#081508")
        else:
            bg = BG if idx % 2 == 0 else SURFACE

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8, border_width=0)
        row.pack(fill="x", pady=0 if compact else 1, padx=2)

        # Hover effects
        def _on_enter(e, f=row, m=mode):
            h_bg = ROW_HOVER_PENDING if m=="pending" else \
                   ROW_HOVER_COMPLETE if m=="complete" else ROW_HOVER
            f.configure(fg_color=h_bg, border_color=BORDER, border_width=1)
        def _on_leave(e, f=row, b=bg):
            f.configure(fg_color=b, border_width=0)
        
        row.bind("<Enter>", _on_enter)
        row.bind("<Leave>", _on_leave)

        # Ensure labels also trigger hover on parent
        for child in row.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.bind("<Enter>", _on_enter)
                child.bind("<Leave>", _on_leave)

        # NEW: Real Absent calculation (using backend helper)
        try:
            abs_list = get_absent_students(rep["session_id"])
            absent_ct = len(abs_list)
        except:
            # Fallback to user's formula if helper fails
            absent_ct = total - attended
            
        absent_color = ABSENT_CLR if absent_ct > 0 else TEXT_MUT

        cells = [
            (str(rep["session_date"]),          95,  TEXT_SEC),
            (rep["teacher_name"] or "—",        145, TEXT_SEC),
            (f"{attended}  ({pct}%)",           110, pct_color),
            (str(pending) if pending else "—",  85,
             (AMBER[0], AMBER[0]) if pending else TEXT_MUT),
            (str(absent_ct) if absent_ct else "—", 85, absent_color),
            (str(total + absent_ct),            65,  TEXT_MUT),
        ]

        fz = 11 if compact else 12
        cp = 2 if compact else 4
        px0 = 12 if compact else 14
        for i, (val, w, color) in enumerate(cells):
            ctk.CTkLabel(
                row, text=val, width=w,
                font=ctk.CTkFont(family="Segoe UI", size=fz),
                text_color=color, anchor="w",
            ).grid(row=0, column=i,
                   padx=(px0 if i == 0 else 6), pady=cp, sticky="w")

        # ── Report Status Badge (col 5) ───────────────────────
        rs = rep.get("report_status")
        if rs == "pending":
            badge_text = "⏳ Pending"
            badge_tc = (PENDING_CLR[0],  PENDING_CLR[0])
            badge_bg = (PENDING_BG[0],   PENDING_BG[0])
            badge_bd = (PENDING_BD[0],   PENDING_BD[0])
            gen_time = rep.get("pending_report_generated_at")
            if gen_time:
                badge_text = f"⏳ Pending\n{str(gen_time)[11:16]}"
        elif rs == "complete":
            badge_text = "✅ Complete"
            badge_tc = (COMPLETE_CLR[0], COMPLETE_CLR[0])
            badge_bg = (COMPLETE_BG[0],  COMPLETE_BG[0])
            badge_bd = (COMPLETE_BD[0],  COMPLETE_BD[0])
            gen_time = rep.get("complete_report_generated_at")
            if gen_time:
                badge_text = f"✅ Complete\n{str(gen_time)[11:16]}"
        else:
            badge_text = "— N/A"
            badge_tc = (NULL_CLR[0], NULL_CLR[0])
            badge_bg = (NULL_BG[0],  NULL_BG[0])
            badge_bd = (NULL_BD[0],  NULL_BD[0])

        bw = 78 if compact else 82
        _badge_kw = dict(
            fg_color=badge_bg,
            border_color=badge_bd, border_width=1,
            corner_radius=5, width=bw)
        if compact:
            _badge_kw["height"] = 36
        badge_frame = ctk.CTkFrame(row, **_badge_kw)
        badge_frame.grid(
            row=0, column=6, padx=5 if compact else 6,
            pady=2 if compact else 3, sticky="w")
        badge_frame.grid_propagate(False)
        ctk.CTkLabel(
            badge_frame, text=badge_text,
            font=ctk.CTkFont(
                family="Segoe UI", size=8 if compact else 9, weight="bold"),
            text_color=badge_tc, anchor="center", justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Detail button (col 7) ─────────────────────────────
        sid = rep["session_id"]
        subject = rep["subject"]
        date = rep["session_date"]
        teacher = rep.get("teacher_name") or ""

        bh = 20 if compact else 22
        bp = 2 if compact else 3
        bf = 10 if compact else 11
        ctk.CTkButton(
            row, text="Detail", width=56 if compact else 58, height=bh,
            fg_color="transparent", border_width=1,
            border_color=BLUE, text_color=BLUE_TXT,
            hover_color=BLUE_HV,
            font=ctk.CTkFont(family="Segoe UI", size=bf), corner_radius=6,
            command=lambda s=sid, sub=subject: self._show_detail(s, sub),
        ).grid(row=0, column=7, padx=5 if compact else 6, pady=bp)

        # ── PDF button (col 8) ────────────────────────────────
        ctk.CTkButton(
            row, text="📄 PDF", width=72 if compact else 74, height=bh,
            fg_color=PDF_BTN, hover_color=PDF_HV,
            font=ctk.CTkFont(family="Segoe UI", size=bf), corner_radius=6,
            command=lambda s=sid, sub=subject, d=date, tc=teacher:
                self._export_one_pdf(s, sub, d, tc),
        ).grid(row=0, column=8, padx=3 if compact else 4, pady=bp)

        # ── Delete button (col 9) ─────────────────────────────
        ctk.CTkButton(
            row, text="🗑", width=34 if compact else 36, height=bh,
            fg_color="transparent",
            border_width=1, border_color=RED,
            text_color=RED,
            hover_color=RED_BG,
            font=ctk.CTkFont(family="Segoe UI", size=11 if compact else 12),
            corner_radius=6,
            command=lambda s=sid, r=row, d=date, sub=subject:
                self._delete_one(s, r, d, sub),
        ).grid(row=0, column=9, padx=(0, 6 if compact else 8), pady=bp)

        # Propagate click to Detail modal if row is clicked (optional enhancement)
        for child in row.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.bind("<Button-1>", lambda e, s=sid, sub=subject: self._show_detail(s, sub))
                child.configure(cursor="hand2")

    # ── Detail Modal ──────────────────────────────────────────

    def _show_detail(self, session_id, subject):
        def _row_absent_ui(r):
            """UI-only: absent when no scan in and no scan out."""
            return r.get("scan_in_time") is None and r.get("scan_out_time") is None

        try:
            rows = get_report_detail(session_id)
        except Exception:
            rows = []
        absent_rows_ui = [r for r in rows if _row_absent_ui(r)]
        try:
            teacher_rec = get_teacher_attendance_detail(session_id)
        except Exception:
            teacher_rec = None

        win = ctk.CTkToplevel(self)
        win.title(f"Detail — {subject}")
        win.geometry("860x620")
        win.configure(fg_color=BG[0])
        # Removed win.grab_set() to allow the window to be minimized and non-blocking
        
        # Force window to the front
        win.attributes("-topmost", True)
        win.after(50, lambda: win.attributes("-topmost", False))
        win.focus_force()

        hdr_bar = ctk.CTkFrame(win, fg_color="transparent")
        hdr_bar.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            hdr_bar, text=f"📋  {subject}  —  Attendance Detail",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRI,
        ).pack(side="left")

        if rows:
            complete_ct = sum(
                1 for r in rows
                if r["status"] == "complete" and not _row_absent_ui(r))
            pending_ct = sum(
                1 for r in rows
                if r["status"] == "pending" and not _row_absent_ui(r))
            absent_ct = len(absent_rows_ui)

            bf = ctk.CTkFrame(hdr_bar, fg_color="transparent")
            bf.pack(side="right")
            ctk.CTkLabel(
                bf, text=f"✓ {complete_ct} complete",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=(GREEN_TXT[0], GREEN_TXT[0]),
            ).pack(side="left", padx=6)
            if pending_ct:
                ctk.CTkLabel(
                    bf, text=f"⚠ {pending_ct} pending",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color=(AMBER[0], AMBER[0]),
                ).pack(side="left", padx=6)
            ctk.CTkLabel(
                bf, text=f"✖ {absent_ct} absent",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=(RED[0], RED[0]) if absent_ct else (TEXT_MUT[0], TEXT_MUT[0]),
            ).pack(side="left", padx=6)

        ctk.CTkFrame(win, height=1, fg_color=BORDER).pack(
            fill="x", padx=20, pady=10)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        col_hdrs = ["Roll", "Name", "Department",
                    "Sem", "Scan In", "Scan Out", "Status"]
        col_widths = [100, 145, 130, 55, 120, 120, 85]

        # Teacher section
        teach_hdr = ctk.CTkFrame(
            scroll,
            fg_color=(PURPLE_BG[0], PURPLE_BG[0]),
            border_color=(PURPLE_BD[0], PURPLE_BD[0]),
            border_width=1, corner_radius=8)
        teach_hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            teach_hdr, text="👨‍🏫  Teacher Attendance",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=(PURPLE[0], PURPLE[0]),
        ).pack(anchor="w", padx=14, pady=8)

        t_hdr = ctk.CTkFrame(
            scroll, fg_color=(PURPLE_BG[0], PURPLE_BG[0]),
            corner_radius=6)
        t_hdr.pack(fill="x", pady=(0, 3))
        t_cols = [("Name", 200), ("Scan In", 130),
                  ("Scan Out", 130), ("Status", 100)]
        for i, (h, w) in enumerate(t_cols):
            ctk.CTkLabel(
                t_hdr, text=h, width=w,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=(PURPLE[0], PURPLE[0]), anchor="w",
            ).grid(row=0, column=i,
                   padx=(12 if i == 0 else 8), pady=6, sticky="w")

        t_row = ctk.CTkFrame(
            scroll, fg_color=(PURPLE_BG[0], PURPLE_BG[0]),
            corner_radius=4)
        t_row.pack(fill="x", pady=(0, 2))

        if teacher_rec:
            sin = str(teacher_rec["scan_in_time"])[11:16] \
                if teacher_rec["scan_in_time"] else "—"
            sout = str(teacher_rec["scan_out_time"])[11:16] \
                if teacher_rec["scan_out_time"] else "—"
            status = teacher_rec["status"].upper()
            sc = (GREEN_TXT[0], GREEN_TXT[0]) \
                if status == "COMPLETE" else (AMBER[0], AMBER[0])
            t_cells = [
                (teacher_rec["name"], 200, TEXT_PRI),
                (sin,                 130, TEXT_SEC),
                (sout,                130, TEXT_SEC),
                (status,              100, sc),
            ]
        else:
            t_cells = [
                ("— Not Scanned —", 200, (TEXT_MUT[0], TEXT_MUT[0])),
                ("—",               130, TEXT_MUT),
                ("—",               130, TEXT_MUT),
                ("—",               100, TEXT_MUT),
            ]

        for i, (val, w, color) in enumerate(t_cells):
            ctk.CTkLabel(
                t_row, text=val, width=w,
                font=ctk.CTkFont(family="Segoe UI", size=12,
                                 weight="bold" if i in (0, 3) else "normal"),
                text_color=color, anchor="w",
            ).grid(row=0, column=i,
                   padx=(12 if i == 0 else 8), pady=7, sticky="w")

        ctk.CTkFrame(scroll, height=1,
                     fg_color=(PURPLE_BD[0], PURPLE_BD[0])).pack(
            fill="x", pady=(4, 10))

        if not rows:
            ctk.CTkLabel(scroll,
                         text="No student records found.",
                         text_color=TEXT_MUT).pack(pady=20)
            return

        pending_rows = [
            r for r in rows
            if r["status"] == "pending" and not _row_absent_ui(r)]
        complete_rows = [
            r for r in rows
            if r["status"] == "complete" and not _row_absent_ui(r)]

        def _section_label(text, color):
            ctk.CTkLabel(
                scroll, text=text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=color,
            ).pack(anchor="w", pady=(8, 2))

        def _draw_table(row_list, bg_even):
            th = ctk.CTkFrame(scroll, fg_color=SURFACE, corner_radius=6)
            th.pack(fill="x", pady=(0, 3))
            for i, (h, w) in enumerate(zip(col_hdrs, col_widths)):
                ctk.CTkLabel(
                    th, text=h, width=w,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color=TEXT_MUT, anchor="w",
                ).grid(row=0, column=i,
                       padx=(10 if i == 0 else 5), pady=6, sticky="w")

            for idx, r in enumerate(row_list):
                rbg = bg_even if idx % 2 == 0 else SURFACE
                rf = ctk.CTkFrame(scroll, fg_color=rbg, corner_radius=6, border_width=0)
                rf.pack(fill="x", pady=2, padx=2)
                
                # Hover effect for detail table
                def _h_enter(e, f=rf, b=bg_even):
                    h_bg = ROW_HOVER if b==BG else ROW_HOVER_PENDING if b==AMBER_BG else ROW_HOVER_COMPLETE
                    f.configure(fg_color=h_bg, border_color=BORDER, border_width=1)
                def _h_leave(e, f=rf, b=rbg):
                    f.configure(fg_color=b, border_width=0)
                rf.bind("<Enter>", _h_enter)
                rf.bind("<Leave>", _h_leave)

                # Propagate hover from labels to row frame
                for child in rf.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.bind("<Enter>", _h_enter)
                        child.bind("<Leave>", _h_leave)

                sc = (GREEN_TXT[0], GREEN_TXT[0]) \
                    if r["status"] == "complete" else (AMBER[0], AMBER[0])
                sin = str(r["scan_in_time"])[11:16] \
                    if r["scan_in_time"] else "—"
                sout = str(r["scan_out_time"])[11:16] \
                    if r["scan_out_time"] else "—"
                cells = [
                    (r["roll"],             col_widths[0], TEXT_SEC),
                    (r["name"],             col_widths[1], TEXT_PRI),
                    (r["department"][:14],  col_widths[2], TEXT_SEC),
                    (r["semester"],         col_widths[3], TEXT_SEC),
                    (sin,                   col_widths[4], TEXT_SEC),
                    (sout,                  col_widths[5], TEXT_SEC),
                    (r["status"].upper(),   col_widths[6], sc),
                ]
                for i, (val, w, color) in enumerate(cells):
                    ctk.CTkLabel(
                        rf, text=val, width=w,
                        font=ctk.CTkFont(family="Segoe UI", size=11),
                        text_color=color, anchor="w",
                    ).grid(row=0, column=i,
                           padx=(10 if i == 0 else 5), pady=6, sticky="w")

        def _draw_absent_table(row_list, bg_even):
            """Same chrome as Complete/Pending; columns per spec (no scan times)."""
            abs_hdrs = ["Roll", "Name", "Department", "Semester", "Status"]
            abs_widths = [100, 145, 120, 72, 85]
            th = ctk.CTkFrame(scroll, fg_color=SURFACE, corner_radius=6)
            th.pack(fill="x", pady=(0, 3))
            for i, (h, w) in enumerate(zip(abs_hdrs, abs_widths)):
                ctk.CTkLabel(
                    th, text=h, width=w,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color=TEXT_MUT, anchor="w",
                ).grid(row=0, column=i,
                       padx=(10 if i == 0 else 5), pady=6, sticky="w")

            if not row_list:
                empty_f = ctk.CTkFrame(
                    scroll, fg_color=SURFACE, corner_radius=6, border_width=0)
                empty_f.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(
                    empty_f,
                    text="No absent students — everyone attended this session.",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=(GREEN_TXT[0], GREEN_TXT[0]),
                    anchor="w",
                ).pack(anchor="w", padx=12, pady=10)
                return

            for idx, r in enumerate(row_list):
                rbg = bg_even if idx % 2 == 0 else SURFACE
                rf = ctk.CTkFrame(
                    scroll, fg_color=rbg, corner_radius=6, border_width=0)
                rf.pack(fill="x", pady=2, padx=2)

                def _h_enter(e, f=rf, b=bg_even):
                    h_bg = (
                        ROW_HOVER if b == BG else
                        ROW_HOVER_PENDING if b == AMBER_BG else
                        ROW_HOVER_COMPLETE)
                    f.configure(fg_color=h_bg, border_color=BORDER, border_width=1)

                def _h_leave(e, f=rf, b=rbg):
                    f.configure(fg_color=b, border_width=0)

                rf.bind("<Enter>", _h_enter)
                rf.bind("<Leave>", _h_leave)
                for child in rf.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.bind("<Enter>", _h_enter)
                        child.bind("<Leave>", _h_leave)

                dept = str(r.get("department") or "—")
                if len(dept) > 14:
                    dept = dept[:14]
                cells = [
                    (r.get("roll") or "—", abs_widths[0], TEXT_SEC),
                    (r.get("name") or "—", abs_widths[1], TEXT_PRI),
                    (dept, abs_widths[2], TEXT_SEC),
                    (str(r.get("semester") or "—"), abs_widths[3], TEXT_SEC),
                    ("ABSENT", abs_widths[4], RED),
                ]
                for i, (val, w, color) in enumerate(cells):
                    ctk.CTkLabel(
                        rf, text=val, width=w,
                        font=ctk.CTkFont(
                            family="Segoe UI", size=11,
                            weight="bold" if i == 4 else "normal"),
                        text_color=color, anchor="w",
                    ).grid(row=0, column=i,
                           padx=(10 if i == 0 else 5), pady=6, sticky="w")

        if pending_rows:
            _section_label(
                f"⚠  Pending ({len(pending_rows)} students) — Scan-out incomplete",
                (AMBER[0], AMBER[0]))
            _draw_table(pending_rows, bg_even=AMBER_BG)
            ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(
                fill="x", pady=8)

        if complete_rows:
            _section_label(
                f"✓  Complete ({len(complete_rows)} students)",
                (GREEN_TXT[0], GREEN_TXT[0]))
            _draw_table(complete_rows, bg_even=BG)

        # Absent list — always shown (empty state if full attendance)
        ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(
            fill="x", pady=8)
        _na = len(absent_rows_ui)
        _section_label(
            f"✖  Absent Students ({_na}) — No entry/exit scan",
            (RED[0], RED[0]) if _na else (TEXT_MUT[0], TEXT_MUT[0]))
        _draw_absent_table(absent_rows_ui, bg_even=BG)

    # ── Delete Actions ────────────────────────────────────────

    def _delete_one(self, session_id, row_frame, date, subject):
        """ session delete ."""
        if not messagebox.askyesno(
                "Delete Report?",
                f"Are you sure you want to delete the report for '{subject}' on {date}?\n"
                f"All attendance records for this session will be permanently deleted."):
            return
        try:
            delete_report(session_id)
            row_frame.destroy()
            self._status_lbl.configure(
                text=f"✅ '{subject}' ({date}) deleted.",
                text_color=(GREEN_TXT[0], GREEN_TXT[0]))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_all(self, reports):
        """ filtered session delete ."""
        if not reports:
            return
        if not messagebox.askyesno(
                "Delete All Reports?",
                f"Are you sure you want to delete all {len(reports)} sessions?\n"
                f"All attendance records will be permanently removed."):
            return

        failed = []
        for rep in reports:
            try:
                delete_report(rep["session_id"])
            except Exception:
                failed.append(rep["session_id"])

        if failed:
            messagebox.showwarning(
                "Partial Delete",
                f"Could not delete {len(failed)} session(s).")
        else:
            self._status_lbl.configure(
                text=f"✅ Successfully deleted {len(reports)} session(s).",
                text_color=(GREEN_TXT[0], GREEN_TXT[0]))

# Comment translated to English.
        for w in self._results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._results_frame,
            text="All reports were deleted. Apply a new filter to continue.",
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUT,
        ).pack(pady=40)

    # ── Export PDF Actions ────────────────────────────────────

    def _export_one_pdf(self, session_id, subject, session_date, teacher_name):
        save_dir = filedialog.askdirectory(title="Select folder to save PDF")
        if not save_dir:
            return

        def do():
            try:
                path = export_session_pdf(
                    session_id, subject, session_date,
                    teacher_name, save_dir)
                self.after(0, lambda p=path: self._status_lbl.configure(
                    text=f"✅ PDF Saved: {os.path.basename(p)}",
                    text_color=(GREEN_TXT[0], GREEN_TXT[0])))
            except Exception as e:
                err = str(e)
                print(f"[PDF ERROR] {err}")   # terminal
                self.after(0, lambda err=err: self._status_lbl.configure(
                    text=f"❌ {err}", text_color=(RED[0], RED[0])))

        threading.Thread(target=do, daemon=True).start()

    def _export_filtered_pdf(self, reports):
        save_dir = filedialog.askdirectory(title="Select folder to save PDF")
        if not save_dir:
            return

        def do():
            try:
                path = export_filtered_pdf(reports, save_dir)
                self.after(0, lambda: self._status_lbl.configure(
                    text=f"✅ PDF Saved: {os.path.basename(path)}",
                    text_color=(GREEN_TXT[0], GREEN_TXT[0])))
            except Exception as e:
                err = str(e)
                self.after(0, lambda err=err: self._status_lbl.configure(
                    text=f"❌ {err}", text_color=(RED[0], RED[0])))

        threading.Thread(target=do, daemon=True).start()

    # ── Refresh ───────────────────────────────────────────────

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._current_reports = []
        self._build_ui()