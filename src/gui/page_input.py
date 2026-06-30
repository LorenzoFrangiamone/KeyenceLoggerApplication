import os
import tkinter as tk
from tkinter import filedialog

from . import theme


class InputPage(tk.Frame):
    def __init__(self, parent, validate_fn, on_next):
        super().__init__(parent, bg=theme.BG)
        self.validate_fn = validate_fn
        self.on_next = on_next

        self.report_a_var = tk.StringVar()
        self.report_b_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self._build()

    def _build(self):
        card = tk.Frame(
            self,
            bg=theme.CARD,
            bd=1,
            relief="solid",
            highlightbackground=theme.BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(card, bg=theme.CARD)
        header.pack(fill="x", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Keyence Report Compare Tool",
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Seleziona due cartelle report e la cartella di output.",
            bg=theme.CARD,
            fg=theme.MUTED,
            font=theme.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(card, bg=theme.CARD)
        form.pack(fill="x", padx=20, pady=10)

        self._create_row(form, 0, "Report A", self.report_a_var, self.browse_report_a)
        self._create_row(form, 1, "Report B", self.report_b_var, self.browse_report_b)
        self._create_row(form, 2, "Output", self.output_var, self.browse_output)

        form.columnconfigure(1, weight=1)

        self.status_label = tk.Label(
            card,
            text="Seleziona i percorsi richiesti.",
            bg=theme.CARD,
            fg=theme.MUTED,
            font=theme.FONT_NORMAL,
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(4, 10))

        action_frame = tk.Frame(card, bg=theme.CARD)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.next_button = tk.Button(
            action_frame,
            text="Next >>",
            command=self._handle_next,
            state="disabled",
            width=14,
            height=2,
            bg=theme.ACCENT,
            fg="white",
            font=theme.FONT_BUTTON,
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
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=row_idx, column=0, sticky="w", pady=8)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            width=78,
            font=theme.FONT_NORMAL,
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
            font=theme.FONT_BUTTON
        ).grid(row=row_idx, column=2, pady=8)

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
        self.status_label.config(text=text, fg=color or theme.MUTED)

    def validate_current_inputs(self):
        report_a = self.report_a_var.get().strip()
        report_b = self.report_b_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not report_a or not report_b or not output_dir:
            self.set_status("Seleziona Report A, Report B e Output.", theme.MUTED)
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

    def get_paths(self):
        return (
            self.report_a_var.get().strip(),
            self.report_b_var.get().strip(),
            self.output_var.get().strip()
        )

    def _handle_next(self):
        if not self.validate_current_inputs():
            return
        self.on_next(*self.get_paths())
