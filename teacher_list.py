# ============================================================
# teacher_list.py — Admin Teacher List Page
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
from models.teacher_model import get_all_teachers, update_teacher, delete_teacher
from theme import ThemeManager

C = ThemeManager.get_color


class TeacherListPage(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(22, 0))

        ctk.CTkLabel(
            top, text="Teacher List",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C("text"),
        ).pack(side="left")

        ctk.CTkButton(
            top, text="↻", width=36, height=32,
            fg_color="transparent", border_width=1,
            border_color=C("card_border"),
            text_color=C("text_dim"),
            hover_color=C("hover"),
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self._refresh,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=C("sep"),
                     ).pack(fill="x", padx=28, pady=12)

        try:
            teachers = get_all_teachers()
        except Exception:
            teachers = []

        if not teachers:
            empty = ctk.CTkFrame(self, fg_color="transparent")
            empty.pack(expand=True)
            ctk.CTkLabel(
                empty, text="◌",
                font=ctk.CTkFont(family="Segoe UI", size=42),
                text_color=C("sep"),
            ).pack(pady=(40, 6))
            ctk.CTkLabel(
                empty, text="No teachers found.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=C("text_dim"),
            ).pack()
            return

        headers = ["ID", "Name", "Department", "Designation", "", ""]
        col_weights = [1, 3, 2, 2, 1, 1]

        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(
            table_frame, fg_color="transparent",
            scrollbar_fg_color=C("bg2"),
        )
        scroll.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(
            scroll,
            fg_color=C("card"),
            corner_radius=8,
            border_width=1,
            border_color=C("card_border")
        )
        hdr.pack(fill="x", pady=(0, 4))
        for i, h in enumerate(headers):
            hdr.grid_columnconfigure(i, weight=col_weights[i], uniform="teacher_cols")
            ctk.CTkLabel(
                hdr, text=h,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=C("text_dim"), anchor="w",
            ).grid(row=0, column=i, padx=(12 if i == 0 else 6), pady=8, sticky="ew")

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
                px, py = row.winfo_pointerxy()
                hovered_widget = row.winfo_containing(px, py)
                if hovered_widget is not None and _is_descendant_of(hovered_widget, row):
                    return
                _set_hover(False)

            row.bind("<Enter>", _on_enter, add="+")
            row.bind("<Leave>", _on_leave, add="+")
            for child in row.winfo_children():
                child.bind("<Enter>", _on_enter, add="+")
                child.bind("<Leave>", _on_leave, add="+")

        for t in teachers:
            bg = row_bg
            rf = ctk.CTkFrame(
                scroll, fg_color=bg, corner_radius=6,
                border_width=1, border_color=C("card_border")
            )
            rf.pack(fill="x", pady=1)

            for i in range(len(headers)):
                rf.grid_columnconfigure(i, weight=col_weights[i], uniform="teacher_cols")

            cells = [
                (str(t["teacher_id"]), "#58a6ff"),
                (t["name"], C("text")),
                (t["department"], C("text_dim")),
                (t["designation"] or "—", C("text_dim")),
            ]
            for i, (val, color) in enumerate(cells):
                ctk.CTkLabel(
                    rf, text=val,
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=(color, color), anchor="w",
                ).grid(row=0, column=i, padx=(12 if i == 0 else 6), pady=7, sticky="ew")

            tid = t["id"]
            ctk.CTkButton(
                rf, text="Edit", width=54, height=26,
                fg_color="transparent",
                border_width=1, border_color=C("accent3"),
                text_color=C("accent3"),
                hover_color=C("hover"),
                font=ctk.CTkFont(family="Segoe UI", size=11), corner_radius=6,
                command=lambda i=tid, n=t["name"], d=t["department"],
                dg=t["designation"]: self._edit(i, n, d, dg),
            ).grid(row=0, column=4, padx=6, pady=5)

            ctk.CTkButton(
                rf, text="Del", width=48, height=26,
                fg_color="transparent",
                border_width=1, border_color=("#f85149", "#f85149"),
                text_color=("#f85149", "#f85149"),
                hover_color=("#2d1117", "#2d1117"),
                font=ctk.CTkFont(family="Segoe UI", size=11), corner_radius=6,
                command=lambda i=tid, r=rf, n=t["name"]: self._delete(i, r, n),
            ).grid(row=0, column=5, padx=4, pady=5)

            _bind_row_hover(rf)

    def _edit(self, tid, name, dept, desig):
        win = ctk.CTkToplevel(self)
        win.title("Edit Teacher")
        win.geometry("400x480")
        win.minsize(400, 480)
        win.grab_set()
        win.configure(fg_color=C("bg"))

        # Main container to hold scrollable content and fixed footer
        main_container = ctk.CTkFrame(win, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Edit Teacher Info",
                     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color=C("text"),
                     ).pack(padx=24, pady=(20, 14), anchor="w")

        entries = {}
        for lbl, key, val in [
            ("Name *",       "name",        name),
            ("Department *", "department",  dept),
            ("Designation",  "designation", desig or ""),
        ]:
            ctk.CTkLabel(scroll, text=lbl,
                         font=ctk.CTkFont(family="Segoe UI", size=13),
                         text_color=C("text_dim"), anchor="w",
                         ).pack(anchor="w", padx=24, pady=(6, 2))
            e = ctk.CTkEntry(scroll, height=38,
                             fg_color=C("bg2"),
                             border_color=C("card_border"),
                             text_color=C("text"))
            e.insert(0, val)
            e.pack(fill="x", padx=24)
            entries[key] = e

        def save():
            n = entries["name"].get().strip()
            d = entries["department"].get().strip()
            dg = entries["designation"].get().strip()
            if not n or not d:
                return
            try:
                update_teacher(tid, n, d, dg)
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
                      corner_radius=8, command=save,
                      ).pack(fill="x", padx=24, pady=16)

    def _delete(self, tid, row_frame, name):
        if messagebox.askyesno(
                "Delete Teacher?",
                f"Are you sure you want to delete '{name}'?\n"
                f"If assigned to any routines, those entries will be updated to NULL."):
            try:
                delete_teacher(tid)
                row_frame.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()