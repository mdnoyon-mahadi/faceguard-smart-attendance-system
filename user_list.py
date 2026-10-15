# ============================================================
# user_list.py — Admin User List Page
# ============================================================
# UPDATE:
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# Comment translated to English.
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
from models.user_model import get_all_users, update_user, delete_user
from theme import ThemeManager

C = ThemeManager.get_color


class UserListPage(ctk.CTkFrame):

    def __init__(self, parent, on_edit=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_edit = on_edit
        self._build_ui()

    def _build_ui(self):
        # ── Top bar: title ────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Student List",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).pack(side="left")

        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *a: self._apply_filters())
        search = ctk.CTkEntry(
            top, textvariable=self.search_var,
            placeholder_text="🔍  Search by name or roll...",
            width=220, height=32,
            fg_color=C("bg2"),
            border_color=C("card_border"),
            text_color=C("text"),
            placeholder_text_color=C("text_dim"),
        )
        search.pack(side="right")

        ctk.CTkButton(
            top, text="↻", width=36, height=32,
            fg_color="transparent", border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self._refresh,
        ).pack(side="right", padx=8)

        # ── Filter bar: Department / Semester / Shift ─────────
        filter_bar = ctk.CTkFrame(
            self,
            fg_color=C("card"),
            corner_radius=10,
            border_width=1,
            border_color=C("card_border"),
        )
        filter_bar.pack(fill="x", padx=28, pady=(12, 0))

        inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            inner, text="Filter:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=C("text_dim"),
        ).pack(side="left", padx=(0, 10))

        # Department filter
        self.dept_var = ctk.StringVar(value="All Departments")
        ctk.CTkOptionMenu(
            inner,
            variable=self.dept_var,
            values=["All Departments", "CST", "ET",
                    "CT", "MT", "PT", "EMT", "ENT"],
            fg_color=C("bg2"),
            button_color=C("card_border"),
            button_hover_color=C("hover"),
            text_color=C("text"),
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            width=160, height=30,
            command=lambda _: self._apply_filters(),
        ).pack(side="left", padx=(0, 8))

        # Semester filter
        self.sem_var = ctk.StringVar(value="All Semesters")
        ctk.CTkOptionMenu(
            inner,
            variable=self.sem_var,
            values=["All Semesters", "1st", "2nd", "3rd", "4th",
                    "5th", "6th", "7th", "8th"],
            fg_color=C("bg2"),
            button_color=C("card_border"),
            button_hover_color=C("hover"),
            text_color=C("text"),
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            width=150, height=30,
            command=lambda _: self._apply_filters(),
        ).pack(side="left", padx=(0, 8))

        # Shift filter
        self.shift_var = ctk.StringVar(value="All Shifts")
        ctk.CTkOptionMenu(
            inner,
            variable=self.shift_var,
            values=["All Shifts", "day", "morning"],
            fg_color=C("bg2"),
            button_color=C("card_border"),
            button_hover_color=C("hover"),
            text_color=C("text"),
            dropdown_fg_color=C("card"),
            dropdown_hover_color=C("hover"),
            width=130, height=30,
            command=lambda _: self._apply_filters(),
        ).pack(side="left", padx=(0, 12))

        # Clear filters button
        ctk.CTkButton(
            inner, text="✕ Clear",
            width=70, height=28,
            fg_color="transparent",
            border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._clear_filters,
        ).pack(side="left")

        # Result count label
        self.count_lbl = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C("text_dim"),
        )
        self.count_lbl.pack(side="right")

        # ── Divider ───────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=C("sep"),
                     ).pack(fill="x", padx=28, pady=12)

        # ── Load data ─────────────────────────────────────────
        try:
            self._all_users = get_all_users()
        except Exception:
            self._all_users = []

        # Table container
        self.table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        self._render_table(self._all_users)
        self._update_count(len(self._all_users))

    # ── Filter logic ──────────────────────────────────────────

    def _apply_filters(self):
        q = self.search_var.get().lower().strip()
        dept = self.dept_var.get()
        sem = self.sem_var.get()
        shift = self.shift_var.get()

        result = self._all_users

        if q:
            result = [u for u in result
                      if q in u["name"].lower() or q in u["roll"].lower()]

        if dept != "All Departments":
            result = [u for u in result if u.get("department") == dept]

        if sem != "All Semesters":
            result = [u for u in result if u.get("semester") == sem]

        if shift != "All Shifts":
            result = [u for u in result if u.get("shift") == shift]

        self._render_table(result)
        self._update_count(len(result))

    def _clear_filters(self):
        self.dept_var.set("All Departments")
        self.sem_var.set("All Semesters")
        self.shift_var.set("All Shifts")
        self.search_var.set("")
        self._render_table(self._all_users)
        self._update_count(len(self._all_users))

    def _update_count(self, count):
        total = len(self._all_users)
        if count == total:
            self.count_lbl.configure(text=f"{total} students")
        else:
            self.count_lbl.configure(
                text=f"{count} of {total} students",
                text_color=("#e3b341", "#e3b341"),
            )
        if count == total:
            self.count_lbl.configure(text_color=C("text_dim"))

    # ── Table render ──────────────────────────────────────────

    def _render_table(self, users):
        for w in self.table_frame.winfo_children():
            w.destroy()

        if not users:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(expand=True)
            ctk.CTkLabel(
                empty, text="◌",
                font=ctk.CTkFont(family="Segoe UI", size=42),
                text_color=C("sep"),
            ).pack(pady=(40, 6))
            ctk.CTkLabel(
                empty,
                text="No students found.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=C("text_dim"),
            ).pack()
            return

        headers = ["Roll", "Name", "Department",
                   "Semester", "Shift", "Status", "", ""]
        col_widths = [100,     150,    130,
                      80,         80,      90,      60, 54]

        scroll = ctk.CTkScrollableFrame(
            self.table_frame, fg_color="transparent",
            scrollbar_fg_color=C("bg2"),
        )
        scroll.pack(fill="both", expand=True)

        # Header row
        hdr = ctk.CTkFrame(scroll, fg_color=C("card"), corner_radius=8, border_width=1, border_color=C("card_border"))
        hdr.pack(fill="x", pady=(0, 4))
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            ctk.CTkLabel(
                hdr, text=h, width=w,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=C("text_dim"), anchor="w",
            ).grid(row=0, column=i, padx=(12 if i == 0 else 6), pady=8, sticky="w")

        # Data rows
        row_bg = C("card")
        row_hover = C("hover")

        def _is_descendant_of(widget, ancestor):
            cur = widget
            while cur is not None:
                if cur == ancestor:
                    return True
                cur = cur.master
            return False

        def _bind_row_hover(row):
            def _set_hover(active):
                row.configure(
                    fg_color=row_hover if active else row_bg,
                    border_color=C("accent3") if active else C("card_border")
                )

            def _on_enter(_event):
                _set_hover(True)

            def _on_leave(_event):
                # Ignore leave events fired while pointer is still inside this row
                px, py = row.winfo_pointerxy()
                hovered_widget = row.winfo_containing(px, py)
                if hovered_widget is not None and _is_descendant_of(hovered_widget, row):
                    return
                _set_hover(False)

            row.bind("<Enter>", _on_enter, add="+")
            row.bind("<Leave>", _on_leave, add="+")

            # Bind all direct children so hover works over every cell/control
            for child in row.winfo_children():
                child.bind("<Enter>", _on_enter, add="+")
                child.bind("<Leave>", _on_leave, add="+")

        for u in users:
            bg = row_bg
            rf = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=6, border_width=1, border_color=C("card_border"))
            rf.pack(fill="x", pady=1)

            sc = "#3fb950" if u["status"] == "approved" else \
                 "#f85149" if u["status"] == "rejected" else "#e3b341"

            shift_val = u.get("shift") or "—"
            shift_icon = "☀" if shift_val == "day" else (
                "🌅" if shift_val == "morning" else "")
            shift_display = f"{shift_icon} {shift_val.title()}" if shift_icon else shift_val

            cells = [
                (u["roll"],            col_widths[0], C("text_dim")),
                (u["name"],            col_widths[1], C("text")),
                (u["department"],      col_widths[2], C("text_dim")),
                (u["semester"],        col_widths[3], C("text_dim")),
                (shift_display,        col_widths[4], "#58a6ff"),
                (u["status"].upper(),  col_widths[5], sc),
            ]
            for i, (val, w, color) in enumerate(cells):
                ctk.CTkLabel(
                    rf, text=val, width=w,
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=(color, color), anchor="w",
                ).grid(row=0, column=i, padx=(12 if i == 0 else 6), pady=7, sticky="w")

            uid = u["id"]

            # Edit button
            ctk.CTkButton(
                rf, text="Edit", width=54, height=26,
                fg_color="transparent",
                border_width=1, border_color=C("accent3"),
                text_color=C("accent3"),
                hover_color=C("hover"),
                font=ctk.CTkFont(family="Segoe UI", size=11), corner_radius=6,
                command=lambda i=uid, n=u["name"], d=u["department"],
                s=u["semester"], sh=u.get("shift", ""), p=u.get("phone", ""): self._edit(i, n, d, s, sh, p),
            ).grid(row=0, column=6, padx=4, pady=5)

            # Delete button
            ctk.CTkButton(
                rf, text="Del", width=48, height=26,
                fg_color="transparent",
                border_width=1, border_color=("#f85149", "#f85149"),
                text_color=("#f85149", "#f85149"),
                hover_color=("#2d1117", "#2d1117"),
                font=ctk.CTkFont(family="Segoe UI", size=11), corner_radius=6,
                command=lambda i=uid, r=rf, n=u["name"]: self._delete(i, r, n),
            ).grid(row=0, column=7, padx=4, pady=5)

            _bind_row_hover(rf)

    # ── Edit modal ────────────────────────────────────────────

    def _edit(self, uid, name, dept, sem, shift, phone):
        win = ctk.CTkToplevel(self)
        win.title("Edit Student")
        win.geometry("420x560")
        win.minsize(420, 560)
        win.grab_set()
        win.configure(fg_color=("#0d1117", "#0d1117"))
        win.configure(fg_color=C("bg"))

        # Main container to hold scrollable content and fixed footer
        main_container = ctk.CTkFrame(win, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Edit Student Info",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=C("text"),
        ).pack(padx=24, pady=(20, 14), anchor="w")

        fields = [("Name *", "name", name), ("Phone", "phone", phone or "")]
        entries = {}
        for lbl, key, val in fields:
            ctk.CTkLabel(scroll, text=lbl,
                         font=ctk.CTkFont(family="Segoe UI", size=13),
                         text_color=C("text_dim"),
                         anchor="w").pack(anchor="w", padx=24, pady=(6, 2))
            e = ctk.CTkEntry(scroll, height=38,
                             fg_color=C("bg2"),
                             border_color=C("card_border"),
                             text_color=C("text"))
            e.insert(0, val)
            e.pack(fill="x", padx=24)
            entries[key] = e

        dept_var = ctk.StringVar(value=dept)
        ctk.CTkLabel(scroll, text="Department", font=ctk.CTkFont(family="Segoe UI", size=13),
                     text_color=C("text_dim"),
                     anchor="w").pack(anchor="w", padx=24, pady=(8, 2))
        ctk.CTkOptionMenu(scroll, variable=dept_var,
                          values=["CST", "ET", "CT", "MT", "PT", "EMT", "ENT"],
                          fg_color=C("bg2"),
                          button_color=C("card_border"),
                          text_color=C("text"),
                          dropdown_fg_color=C("card"),
                          height=38).pack(fill="x", padx=24)

        sem_var = ctk.StringVar(value=sem)
        ctk.CTkLabel(scroll, text="Semester", font=ctk.CTkFont(family="Segoe UI", size=13),
                     text_color=C("text_dim"),
                     anchor="w").pack(anchor="w", padx=24, pady=(8, 2))
        ctk.CTkOptionMenu(scroll, variable=sem_var,
                          values=["1st", "2nd", "3rd", "4th",
                                  "5th", "6th", "7th", "8th"],
                          fg_color=C("bg2"),
                          button_color=C("card_border"),
                          text_color=C("text"),
                          dropdown_fg_color=C("card"),
                          height=38).pack(fill="x", padx=24)

        shift_var = ctk.StringVar(value=shift or "day")
        ctk.CTkLabel(scroll, text="Shift", font=ctk.CTkFont(family="Segoe UI", size=13),
                     text_color=C("text_dim"),
                     anchor="w").pack(anchor="w", padx=24, pady=(8, 2))
        ctk.CTkOptionMenu(scroll, variable=shift_var,
                          values=["day", "morning"],
                          fg_color=C("bg2"),
                          button_color=C("card_border"),
                          text_color=C("text"),
                          dropdown_fg_color=C("card"),
                          height=38).pack(fill="x", padx=24)

        def save():
            n = entries["name"].get().strip()
            p = entries["phone"].get().strip()
            if not n:
                return
            try:
                update_user(uid, n, dept_var.get(), sem_var.get(),
                            shift_var.get(), p)
                win.destroy()
                self._refresh()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        # Fixed Footer Action Bar
        footer = ctk.CTkFrame(main_container, fg_color=C("bg"), border_width=1, border_color=C("card_border"), corner_radius=0)
        footer.pack(fill="x", side="bottom")

        ctk.CTkButton(footer, text="💾  Save Changes", height=42,
                      fg_color=C("accent3"),
                      hover_color=C("accent"),
                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                      corner_radius=8,
                      command=save,
                      ).pack(fill="x", padx=24, pady=16)

    # ── Delete ────────────────────────────────────────────────

    def _delete(self, uid, row_frame, name):
        if messagebox.askyesno(
            "Delete Student?",
            f"Are you sure you want to delete '{name}'?\nAll attendance records for this student will be permanently removed."
        ):
            try:
                delete_user(uid)
                row_frame.destroy()
                # count update
                self._all_users = [
                    u for u in self._all_users if u["id"] != uid]
                self._update_count(len(self._all_users))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Refresh ───────────────────────────────────────────────

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()