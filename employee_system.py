import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class EmployeeManagementSystem:
    def __init__(self, root: tk.Tk, db_path: str = "employees.db") -> None:
        self.root = root
        self.root.title("Employee Management System")
        self.root.geometry("920x520")
        self.root.minsize(780, 460)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_db()

        self.emp_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.dept_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self._build_ui()
        self.refresh_table()

    def _init_db(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def _build_ui(self) -> None:
        header = tk.Label(
            self.root,
            text="Employee Management System",
            font=("Segoe UI", 16, "bold"),
            pady=10,
        )
        header.pack(fill=tk.X)

        main_frame = tk.Frame(self.root, padx=12, pady=6)
        main_frame.pack(fill=tk.BOTH, expand=True)

        form_frame = tk.LabelFrame(main_frame, text="Employee Details", padx=12, pady=10)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        fields = [
            ("Employee ID", self.emp_id_var, True),
            ("Full Name", self.name_var, False),
            ("Role / Title", self.role_var, False),
            ("Department", self.dept_var, False),
            ("Salary (INR)", self.salary_var, False),
        ]

        for row_idx, (label_text, var, readonly) in enumerate(fields):
            tk.Label(form_frame, text=label_text, anchor="w", font=("Segoe UI", 10)).grid(
                row=row_idx, column=0, sticky="w", pady=5
            )
            state = "readonly" if readonly else "normal"
            entry = tk.Entry(
                form_frame, textvariable=var, width=24, state=state, font=("Segoe UI", 10)
            )
            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=(8, 0))

        btn_frame = tk.Frame(form_frame, pady=12)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, sticky="ew")

        tk.Button(btn_frame, text="Add", width=10, command=self.add_employee).grid(
            row=0, column=0, padx=3, pady=3
        )
        tk.Button(btn_frame, text="Update", width=10, command=self.update_employee).grid(
            row=0, column=1, padx=3, pady=3
        )
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_employee).grid(
            row=1, column=0, padx=3, pady=3
        )
        tk.Button(btn_frame, text="Clear", width=10, command=self.clear_form).grid(
            row=1, column=1, padx=3, pady=3
        )

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        search_frame = tk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(search_frame, text="Search:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        search_entry.bind("<Return>", lambda _e: self.search_employees())

        tk.Button(search_frame, text="Find", width=8, command=self.search_employees).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        tk.Button(search_frame, text="Show All", width=8, command=self.reset_search).pack(
            side=tk.LEFT
        )

        table_frame = tk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("emp_id", "name", "role", "department", "salary")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )

        headings = {
            "emp_id": ("ID", 65, tk.CENTER),
            "name": ("Name", 170, tk.W),
            "role": ("Role", 150, tk.W),
            "department": ("Department", 140, tk.W),
            "salary": ("Salary", 110, tk.E),
        }

        for col, (text, width, anchor) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def _validate_inputs(self) -> tuple[str, str, str, float] | None:
        name = self.name_var.get().strip()
        role = self.role_var.get().strip()
        dept = self.dept_var.get().strip()
        salary_raw = self.salary_var.get().strip()

        if not name or not role or not dept or not salary_raw:
            messagebox.showwarning(
                "Missing Data", "Please fill out Name, Role, Department, and Salary."
            )
            return None

        try:
            salary = float(salary_raw)
            if salary < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Salary", "Salary must be a non-negative number.")
            return None

        return name, role, dept, salary

    def add_employee(self) -> None:
        validated = self._validate_inputs()
        if not validated:
            return
        name, role, dept, salary = validated
        self.cursor.execute(
            "INSERT INTO employees (name, role, department, salary) VALUES (?, ?, ?, ?)",
            (name, role, dept, salary),
        )
        self.conn.commit()
        self.clear_form()
        self.refresh_table()
        messagebox.showinfo("Success", "Employee added.")

    def update_employee(self) -> None:
        emp_id = self.emp_id_var.get().strip()
        if not emp_id:
            messagebox.showwarning("No Selection", "Select an employee row first to update.")
            return

        validated = self._validate_inputs()
        if not validated:
            return
        name, role, dept, salary = validated

        self.cursor.execute(
            """
            UPDATE employees
            SET name = ?, role = ?, department = ?, salary = ?
            WHERE emp_id = ?
            """,
            (name, role, dept, salary, int(emp_id)),
        )
        self.conn.commit()
        self.clear_form()
        self.refresh_table()
        messagebox.showinfo("Success", "Employee updated.")

    def delete_employee(self) -> None:
        emp_id = self.emp_id_var.get().strip()
        if not emp_id:
            messagebox.showwarning("No Selection", "Select an employee row first to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete employee ID {emp_id}?")
        if not confirm:
            return

        self.cursor.execute("DELETE FROM employees WHERE emp_id = ?", (int(emp_id),))
        self.conn.commit()
        self.clear_form()
        self.refresh_table()
        messagebox.showinfo("Deleted", "Employee record deleted.")

    def search_employees(self) -> None:
        query = f"%{self.search_var.get().strip()}%"
        rows = self.cursor.execute(
            """
            SELECT emp_id, name, role, department, salary
            FROM employees
            WHERE CAST(emp_id AS TEXT) LIKE ?
               OR name LIKE ?
               OR role LIKE ?
               OR department LIKE ?
            ORDER BY emp_id DESC
            """,
            (query, query, query, query),
        ).fetchall()
        self._populate_tree(rows)

    def reset_search(self) -> None:
        self.search_var.set("")
        self.refresh_table()

    def refresh_table(self) -> None:
        rows = self.cursor.execute(
            "SELECT emp_id, name, role, department, salary FROM employees ORDER BY emp_id DESC"
        ).fetchall()
        self._populate_tree(rows)

    def _populate_tree(self, rows: list[tuple]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp_id, name, role, dept, salary in rows:
            self.tree.insert("", tk.END, values=(emp_id, name, role, dept, f"{salary:,.2f}"))

    def _on_row_select(self, _event: object) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        self.emp_id_var.set(values[0])
        self.name_var.set(values[1])
        self.role_var.set(values[2])
        self.dept_var.set(values[3])
        self.salary_var.set(str(values[4]).replace(",", ""))

    def clear_form(self) -> None:
        self.emp_id_var.set("")
        self.name_var.set("")
        self.role_var.set("")
        self.dept_var.set("")
        self.salary_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def close(self) -> None:
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    app_root = tk.Tk()
    app = EmployeeManagementSystem(app_root)
    app_root.protocol("WM_DELETE_WINDOW", app.close)
    app_root.mainloop()