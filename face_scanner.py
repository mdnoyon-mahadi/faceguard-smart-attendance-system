# ============================================================
# face_scanner.py — Face Scanner (Multi-Class Support)
# ============================================================
# নতুন Features:
#   - একই সময়ে একাধিক class → আলাদা card (scrollable)
#   - Student scan → dept/sem/shift দিয়ে সঠিক class match
#   - Teacher scan → student এর মতো pending/complete status
#   - Scanner card → teacher এর subject + PENDING/COMPLETE badge
#   - Entry end time তে exact → "Pending" report_status DB তে set হয়
#   - Exit end time তে exact → "Complete" report_status DB তে set হয়
#   - Time এর বাইরে scan → "Attendance not possible"
#   - Scan complete → 10 sec highlight notification
# ============================================================

import customtkinter as ctk
import threading
import time as time_module
import cv2
from PIL import Image
from datetime import datetime, timedelta

from services.face_service import (load_all_encodings, recognize_face,
                                   draw_face_box, save_unknown_face)
from services.routine_service import (get_active_routines,
                                      get_todays_all_routines,
                                      get_or_create_session, close_session)
from services.attendance_service import (
    student_scan_by_identity, teacher_scan_by_identity,
    get_session_scan_counts, get_teacher_scan_status)
from models.user_model import get_user_by_id
from models.report_model import set_session_report_status
from config import APP_NAME, WEBCAM_INDEX, EXTRA_CAMERAS
from transitions import PageTransition, NavigationLock

SCAN_COOLDOWN_SEC = 4

# ── Project colour palette ─────────────────────────────────────────────────────
_BG         = "#0d1117"
_SURFACE    = "#161b22"
_SURFACE2   = "#1c2128"
_BORDER     = "#21262d"
_BORDER2    = "#1e293b"
_ACCENT     = "#1f6feb"
_ACCENT_LT  = "#58a6ff"
_SUCCESS    = "#238636"
_SUCCESS_LT = "#3fb950"
_ERROR      = "#f85149"
_WARN       = "#e3b341"
_PURPLE     = "#6e40c9"
_TEXT_PRI   = "#e6edf3"
_TEXT_SEC   = "#8b949e"
_TEXT_MUT   = "#484f58"

# Notification backgrounds (dark tinted)
_NOTIF_GREEN_BG  = "#0d2016"
_NOTIF_RED_BG    = "#2d1117"
_NOTIF_ORANGE_BG = "#2a1d00"
_NOTIF_BLUE_BG   = "#0d1f3c"


class FaceScanner(ctk.CTkToplevel):

    def __init__(self, on_close=None):
        super().__init__()
        # [ANIM] Hide immediately — zero flicker during widget construction
        PageTransition.prepare_window(self)

        self.on_close = on_close

        self.title(f"{APP_NAME} — Face Scanner")
        self.geometry("1200x660")
        self.resizable(False, False)
        self._center_window(1200, 660)
        self.protocol("WM_DELETE_WINDOW", self._stop_and_close)

        # State
        self._cap = None
        self._extra_caps = []
        self._running = False
        self._students = []
        self._teachers = []
        self._last_scan_time = {}
        self._processing = False

        self._active_routines = []
        self._sessions = {}
        self._closed_sessions = set()
        self._scheduled_closes = set()

        self._latest_frame = None
        self._display_frame = None
        self._frame_lock = threading.Lock()
        self._display_lock = threading.Lock()
        self._recognition_running = False

        self._build_ui()
        self._init_scanner()
        self.lift()
        self.focus_force()
        # [ANIM] Smooth ease-out fade in after full construction
        PageTransition.fade_in(self, steps=14, ms=12)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(fg_color=(_BG, _BG))

        # ── Header ────────────────────────────────────────────
        header = ctk.CTkFrame(
            self,
            fg_color=(_SURFACE, _SURFACE),
            corner_radius=0,
            height=52,
            border_width=1,
            border_color=(_BORDER, _BORDER),
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            width=80,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color=(_BORDER, _BORDER),
            text_color=(_TEXT_SEC, _TEXT_SEC),
            hover_color=(_SURFACE2, _SURFACE2),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=6,
            command=self._stop_and_close,
        )
        back_btn.place(x=16, rely=0.5, anchor="w")

        # Accent underline stripe on left of header
        ctk.CTkFrame(
            header,
            fg_color=(_ACCENT, _ACCENT),
            width=3,
            corner_radius=0,
        ).place(x=0, y=0, relheight=1)

        ctk.CTkLabel(
            header,
            text="🎯  Face Scanner",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=(_TEXT_PRI, _TEXT_PRI),
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.clock_lbl = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=(_TEXT_MUT, _TEXT_MUT),
        )
        self.clock_lbl.place(relx=1.0, x=-16, rely=0.5, anchor="e")
        self._tick_clock()

        # ── Body ──────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Left: Camera panel ────────────────────────────────
        left = ctk.CTkFrame(
            body,
            fg_color=(_SURFACE, _SURFACE),
            corner_radius=12,
            border_width=1,
            border_color=(_BORDER, _BORDER),
            width=500,
        )
        left.pack(side="left", fill="both", expand=False, padx=(0, 12))
        left.pack_propagate(False)

        # Camera label
        self.camera_label = ctk.CTkLabel(
            left,
            text="📷  Camera চালু হচ্ছে...",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=(_TEXT_MUT, _TEXT_MUT),
            width=460,
            height=345,
            fg_color=(_BG, _BG),
            corner_radius=8,
        )
        self.camera_label.pack(pady=(14, 6), padx=16)

        # Notification box
        self.notif_box = ctk.CTkFrame(
            left,
            fg_color=(_BG, _BG),
            corner_radius=8,
            border_width=1,
            border_color=(_BORDER, _BORDER),
            height=56,
        )
        self.notif_box.pack(fill="x", padx=16, pady=(0, 6))
        self.notif_box.pack_propagate(False)

        self.notif_lbl = ctk.CTkLabel(
            self.notif_box,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=(_SUCCESS_LT, _SUCCESS_LT),
            wraplength=440,
        )
        self.notif_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Status bar
        self.status_lbl = ctk.CTkLabel(
            left,
            text="Initializing...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=(_TEXT_SEC, _TEXT_SEC),
            wraplength=460,
        )
        self.status_lbl.pack(pady=(0, 8), padx=16)

        # ── Right: Active class cards (scrollable) ────────────
        right_outer = ctk.CTkFrame(body, fg_color="transparent")
        right_outer.pack(side="right", fill="both", expand=True)

        # Section header row
        sec_row = ctk.CTkFrame(right_outer, fg_color="transparent", height=28)
        sec_row.pack(fill="x", pady=(0, 6))
        sec_row.pack_propagate(False)

        ctk.CTkLabel(
            sec_row,
            text="Active Classes",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=(_TEXT_PRI, _TEXT_PRI),
        ).pack(side="left")

        # Accent line under section title
        ctk.CTkFrame(
            right_outer,
            fg_color=(_ACCENT, _ACCENT),
            height=2,
            corner_radius=1,
        ).pack(fill="x", pady=(0, 8))

        self._cards_scroll = ctk.CTkScrollableFrame(
            right_outer,
            fg_color="transparent",
            scrollbar_fg_color=(_SURFACE, _SURFACE),
            scrollbar_button_color=(_BORDER, _BORDER),
            scrollbar_button_hover_color=(_ACCENT, _ACCENT),
        )
        self._cards_scroll.pack(fill="both", expand=True)

        self._no_class_lbl = ctk.CTkLabel(
            self._cards_scroll,
            text="⏳  কোনো active class নেই এই মুহূর্তে।",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=(_TEXT_MUT, _TEXT_MUT),
        )
        self._no_class_lbl.pack(pady=40)

        self._card_widgets = {}

    # ── Init ──────────────────────────────────────────────────

    def _init_scanner(self):
        self._running = True
        threading.Thread(target=self._load_and_start, daemon=True).start()

    def _load_and_start(self):
        threading.Thread(
            target=self._camera_capture_loop, daemon=True).start()

        for cam_url in EXTRA_CAMERAS:
            if cam_url:
                threading.Thread(
                    target=self._extra_camera_loop,
                    args=(cam_url,), daemon=True).start()

        self.after(100, self._update_camera_ui)

        self.after(0, lambda: self._set_status(
            "Encodings load হচ্ছে...", "gray"))
        try:
            self._students = load_all_encodings(role="student")
            self._teachers = load_all_encodings(role="teacher")
        except Exception as e:
            self.after(0, lambda: self._set_status(
                f"❌ Encoding load error: {e}", "red"))
            return

        self.after(0, self._refresh_routines)
        self.after(500, self._schedule_todays_sessions)
        threading.Thread(
            target=self._recognition_loop, daemon=True).start()
        self.after(10_000, self._routine_watcher)

    def _schedule_todays_sessions(self):
        try:
            all_routines = get_todays_all_routines()
            for r in all_routines:
                rid = r["routine_id"]
                if rid not in self._sessions:
                    try:
                        sid = get_or_create_session(
                            rid, r["teacher_id"], r["subject"])
                        self._sessions[rid] = sid
                    except Exception:
                        continue
                self._schedule_report_submit(r)
        except Exception:
            pass

    # ── Routine Refresh ───────────────────────────────────────

    def _refresh_routines(self):
        routines = get_active_routines()
        self._active_routines = routines

        for r in routines:
            rid = r["routine_id"]
            if rid not in self._sessions:
                try:
                    sid = get_or_create_session(
                        rid, r["teacher_id"], r["subject"])
                    self._sessions[rid] = sid
                except Exception:
                    pass

        self._rebuild_cards()

        for r in routines:
            self._schedule_report_submit(r)

        if not routines:
            self._set_status(
                "কোনো active class নেই। Routine time এ আসুন।", "gray")
        else:
            phases = set(r["phase"] for r in routines)
            if "entry" in phases:
                self._set_status(
                    f"📋 {len(routines)} টি class active। Entry scan চলছে।", "green")
            elif "exit" in phases:
                self._set_status(
                    "✅ Exit scan চলছে। Pending attendance complete করুন।", "green")
            else:
                self._set_status(
                    "⏳ Class চলছে। Exit scan এর জন্য অপেক্ষা করুন।", "orange")

    def _rebuild_cards(self):
        for w in self._card_widgets.values():
            w.destroy()
        self._card_widgets.clear()

        if not self._active_routines:
            self._no_class_lbl.pack(pady=40)
            return

        self._no_class_lbl.pack_forget()

        for r in self._active_routines:
            card = self._make_class_card(r)
            self._card_widgets[r["routine_id"]] = card

    def _make_class_card(self, r):
        phase = r["phase"]
        if phase == "entry":
            border_color  = _SUCCESS
            border_hover  = _SUCCESS_LT
            phase_color   = _SUCCESS_LT
            phase_text    = "🟢 ENTRY SCAN"
        elif phase == "exit":
            border_color  = _ACCENT
            border_hover  = _ACCENT_LT
            phase_color   = _ACCENT_LT
            phase_text    = "🔵 EXIT SCAN"
        else:
            border_color  = _BORDER
            border_hover  = _WARN
            phase_color   = _WARN
            phase_text    = "⏳ CLASS IN PROGRESS"

        shift_icon = "🌅" if r.get("shift") == "morning" else "☀️"

        card = ctk.CTkFrame(
            self._cards_scroll,
            fg_color=(_SURFACE, _SURFACE),
            corner_radius=10,
            border_width=2,
            border_color=(border_color, border_color),
        )
        card.pack(fill="x", pady=5, padx=2)

        # ── Hover animation helpers ───────────────────────────
        def _card_enter(e,
                        c=card,
                        hc=border_hover):
            c.configure(
                fg_color=(_SURFACE2, _SURFACE2),
                border_color=(hc, hc),
            )

        def _card_leave(e,
                        c=card,
                        bc=border_color):
            c.configure(
                fg_color=(_SURFACE, _SURFACE),
                border_color=(bc, bc),
            )

        card.bind("<Enter>", _card_enter)
        card.bind("<Leave>", _card_leave)

        # ── Phase badge row ───────────────────────────────────
        badge_row = ctk.CTkFrame(card, fg_color="transparent")
        badge_row.pack(fill="x", padx=14, pady=(10, 4))
        badge_row.bind("<Enter>", _card_enter)
        badge_row.bind("<Leave>", _card_leave)

        ctk.CTkLabel(
            badge_row,
            text=phase_text,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=(phase_color, phase_color),
        ).pack(side="left")

        ctk.CTkLabel(
            badge_row,
            text=f"{shift_icon} {r.get('shift','').title()}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=(_WARN, _WARN),
        ).pack(side="right")

        # ── Subject + teacher ─────────────────────────────────
        subj_lbl = ctk.CTkLabel(
            card,
            text=r["subject"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=(_TEXT_PRI, _TEXT_PRI),
            anchor="w",
        )
        subj_lbl.pack(anchor="w", padx=14, pady=(2, 0))
        subj_lbl.bind("<Enter>", _card_enter)
        subj_lbl.bind("<Leave>", _card_leave)

        teach_lbl = ctk.CTkLabel(
            card,
            text=f"👨‍🏫 {r['teacher_name']}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=(_TEXT_SEC, _TEXT_SEC),
            anchor="w",
        )
        teach_lbl.pack(anchor="w", padx=14)
        teach_lbl.bind("<Enter>", _card_enter)
        teach_lbl.bind("<Leave>", _card_leave)

        # Thin accent divider
        ctk.CTkFrame(
            card,
            fg_color=(border_color, border_color),
            height=1,
            corner_radius=0,
        ).pack(fill="x", padx=14, pady=(8, 6))

        # ── Info grid ─────────────────────────────────────────
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=14, pady=(0, 6))
        info_frame.bind("<Enter>", _card_enter)
        info_frame.bind("<Leave>", _card_leave)

        infos = [
            ("Dept",       r["department"]),
            ("Semester",   r["semester"]),
            ("Class Time", f"{r['class_start']} – {r['class_end']}"),
            ("Entry Scan",
             f"{r['entry_start'].strftime('%I:%M %p')} – {r['entry_end'].strftime('%I:%M %p')}"),
            ("Exit Scan",
             f"{r['exit_start'].strftime('%I:%M %p')} – {r['exit_end'].strftime('%I:%M %p')}"),
        ]

        for i, (lbl, val) in enumerate(infos):
            col = ctk.CTkFrame(info_frame, fg_color="transparent")
            col.grid(row=i // 3, column=i % 3,
                     padx=(0, 16), pady=2, sticky="w")
            ctk.CTkLabel(
                col,
                text=lbl + ":",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=(_TEXT_MUT, _TEXT_MUT),
            ).pack(anchor="w")
            if "Entry" in lbl:
                tc = _SUCCESS_LT
            elif "Exit" in lbl:
                tc = _ACCENT_LT
            else:
                tc = _TEXT_SEC
            ctk.CTkLabel(
                col,
                text=val,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=(tc, tc),
            ).pack(anchor="w")

        # ── Teacher attendance badge ──────────────────────────
        sid = self._sessions.get(r["routine_id"])
        if sid:
            self._add_teacher_status_badge(card, sid, r["teacher_id"],
                                           _card_enter, _card_leave)

        # ── Student count row ─────────────────────────────────
        if sid:
            try:
                counts = get_session_scan_counts(sid)
                cnt_lbl = ctk.CTkLabel(
                    card,
                    text=(f"👥 Student  "
                          f"✅ {counts['complete']} complete   "
                          f"⏳ {counts['pending']} pending"),
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=(_TEXT_MUT, _TEXT_MUT),
                )
                cnt_lbl.pack(anchor="w", padx=14, pady=(0, 10))
                cnt_lbl.bind("<Enter>", _card_enter)
                cnt_lbl.bind("<Leave>", _card_leave)
            except Exception:
                pass

        return card

    def _add_teacher_status_badge(self, card, session_id, teacher_id,
                                  enter_cb, leave_cb):
        try:
            rec = get_teacher_scan_status(session_id, teacher_id)
        except Exception:
            rec = None

        if rec is None:
            badge_text  = "👨‍🏫 Teacher  ⬜ Not Scanned Yet"
            badge_color = (_TEXT_MUT, _TEXT_MUT)
        elif rec["status"] == "pending":
            sin = str(rec["scan_in_time"])[11:16] if rec["scan_in_time"] else "?"
            badge_text  = f"👨‍🏫 Teacher  ⏳ PENDING  (in: {sin})"
            badge_color = (_WARN, _WARN)
        else:
            sin  = str(rec["scan_in_time"])[11:16]  if rec["scan_in_time"]  else "?"
            sout = str(rec["scan_out_time"])[11:16] if rec["scan_out_time"] else "?"
            badge_text  = f"👨‍🏫 Teacher  ✅ COMPLETE  ({sin} → {sout})"
            badge_color = (_SUCCESS_LT, _SUCCESS_LT)

        lbl = ctk.CTkLabel(
            card,
            text=badge_text,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=badge_color,
            anchor="w",
        )
        lbl.pack(anchor="w", padx=14, pady=(0, 4))
        lbl.bind("<Enter>", enter_cb)
        lbl.bind("<Leave>", leave_cb)

    # ── Timed Report Submit ───────────────────────────────────

    def _schedule_report_submit(self, routine):
        rid = routine["routine_id"]
        now = datetime.now()

        entry_end_dt   = datetime.combine(now.date(), routine["entry_end"])
        entry_delay_ms = int((entry_end_dt - now).total_seconds() * 1000)

        exit_end_dt    = datetime.combine(now.date(), routine["exit_end"])
        exit_delay_ms  = int((exit_end_dt - now).total_seconds() * 1000)

        sched_key_entry = f"{rid}_entry"
        sched_key_exit  = f"{rid}_exit"

        if sched_key_entry not in self._scheduled_closes:
            self._scheduled_closes.add(sched_key_entry)
            if entry_delay_ms > 0:
                self.after(entry_delay_ms,
                           lambda r=routine: self._submit_entry_report(r))
            else:
                self.after(100,
                           lambda r=routine: self._submit_entry_report(r))

        if sched_key_exit not in self._scheduled_closes:
            self._scheduled_closes.add(sched_key_exit)
            if exit_delay_ms > 0:
                self.after(exit_delay_ms,
                           lambda r=routine: self._submit_final_report(r))
            else:
                self.after(200,
                           lambda r=routine: self._submit_final_report(r))

    def _submit_entry_report(self, routine):
        if not self.winfo_exists():
            return
        sid = self._sessions.get(routine["routine_id"])
        if not sid:
            return

        def _do_db():
            try:
                set_session_report_status(sid, "pending")
            except Exception as e:
                self.after(0, lambda: self._set_status(
                    f"❌ Pending report DB error: {e}", "red"))

        threading.Thread(target=_do_db, daemon=True).start()
        self._set_status(
            f"📋 {routine['subject']} — Entry scan শেষ। "
            f"Pending Attendance Report তৈরি হয়েছে।", "green")
        self._rebuild_cards()

    def _submit_final_report(self, routine):
        if not self.winfo_exists():
            return
        sid = self._sessions.get(routine["routine_id"])
        if not sid:
            return

        def _do_db():
            try:
                set_session_report_status(sid, "complete")
            except Exception as e:
                self.after(0, lambda: self._set_status(
                    f"❌ Complete report DB error: {e}", "red"))
            if sid not in self._closed_sessions:
                self._closed_sessions.add(sid)
                try:
                    close_session(sid)
                except Exception:
                    pass

        threading.Thread(target=_do_db, daemon=True).start()
        self._set_status(
            f"✅ {routine['subject']} — Class শেষ। "
            f"Complete Attendance Report তৈরি হয়েছে।", "green")
        self._rebuild_cards()

    # ── Routine Watcher ───────────────────────────────────────

    def _routine_watcher(self):
        if not self.winfo_exists():
            return
        self._refresh_routines()
        if self.winfo_exists():
            self.after(15_000, self._routine_watcher)

    # ── Camera Capture Loop ───────────────────────────────────

    def _camera_capture_loop(self):
        self.after(0, lambda: self._set_status("📷 Camera খুলছে...", "gray"))

        self._cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = cv2.VideoCapture(WEBCAM_INDEX)

        if not self._cap.isOpened():
            opened = False
            for idx in range(4):
                if idx == WEBCAM_INDEX:
                    continue
                for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
                    tc = cv2.VideoCapture(idx, backend)
                    if tc.isOpened():
                        self._cap = tc
                        opened = True
                        break
                    tc.release()
                if opened:
                    break
            if not opened:
                self.after(0, lambda: self._set_status(
                    "❌ Webcam পাওয়া যায়নি।", "red"))
                return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.after(0, lambda: self.camera_label.configure(text=""))

        fail = 0
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                fail += 1
                time_module.sleep(0.03)
                if fail > 100:
                    self.after(0, lambda: self._set_status(
                        "❌ Camera frame পাওয়া যাচ্ছে না।", "red"))
                    break
                continue
            fail = 0
            with self._frame_lock:
                self._latest_frame = frame
            time_module.sleep(0.01)

        if self._cap:
            self._cap.release()

    def _extra_camera_loop(self, cam_url: str):
        cap = cv2.VideoCapture(cam_url)
        if not cap.isOpened():
            self.after(0, lambda u=cam_url: self._set_status(
                f"⚠️ Camera connect হয়নি: {u}", "orange"))
            return

        self.after(0, lambda u=cam_url: self._set_status(
            f"📱 Mobile camera connected: {u}", "green"))

        fail = 0
        while self._running:
            ret, frame = cap.read()
            if not ret:
                fail += 1
                time_module.sleep(0.1)
                if fail > 50:
                    cap.release()
                    time_module.sleep(2)
                    cap = cv2.VideoCapture(cam_url)
                    fail = 0
                continue
            fail = 0

            scan_phases = [r["phase"] for r in self._active_routines
                           if r["phase"] in ("entry", "exit")]

            if scan_phases and not self._processing:
                known = self._students + self._teachers
                result, person, location = recognize_face(frame, known)

                if result == "matched" and person:
                    uid = person["id"]
                    now = datetime.now()
                    last = self._last_scan_time.get(uid)
                    if last is None or (now - last).total_seconds() >= SCAN_COOLDOWN_SEC:
                        self._last_scan_time[uid] = now
                        self._processing = True
                        self.after(0, lambda p=person: self._process_scan(p))
                elif result == "unknown":
                    self.after(0, lambda f=frame.copy(): self._handle_unknown(f))

            time_module.sleep(0.05)

        cap.release()

    # ── Recognition Loop ──────────────────────────────────────

    def _recognition_loop(self):
        self._recognition_running = True

        while self._running and self._recognition_running:
            with self._frame_lock:
                frame = (self._latest_frame.copy()
                         if self._latest_frame is not None else None)

            if frame is None:
                time_module.sleep(0.05)
                continue

            display = frame.copy()

            scan_phases = [r["phase"] for r in self._active_routines
                           if r["phase"] in ("entry", "exit")]

            if scan_phases and not self._processing:
                known = self._students + self._teachers
                result, person, location = recognize_face(frame, known)

                if result == "matched" and person:
                    uid  = person["id"]
                    now  = datetime.now()
                    last = self._last_scan_time.get(uid)

                    if last is None or (now - last).total_seconds() >= SCAN_COOLDOWN_SEC:
                        self._last_scan_time[uid] = now
                        self._processing = True
                        display = draw_face_box(
                            display, person.get("name", ""),
                            color=(0, 255, 0), location=location)
                        self.after(0, lambda p=person: self._process_scan(p))
                    else:
                        display = draw_face_box(
                            display, person.get("name", "✓"),
                            color=(0, 200, 100), location=location)

                elif result == "unknown":
                    display = draw_face_box(
                        display, "UNKNOWN",
                        color=(0, 0, 255), location=location)
                    self.after(0, lambda f=frame.copy(): self._handle_unknown(f))

            with self._display_lock:
                self._display_frame = display

            time_module.sleep(0.05)

    # ── Scan Processing ───────────────────────────────────────

    def _process_scan(self, person):
        try:
            uid        = person["id"]
            name       = person.get("name", "Unknown")
            is_teacher = any(t["id"] == uid for t in self._teachers)

            if not self._active_routines:
                self._show_notification(
                    f"⚠️ {name}\nকোনো active class নেই।", "orange")
                return

            active_phases = [r["phase"] for r in self._active_routines]
            if all(p == "between" for p in active_phases):
                self._show_notification(
                    f"🚫 {name}\nAttendance not possible এই সময়ে।", "red")
                return

            if is_teacher:
                results  = teacher_scan_by_identity(uid)
                msgs     = []
                for action, msg, sid in results:
                    msgs.append(msg)
                if any(sid for _, _, sid in results):
                    self._refresh_routines()
                combined     = " | ".join(msgs)
                first_action = results[0][0] if results else "error"
                if first_action in ("teacher_in", "teacher_out"):
                    color = "green"
                elif first_action in ("already_entry", "already_done"):
                    color = "blue"
                else:
                    color = "orange"
                self._show_notification(f"👨‍🏫 {name}\n{combined}", color)
                self._set_status(combined, color)

            else:
                user_info = get_user_by_id(uid)
                if not user_info:
                    self._show_notification(
                        f"❌ {name}\nUser info পাওয়া যায়নি।", "red")
                    return

                dept  = user_info.get("department", "")
                sem   = user_info.get("semester", "")
                shift = user_info.get("shift") or self._get_student_shift(dept, sem)

                matching = [r for r in self._active_routines
                            if r["department"] == dept
                            and r["semester"] == sem
                            and r.get("shift") == shift
                            and r["phase"] in ("entry", "exit")]

                if not matching:
                    self._show_notification(
                        f"🚫 {name}\nAttendance not possible — তোমার class এর time এ আসো।",
                        "red")
                    return

                routine        = matching[0]
                phase          = routine["phase"]
                action, msg, sid = student_scan_by_identity(
                    uid, dept, sem, shift, phase,
                    routine_id=routine["routine_id"])

                if action in ("scan_in", "scan_out"):
                    color = "green"
                elif action in ("already_entry", "already_done"):
                    color = "blue"
                else:
                    color = "orange"

                self._show_notification(
                    f"{'🟢' if phase == 'entry' else '🔵'} {name}\n{msg}",
                    color)
                self._set_status(msg, color)
                
                # Refresh attendance state for successful scans and exit scans
                if sid or action == "scan_out":
                    self._refresh_routines()
                    self._set_status(msg, color)

        except Exception as e:
            self._set_status(f"❌ Error: {e}", "red")
        finally:
            self.after(SCAN_COOLDOWN_SEC * 1000, self._reset_processing)

    def _get_student_shift(self, department, semester):
        for r in self._active_routines:
            if r["department"] == department and r["semester"] == semester:
                return r.get("shift", "morning")
        return "morning"

    def _reset_processing(self):
        self._processing = False

    def _handle_unknown(self, frame):
        save_unknown_face(frame, page_context="face_scanner")
        self._show_notification("⚠️  Unknown Face — Log করা হয়েছে", "red")

    # ── Notification (10 sec highlight) ──────────────────────

    def _show_notification(self, msg, color="green"):
        color_map = {
            "green":  (_SUCCESS_LT,  _NOTIF_GREEN_BG,  _SUCCESS),
            "red":    (_ERROR,        _NOTIF_RED_BG,    _ERROR),
            "orange": (_WARN,         _NOTIF_ORANGE_BG, _WARN),
            "blue":   (_ACCENT_LT,    _NOTIF_BLUE_BG,   _ACCENT),
        }
        tc, bg, bc = color_map.get(color, color_map["green"])

        self.notif_box.configure(
            fg_color=(bg, bg),
            border_color=(bc, bc),
        )
        self.notif_lbl.configure(text=msg, text_color=(tc, tc))
        self.after(10_000, self._clear_notification)

    def _clear_notification(self):
        if self.winfo_exists():
            self.notif_box.configure(
                fg_color=(_BG, _BG),
                border_color=(_BORDER, _BORDER),
            )
            self.notif_lbl.configure(text="")

    # ── Camera UI ─────────────────────────────────────────────

    def _update_camera_ui(self):
        if not self.winfo_exists():
            return

        frame = None
        with self._display_lock:
            if self._display_frame is not None:
                frame = self._display_frame.copy()
        if frame is None:
            with self._frame_lock:
                if self._latest_frame is not None:
                    frame = self._latest_frame.copy()

        if frame is not None:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb).resize((460, 345))
                img = ctk.CTkImage(light_image=pil, size=(460, 345))
                self.camera_label.configure(image=img, text="")
                self.camera_label._image = img
            except Exception:
                pass

        if self.winfo_exists():
            self.after(33, self._update_camera_ui)

    # ── Helpers ───────────────────────────────────────────────

    def _set_status(self, msg, color="gray"):
        color_map = {
            "gray":   (_TEXT_SEC,    _TEXT_SEC),
            "green":  (_SUCCESS_LT,  _SUCCESS_LT),
            "red":    (_ERROR,       _ERROR),
            "orange": (_WARN,        _WARN),
            "blue":   (_ACCENT_LT,   _ACCENT_LT),
        }
        if self.winfo_exists():
            self.status_lbl.configure(
                text=msg,
                text_color=color_map.get(color, (_TEXT_SEC, _TEXT_SEC)),
            )

    def _tick_clock(self):
        if self.winfo_exists():
            self.clock_lbl.configure(
                text=datetime.now().strftime("%I:%M:%S %p"))
            self.after(1000, self._tick_clock)

    def _stop_and_close(self):
        self._running = False
        self._recognition_running = False
        # [ANIM] Fade out smoothly before destroying
        NavigationLock.release()          # ensure lock is free
        PageTransition.fade_out(self, on_done=self._do_close, steps=10, ms=12)

    def _do_close(self):
        if self._cap:
            self._cap.release()
        self.destroy()
        if self.on_close:
            self.on_close()

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")