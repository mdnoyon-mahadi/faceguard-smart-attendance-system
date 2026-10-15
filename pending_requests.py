# ============================================================
# pending_requests.py — Admin Pending Requests Page
# ============================================================
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
from theme import ThemeManager
from models.user_model import (
    get_all_pending_requests,
    approve_request,
    reject_request,
)

C = ThemeManager.get_color


class PendingRequestsPage(ctk.CTkFrame):

    def __init__(self, parent, on_refresh=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_refresh = on_refresh
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            top, text="Pending Requests",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).grid(row=0, column=0, sticky="w")

        action_wrap = ctk.CTkFrame(top, fg_color="transparent")
        action_wrap.grid(row=0, column=1, sticky="e")

        try:
            requests = get_all_pending_requests()
        except Exception:
            requests = []

        count_color = "#e3b341" if requests else C("success")
        count_text = f"{len(requests)} pending" if requests else "No pending requests"

        badge = ctk.CTkFrame(
            action_wrap,
            fg_color=C("bg2"),
            corner_radius=16,
            border_width=1,
            border_color=C("card_border"),
        )
        badge.pack(side="right", padx=(10, 0))
        ctk.CTkLabel(
            badge, text=count_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=(count_color, count_color),
        ).pack(padx=12, pady=6)

        refresh_btn = ctk.CTkButton(
            action_wrap, text="↻ Refresh", width=96, height=32,
            fg_color="transparent",
            border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._refresh,
        )
        refresh_btn.pack(side="right")
        self._bind_soft_hover(refresh_btn, "transparent", C("hover"))

        ctk.CTkFrame(self, height=1, fg_color=C("sep")).pack(fill="x", padx=28, pady=16)

        if not requests:
            self._show_empty()
        else:
            self._build_list(requests)

    def _show_empty(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text="◌",
            font=ctk.CTkFont(family="Segoe UI", size=52),
            text_color=C("sep"),
        ).pack()

        ctk.CTkLabel(
            frame, text="No pending requests",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=C("text_dim"),
        ).pack(pady=(8, 0))

    def _build_list(self, requests):
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_fg_color=C("bg2"),
        )
        scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        for req in requests:
            self._make_request_card(scroll, req)

    def _make_request_card(self, parent, req):
        card = ctk.CTkFrame(
            parent,
            fg_color=C("card"),
            corner_radius=14,
            border_width=1,
            border_color=C("card_border"),
        )
        card.pack(fill="x", pady=8)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        # Avatar circle with initials
        initials = "".join([w[0].upper() for w in req["name"].split()[:2]])
        avatar = ctk.CTkFrame(
            left,
            width=48, height=48,
            fg_color=C("btn_active"),
            corner_radius=24,
            border_width=1,
            border_color=C("accent3"),
        )
        avatar.pack(side="left", padx=(0, 14))
        avatar.pack_propagate(False)

        ctk.CTkLabel(
            avatar, text=initials,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=C("accent3"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Info
        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left", fill="x")

        ctk.CTkLabel(
            info,
            text=req["name"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=C("text"),
            anchor="w",
        ).pack(anchor="w")

        details = f"Roll: {req['roll']}   |   {req['department']}   |   {req['semester']} Semester"
        ctk.CTkLabel(
            info, text=details,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C("text_dim"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        phone_text = f"📞 {req['phone']}" if req.get("phone") else ""
        submitted = req["submitted_at"].strftime(
            "%d %b %Y, %I:%M %p") if req.get("submitted_at") else ""

        ctk.CTkLabel(
            info,
            text=f"{phone_text}   🕐 {submitted}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        req_id = req["id"]

        approve_btn = ctk.CTkButton(
            btn_frame,
            text="✓  Approve",
            width=108, height=36,
            fg_color=("#22c55e", "#22c55e"),
            hover_color=("#34d399", "#34d399"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=10,
            command=lambda rid=req_id, c=card, n=req["name"]: self._approve(
                rid, c, n),
        )
        approve_btn.pack(pady=(0, 8))
        self._bind_action_hover(approve_btn, ("#22c55e", "#22c55e"), ("#34d399", "#34d399"))

        reject_btn = ctk.CTkButton(
            btn_frame,
            text="✗  Reject",
            width=108, height=36,
            fg_color="transparent",
            border_width=1,
            border_color=("#f85149", "#f85149"),
            text_color=("#f85149", "#f85149"),
            hover_color=("#2d1117", "#2d1117"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=10,
            command=lambda rid=req_id, c=card, n=req["name"]: self._reject(
                rid, c, n),
        )
        reject_btn.pack()
        self._bind_action_hover(reject_btn, "transparent", ("#2d1117", "#2d1117"))
        self._bind_card_hover(card)

    # ── Actions ───────────────────────────────────────────────

    def _approve(self, request_id, card_widget, name):
        confirm = messagebox.askyesno(
            "Approve Request?",
            f"Are you sure you want to approve registration for '{name}'?\nOnce approved, the student will be able to log in.",
        )
        if not confirm:
            return

        try:
            approve_request(request_id)
            self._animate_remove(card_widget, success=True, name=name)
        except Exception as e:
            messagebox.showerror("Error", f"Could not approve:\n{e}")

    def _reject(self, request_id, card_widget, name):
        confirm = messagebox.askyesno(
            "Reject Request?",
            f"Are you sure you want to reject registration for '{name}'?",
        )
        if not confirm:
            return

        try:
            reject_request(request_id)
            self._animate_remove(card_widget, success=False, name=name)
        except Exception as e:
            messagebox.showerror("Error", f"Could not reject:\n{e}")

    def _animate_remove(self, card_widget, success, name):
        flash_color = "#0d2a0f" if success else "#2d1117"
        card_widget.configure(fg_color=(flash_color, flash_color))
        start_pad = 8

        def step(i=0):
            if not card_widget.winfo_exists():
                return
            if i >= 7:
                card_widget.destroy()
                if self.on_refresh:
                    self.on_refresh()
                return
            card_widget.pack_configure(pady=max(0, start_pad - i))
            card_widget.configure(corner_radius=max(2, 14 - i))
            self.after(45, lambda: step(i + 1))

        self.after(180, step)

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    # ── UI helpers ────────────────────────────────────────────

    def _bind_soft_hover(self, btn, normal_color, hover_color):
        def _enter(_e):
            btn.configure(fg_color=hover_color, border_color=C("accent3"))

        def _leave(_e):
            btn.configure(fg_color=normal_color, border_color=C("card_border"))

        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    def _bind_action_hover(self, btn, normal_color, hover_color):
        def _enter(_e):
            btn.configure(
                fg_color=hover_color,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                border_width=1
            )

        def _leave(_e):
            btn.configure(
                fg_color=normal_color,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
            )

        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)

    def _bind_card_hover(self, card):
        def _is_descendant_of(widget, ancestor):
            cur = widget
            while cur is not None:
                if cur == ancestor:
                    return True
                cur = cur.master
            return False

        def _set_hover(active):
            card.configure(
                fg_color=C("hover") if active else C("card"),
                border_color=C("accent3") if active else C("card_border")
            )

        def _on_enter(_event):
            _set_hover(True)

        def _on_leave(_event):
            px, py = card.winfo_pointerxy()
            hovered = card.winfo_containing(px, py)
            if hovered is not None and _is_descendant_of(hovered, card):
                return
            _set_hover(False)

        card.bind("<Enter>", _on_enter, add="+")
        card.bind("<Leave>", _on_leave, add="+")
        for child in card.winfo_children():
            child.bind("<Enter>", _on_enter, add="+")
            child.bind("<Leave>", _on_leave, add="+")