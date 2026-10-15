# ============================================================
# unknown_faces.py — Admin Unknown Face Log Page
# ============================================================
# Comment translated to English.
# Comment translated to English.
#   - Thumbnail + timestamp + page context
# Comment translated to English.
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from database.db_connection import execute_query
from config import UNKNOWN_FACES_DIR
import os


def _get_all_logs():
    return execute_query(
        """SELECT id, detected_at, image_path, page_context
           FROM unknown_face_logs
           ORDER BY detected_at DESC""",
        fetch="all"
    ) or []


def _delete_log(log_id):
    row = execute_query(
        "SELECT image_path FROM unknown_face_logs WHERE id=%s",
        (log_id,), fetch="one"
    )
    if row and row["image_path"] and os.path.exists(row["image_path"]):
        try:
            os.remove(row["image_path"])
        except Exception:
            pass
    execute_query("DELETE FROM unknown_face_logs WHERE id=%s", (log_id,))


def _clear_all_logs():
    rows = execute_query(
        "SELECT image_path FROM unknown_face_logs", fetch="all"
    ) or []
    for r in rows:
        if r["image_path"] and os.path.exists(r["image_path"]):
            try:
                os.remove(r["image_path"])
            except Exception:
                pass
    execute_query("DELETE FROM unknown_face_logs")


class UnknownFacesPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Unknown Face Log",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=("#e6edf3", "#e6edf3"),
        ).pack(side="left")

        # Clear All
        ctk.CTkButton(
            top, text="🗑  Clear All", width=110, height=32,
            fg_color="transparent",
            border_width=1,
            border_color=("#f85149", "#f85149"),
            text_color=("#f85149", "#f85149"),
            hover_color=("#2d1117", "#2d1117"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=8,
            command=self._clear_all,
        ).pack(side="right")

        ctk.CTkButton(
            top, text="↻ Refresh", width=90, height=32,
            fg_color="transparent", border_width=1,
            border_color=("#30363d", "#30363d"),
            text_color=("#8b949e", "#8b949e"),
            hover_color=("#21262d", "#21262d"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._refresh,
        ).pack(side="right", padx=10)

        ctk.CTkFrame(
            self, height=1, fg_color=("#21262d", "#21262d"),
        ).pack(fill="x", padx=28, pady=12)

        # Load logs
        logs = _get_all_logs()

        # Count badge
        count_color = "#f85149" if logs else "#3fb950"
        ctk.CTkLabel(
            self,
            text=f"{len(logs)} unknown attempt(s) logged",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=(count_color, count_color),
        ).pack(anchor="w", padx=28, pady=(0, 8))

        if not logs:
            ctk.CTkLabel(
                self, text="✅  No unknown face logs found.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=("#3fb950", "#3fb950"),
            ).place(relx=0.5, rely=0.5, anchor="center")
            return

        self._build_grid(logs)

    def _build_grid(self, logs):
        """Card grid layout —  log  card."""
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_fg_color=("#161b22", "#161b22"),
        )
        scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        COLS = 4
        for idx, log in enumerate(logs):
            row_i = idx // COLS
            col_i = idx % COLS
            self._make_card(scroll, log, row_i, col_i)
            scroll.columnconfigure(col_i, weight=1)

    def _make_card(self, parent, log, row, col):
        """ unknown face card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#161b22", "#161b22"),
            corner_radius=10,
            border_width=1,
            border_color=("#30363d", "#30363d"),
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        # Thumbnail
        thumb_frame = ctk.CTkFrame(
            card,
            width=140, height=110,
            fg_color=("#0d1117", "#0d1117"),
            corner_radius=6,
        )
        thumb_frame.pack(padx=10, pady=(10, 6))
        thumb_frame.pack_propagate(False)

        img_path = log.get("image_path")
        if img_path and os.path.exists(img_path):
            try:
                pil = Image.open(img_path).resize((140, 110))
                ctk_img = ctk.CTkImage(light_image=pil, size=(140, 110))
                lbl = ctk.CTkLabel(thumb_frame, image=ctk_img, text="")
                lbl._image = ctk_img
                lbl.pack()
            except Exception:
                self._placeholder_thumb(thumb_frame)
        else:
            self._placeholder_thumb(thumb_frame)

        # Timestamp
        detected = log.get("detected_at")
        ts_str = detected.strftime(
            "%d %b %Y\n%I:%M:%S %p") if detected else "—"

        ctk.CTkLabel(
            card, text=ts_str,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#8b949e", "#8b949e"),
            justify="center",
        ).pack(pady=(0, 4))

        # Context badge
        ctx = (log.get("page_context") or "unknown").replace("_", " ").title()
        ctk.CTkLabel(
            card, text=ctx,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=("#e3b341", "#e3b341"),
            fg_color=("#2b2000", "#2b2000"),
            corner_radius=4,
            padx=8, pady=2,
        ).pack(pady=(0, 6))

        # Delete button
        lid = log["id"]
        ctk.CTkButton(
            card, text="Delete", height=26,
            fg_color="transparent",
            border_width=1,
            border_color=("#f85149", "#f85149"),
            text_color=("#f85149", "#f85149"),
            hover_color=("#2d1117", "#2d1117"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=6,
            command=lambda i=lid, c=card: self._delete_one(i, c),
        ).pack(fill="x", padx=10, pady=(0, 10))

    def _placeholder_thumb(self, parent):
        ctk.CTkLabel(
            parent, text="?",
            font=ctk.CTkFont(family="Segoe UI", size=36),
            text_color=("#30363d", "#30363d"),
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ── Actions ───────────────────────────────────────────────

    def _delete_one(self, log_id, card_widget):
        if messagebox.askyesno("Delete?", "Delete this log entry?"):
            try:
                _delete_log(log_id)
                card_widget.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear_all(self):
        if messagebox.askyesno("Clear All?",
                               "Are you sure you want to delete all unknown face logs and screenshots?"):
            try:
                _clear_all_logs()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()