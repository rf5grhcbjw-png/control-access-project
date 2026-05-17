import tkinter as tk
from tkinter import ttk, messagebox
from database import get_conn, BLOCKS
from auth import check_resident, check_visitor, simulate_biometric_scan, log_attempt
from users import add_resident, remove_resident, add_visitor, deactivate_visitor


class ControlAccessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control Access System")
        self.geometry("820x560")
        self.resizable(True, True)
        self.configure(bg="#2c3e50")

        tk.Label(self, text="CONTROL ACCESS SYSTEM",
                 font=("Helvetica", 15, "bold"),
                 bg="#2c3e50", fg="white", pady=10).pack(fill=tk.X)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tab_gate      = ttk.Frame(notebook)
        self.tab_residents = ttk.Frame(notebook)
        self.tab_visitors  = ttk.Frame(notebook)
        self.tab_log       = ttk.Frame(notebook)

        notebook.add(self.tab_gate,      text="   Access Gate   ")
        notebook.add(self.tab_residents, text="   Residents   ")
        notebook.add(self.tab_visitors,  text="   Visitors   ")
        notebook.add(self.tab_log,       text="   Access Log   ")
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self._build_gate_tab()
        self._build_residents_tab()
        self._build_visitors_tab()
        self._build_log_tab()

    def _on_tab_change(self, event):
        tab = event.widget.index("current")
        if tab == 1: self._refresh_residents()
        elif tab == 2: self._refresh_visitors()
        elif tab == 3: self._refresh_log()

    # ── ACCESS GATE ───────────────────────────────────────────────
    def _build_gate_tab(self):
        form = ttk.LabelFrame(self.tab_gate, text="Check In", padding=15)
        form.pack(padx=20, pady=20, fill=tk.X)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.gate_username = ttk.Entry(form, width=28)
        self.gate_username.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.gate_password = ttk.Entry(form, width=28, show="*")
        self.gate_password.grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(form, text="Method:").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.gate_method = tk.StringVar(value="password")
        mf = ttk.Frame(form)
        mf.grid(row=2, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(mf, text="Password",  variable=self.gate_method, value="password").pack(side=tk.LEFT)
        ttk.Radiobutton(mf, text="Biometric", variable=self.gate_method, value="biometric").pack(side=tk.LEFT, padx=12)

        ttk.Button(form, text="Check In", command=self._do_checkin).grid(
            row=3, column=1, sticky=tk.W, padx=10, pady=12)

        self.gate_result = tk.Label(self.tab_gate, text="", font=("Helvetica", 13, "bold"),
                                    pady=14, width=40)
        self.gate_result.pack(pady=10)

    def _do_checkin(self):
        username = self.gate_username.get().strip()
        password = self.gate_password.get().strip()
        if not username:
            messagebox.showwarning("Missing field", "Please enter a username.")
            return
        if self.gate_method.get() == "password":
            granted = check_resident(username, password) or check_visitor(username)
            log_attempt(username, granted, "password")
        else:
            granted = simulate_biometric_scan(username)
            log_attempt(username, granted, "biometric")
        if granted:
            self.gate_result.config(text="✔   ACCESS GRANTED", fg="#155724", bg="#d4edda")
        else:
            self.gate_result.config(text="✘   ACCESS DENIED",  fg="#721c24", bg="#f8d7da")
        self.gate_username.delete(0, tk.END)
        self.gate_password.delete(0, tk.END)

    # ── RESIDENTS ─────────────────────────────────────────────────
    def _build_residents_tab(self):
        form = ttk.LabelFrame(self.tab_residents, text="Add New Resident", padding=10)
        form.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.res_username = ttk.Entry(form, width=18)
        self.res_username.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        self.res_password = ttk.Entry(form, width=18, show="*")
        self.res_password.grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Block:").grid(row=0, column=4, sticky=tk.W, padx=(12, 0))
        self.res_block = ttk.Combobox(form, values=BLOCKS, width=5, state="readonly")
        self.res_block.current(0)
        self.res_block.grid(row=0, column=5, padx=5)

        ttk.Button(form, text="Add Resident", command=self._do_add_resident).grid(
            row=0, column=6, padx=14)

        tf = ttk.Frame(self.tab_residents)
        tf.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        cols = ("block", "username", "reg_code", "registered")
        self.res_tree = ttk.Treeview(tf, columns=cols, show="headings", height=13)
        self.res_tree.heading("block",      text="Block")
        self.res_tree.heading("username",   text="Username")
        self.res_tree.heading("reg_code",   text="Reg Code")
        self.res_tree.heading("registered", text="Registered")
        self.res_tree.column("block",      width=60,  anchor=tk.CENTER)
        self.res_tree.column("username",   width=160)
        self.res_tree.column("reg_code",   width=100, anchor=tk.CENTER)
        self.res_tree.column("registered", width=180)

        sb = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self.res_tree.yview)
        self.res_tree.configure(yscrollcommand=sb.set)
        self.res_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.tab_residents, text="Remove Selected",
                   command=self._do_remove_resident).pack(pady=5)
        self._refresh_residents()

    def _do_add_resident(self):
        u = self.res_username.get().strip()
        p = self.res_password.get().strip()
        b = self.res_block.get()
        if not u or not p:
            messagebox.showwarning("Missing fields", "Please fill in username and password.")
            return
        ok, msg = add_resident(u, p, b)
        if ok:
            messagebox.showinfo("Registered", msg)
            self.res_username.delete(0, tk.END)
            self.res_password.delete(0, tk.END)
            self._refresh_residents()
        else:
            messagebox.showerror("Error", msg)

    def _do_remove_resident(self):
        sel = self.res_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a resident to remove.")
            return
        username = self.res_tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Confirm", f"Remove resident '{username}'?"):
            _, msg = remove_resident(username)
            messagebox.showinfo("Done", msg)
            self._refresh_residents()

    def _refresh_residents(self):
        self.res_tree.delete(*self.res_tree.get_children())
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT block, username, reg_code, created_at FROM residents ORDER BY block, reg_code"
            ).fetchall()
        for row in rows:
            self.res_tree.insert("", tk.END,
                values=(row["block"], row["username"], row["reg_code"], row["created_at"]))

    # ── VISITORS ──────────────────────────────────────────────────
    def _build_visitors_tab(self):
        form = ttk.LabelFrame(self.tab_visitors, text="Add Visitor", padding=10)
        form.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.vis_username = ttk.Entry(form, width=16)
        self.vis_username.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Block:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.vis_block = ttk.Combobox(form, values=BLOCKS, width=5, state="readonly")
        self.vis_block.current(0)
        self.vis_block.grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Host:").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        self.vis_host = ttk.Entry(form, width=16)
        self.vis_host.grid(row=0, column=5, padx=5)

        ttk.Label(form, text="Reason:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.vis_reason = ttk.Entry(form, width=36)
        self.vis_reason.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5)

        ttk.Button(form, text="Add Visitor", command=self._do_add_visitor).grid(
            row=1, column=5, padx=10)

        tf = ttk.Frame(self.tab_visitors)
        tf.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        cols = ("username", "block", "host", "reason", "status")
        self.vis_tree = ttk.Treeview(tf, columns=cols, show="headings", height=13)
        widths = {"username": 140, "block": 60, "host": 130, "reason": 180, "status": 90}
        for col in cols:
            self.vis_tree.heading(col, text=col.capitalize())
            self.vis_tree.column(col, width=widths[col],
                                 anchor=tk.CENTER if col in ("block", "status") else tk.W)

        sb = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self.vis_tree.yview)
        self.vis_tree.configure(yscrollcommand=sb.set)
        self.vis_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.tab_visitors, text="Deactivate Selected",
                   command=self._do_deactivate_visitor).pack(pady=5)
        self._refresh_visitors()

    def _do_add_visitor(self):
        u      = self.vis_username.get().strip()
        b      = self.vis_block.get()
        host   = self.vis_host.get().strip()
        reason = self.vis_reason.get().strip()
        if not u or not host:
            messagebox.showwarning("Missing fields", "Please fill in username and host.")
            return
        ok, msg = add_visitor(u, b, host, reason)
        messagebox.showinfo("Registered", msg)
        for field in (self.vis_username, self.vis_host, self.vis_reason):
            field.delete(0, tk.END)
        self._refresh_visitors()

    def _do_deactivate_visitor(self):
        sel = self.vis_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a visitor to deactivate.")
            return
        username = self.vis_tree.item(sel[0])["values"][0]
        _, msg = deactivate_visitor(username)
        messagebox.showinfo("Done", msg)
        self._refresh_visitors()

    def _refresh_visitors(self):
        self.vis_tree.delete(*self.vis_tree.get_children())
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT username, block, host, reason, temporary_access FROM visitors ORDER BY block, username"
            ).fetchall()
        for row in rows:
            self.vis_tree.insert("", tk.END, values=(
                row["username"], row["block"], row["host"],
                row["reason"] or "-", row["temporary_access"]
            ))

    # ── ACCESS LOG ────────────────────────────────────────────────
    def _build_log_tab(self):
        tf = ttk.Frame(self.tab_log)
        tf.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        cols = ("timestamp", "username", "method", "status")
        self.log_tree = ttk.Treeview(tf, columns=cols, show="headings", height=17)
        widths = {"timestamp": 180, "username": 160, "method": 110, "status": 100}
        for col in cols:
            self.log_tree.heading(col, text=col.capitalize())
            self.log_tree.column(col, width=widths[col],
                                 anchor=tk.CENTER if col == "status" else tk.W)

        self.log_tree.tag_configure("granted", foreground="#155724")
        self.log_tree.tag_configure("denied",  foreground="#721c24")

        sb = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=sb.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.tab_log, text="Refresh", command=self._refresh_log).pack(pady=5)
        self._refresh_log()

    def _refresh_log(self):
        self.log_tree.delete(*self.log_tree.get_children())
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT timestamp, username, method, granted FROM access_log ORDER BY timestamp DESC"
            ).fetchall()
        for row in rows:
            status = "GRANTED" if row["granted"] else "DENIED"
            tag    = "granted" if row["granted"] else "denied"
            self.log_tree.insert("", tk.END,
                values=(row["timestamp"], row["username"], row["method"], status), tags=(tag,))


if __name__ == "__main__":
    app = ControlAccessApp()
    app.mainloop()
