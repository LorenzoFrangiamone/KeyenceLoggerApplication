import os
import tkinter as tk
from tkinter import filedialog, messagebox


class CompareApp(tk.Tk):
    def __init__(self, validate_fn, generate_fn):
        super().__init__()

        self.validate_fn = validate_fn
        self.generate_fn = generate_fn

        # ============================================================
        # STILE UI
        # ============================================================
        self.BG = "#f4f6f8"
        self.CARD = "#ffffff"
        self.ACCENT = "#2b579a"
        self.ACCENT2 = "#d9ead3"
        self.TEXT = "#1f1f1f"
        self.MUTED = "#666666"
        self.BORDER = "#d0d7de"

        self.FONT_TITLE = ("Segoe UI", 16, "bold")
        self.FONT_LABEL = ("Segoe UI", 10, "bold")
        self.FONT_NORMAL = ("Segoe UI", 10)
        self.FONT_BUTTON = ("Segoe UI", 10, "bold")
        self.FONT_COMMENT = ("Consolas", 10)

        # ============================================================
        # ROOT
        # ============================================================
        self.title("Compare Export Agent v3")
        self.geometry("860x520")
        self.configure(bg=self.BG)
        self.resizable(False, False)

        self.report_a_var = tk.StringVar()
        self.report_b_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self._build_page1()
        self._build_page2()

        self.page1.pack(fill="both", expand=True)

    # ============================================================
    # PAGE 1
    # ============================================================
    def _build_page1(self):
        self.page1 = tk.Frame(self, bg=self.BG)

        card = tk.Frame(
            self.page1,
            bg=self.CARD,
            bd=1,
            relief="solid",
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(card, bg=self.CARD)
        header.pack(fill="x", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Keyence Report Compare Tool",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Seleziona due cartelle report e la cartella di output.",
            bg=self.CARD,
            fg=self.MUTED,
            font=self.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(card, bg=self.CARD)
        form.pack(fill="x", padx=20, pady=10)

        self._create_row(form, 0, "Report A", self.report_a_var, self.browse_report_a)
        self._create_row(form, 1, "Report B", self.report_b_var, self.browse_report_b)
        self._create_row(form, 2, "Output", self.output_var, self.browse_output)

        form.columnconfigure(1, weight=1)

        self.status_label = tk.Label(
            card,
            text="Seleziona i percorsi richiesti.",
            bg=self.CARD,
            fg=self.MUTED,
            font=self.FONT_NORMAL,
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(4, 10))

        action_frame = tk.Frame(card, bg=self.CARD)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.next_button = tk.Button(
            action_frame,
            text="Next >>",
            command=self.next_page,
            state="disabled",
            width=14,
            height=2,
            bg=self.ACCENT,
            fg="white",
            font=self.FONT_BUTTON,
            relief="flat"
        )
        self.next_button.pack(anchor="e")

        self.report_a_var.trace_add("write", lambda *args: self.validate_current_inputs())
        self.report_b_var.trace_add("write", lambda *args: self.validate_current_inputs())
        self.output_var.trace_add("write", lambda *args: self.validate_current_inputs())

    def _create_row(self, parent, row_idx, label_text, variable, browse_command):
        tk.Label(
            parent,
            text=label_text,
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_LABEL
        ).grid(row=row_idx, column=0, sticky="w", pady=8)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            width=78,
            font=self.FONT_NORMAL,
            relief="solid",
            bd=1
        )
        entry.grid(row=row_idx, column=1, padx=10, pady=8, sticky="ew")

        tk.Button(
            parent,
            text="Sfoglia...",
            command=browse_command,
            width=12,
            bg="#e9eef5",
            font=self.FONT_BUTTON
        ).grid(row=row_idx, column=2, pady=8)

    # ============================================================
    # PAGE 2
    # ============================================================
    def _build_page2(self):
        self.page2 = tk.Frame(self, bg=self.BG)

        card = tk.Frame(
            self.page2,
            bg=self.CARD,
            bd=1,
            relief="solid",
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(card, bg=self.CARD)
        header.pack(fill="x", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Comments",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Inserisci un commento opzionale da scrivere nella sezione finale del changelog.",
            bg=self.CARD,
            fg=self.MUTED,
            font=self.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        self.comment_box = tk.Text(
            card,
            height=18,
            width=96,
            font=self.FONT_COMMENT,
            relief="solid",
            bd=1,
            wrap="word"
        )
        self.comment_box.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        btn_frame = tk.Frame(card, bg=self.CARD)
        btn_frame.pack(fill="x", padx=20, pady=(0, 18))

        tk.Button(
            btn_frame,
            text="<< Back",
            command=self.back_page,
            width=14,
            height=2,
            bg="#e9eef5",
            font=self.FONT_BUTTON,
            relief="flat"
        ).pack(side="left")

        tk.Button(
            btn_frame,
            text="Generate Log",
            command=self.on_generate,
            width=18,
            height=2,
            bg=self.ACCENT2,
            fg=self.TEXT,
            font=self.FONT_BUTTON,
            relief="flat"
        ).pack(side="right")

    # ============================================================
    # CALLBACKS
    # ============================================================
    def browse_report_a(self):
        folder = filedialog.askdirectory(title="Seleziona cartella Report A")
        if folder:
            self.report_a_var.set(folder)

    def browse_report_b(self):
        folder = filedialog.askdirectory(title="Seleziona cartella Report B")
        if folder:
            self.report_b_var.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Seleziona cartella Output")
        if folder:
            self.output_var.set(folder)

    def set_status(self, text, color=None):
        self.status_label.config(text=text, fg=color or self.MUTED)

    def validate_current_inputs(self):
        report_a = self.report_a_var.get().strip()
        report_b = self.report_b_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not report_a or not report_b or not output_dir:
            self.set_status("Seleziona Report A, Report B e Output.", self.MUTED)
            self.next_button.config(state="disabled")
            return False

        ok_a, err_a, warn_a = self.validate_fn(report_a)
        ok_b, err_b, warn_b = self.validate_fn(report_b)

        if not os.path.isdir(output_dir):
            self.set_status("La cartella di output non esiste ancora: verrà creata.", "#996c00")
        else:
            self.set_status("Percorsi selezionati. Premi Next >>", "#2d6a4f")

        if not ok_a or not ok_b:
            msgs = []
            if err_a:
                msgs.append("Report A: " + "; ".join(err_a))
            if err_b:
                msgs.append("Report B: " + "; ".join(err_b))

            self.set_status(" | ".join(msgs), "#b00020")
            self.next_button.config(state="disabled")
            return False

        self.next_button.config(state="normal")
        return True

    def next_page(self):
        if not self.validate_current_inputs():
            return

        report_a = self.report_a_var.get().strip()
        report_b = self.report_b_var.get().strip()

        ok_a, err_a, warn_a = self.validate_fn(report_a)
        ok_b, err_b, warn_b = self.validate_fn(report_b)

        warn_msgs = []
        if warn_a:
            warn_msgs.append("Report A: " + "; ".join(warn_a))
        if warn_b:
            warn_msgs.append("Report B: " + "; ".join(warn_b))

        self.page1.pack_forget()
        self.page2.pack(fill="both", expand=True)

        if warn_msgs:
            messagebox.showwarning("Warning", "\n".join(warn_msgs))

    def back_page(self):
        self.page2.pack_forget()
        self.page1.pack(fill="both", expand=True)

    def on_generate(self):
        report_a = self.report_a_var.get().strip()
        report_b = self.report_b_var.get().strip()
        output_dir = self.output_var.get().strip()
        comment_text = self.comment_box.get("1.0", "end").strip()

        if not self.validate_current_inputs():
            return

        try:
            output_file = self.generate_fn(report_a, report_b, output_dir, comment_text)
            messagebox.showinfo("Completato", f"Change log creato con successo:\n\n{output_file}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione:\n\n{e}")