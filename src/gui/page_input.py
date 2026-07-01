import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from . import theme


class InputPage(ctk.CTkFrame):
    def __init__(self, parent, validate_fn, load_paths_fn, save_paths_fn, on_next):
        super().__init__(parent, fg_color=theme.BG, corner_radius=0)
        self.validate_fn = validate_fn
        self.load_paths_fn = load_paths_fn
        self.save_paths_fn = save_paths_fn
        self.on_next = on_next

        self.report_a_var = tk.StringVar()
        self.report_b_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self._build()
        self._load_saved_paths()

    def _build(self):
        card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.BORDER
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            header,
            text="Keyence Report Compare Tool",
            text_color=theme.TEXT,
            font=theme.FONT_TITLE
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Seleziona due cartelle report e la cartella di output.",
            text_color=theme.MUTED,
            font=theme.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)

        self._create_row(form, 0, "Report A", self.report_a_var, self.browse_report_a)
        self._create_row(form, 1, "Report B", self.report_b_var, self.browse_report_b)
        self._create_row(form, 2, "Output", self.output_var, self.browse_output)

        form.columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            card,
            text="Seleziona i percorsi richiesti.",
            text_color=theme.MUTED,
            font=theme.FONT_NORMAL,
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(4, 10))

        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.next_button = ctk.CTkButton(
            action_frame,
            text="Next >>",
            command=self._handle_next,
            state="disabled",
            width=170,
            height=58,
            fg_color=theme.ACCENT,
            text_color="white",
            text_color_disabled=theme.MUTED,
            hover_color=theme.ACCENT_ACTIVE,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
        )
        self.next_button.pack(anchor="e")

        self.report_a_var.trace_add("write", lambda *args: self.validate_current_inputs())
        self.report_b_var.trace_add("write", lambda *args: self.validate_current_inputs())
        self.output_var.trace_add("write", lambda *args: self.validate_current_inputs())

    def _create_row(self, parent, row_idx, label_text, variable, browse_command):
        ctk.CTkLabel(
            parent,
            text=label_text,
            text_color=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=row_idx, column=0, sticky="w", pady=8)

        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            width=320,
            height=46,
            font=theme.FONT_MONO,
            fg_color=theme.FIELD,
            text_color=theme.TEXT,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            corner_radius=theme.RADIUS_CONTROL
        )
        entry.grid(row=row_idx, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkButton(
            parent,
            text="Sfoglia...",
            command=browse_command,
            width=130,
            height=46,
            fg_color=theme.ACCENT2,
            text_color=theme.TEXT,
            hover_color=theme.ACCENT2_ACTIVE,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
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
        self.status_label.configure(text=text, text_color=color or theme.MUTED)

    def validate_current_inputs(self):
        report_a = self.report_a_var.get().strip()
        report_b = self.report_b_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not report_a or not report_b or not output_dir:
            self.set_status("Seleziona Report A, Report B e Output.", theme.MUTED)
            self.next_button.configure(state="disabled")
            return False

        ok_a, err_a, warn_a = self.validate_fn(report_a)
        ok_b, err_b, warn_b = self.validate_fn(report_b)

        if not os.path.isdir(output_dir):
            self.set_status("La cartella di output non esiste ancora: verrà creata.", theme.WARNING)
        else:
            self.set_status("Percorsi selezionati. Premi Next >>", theme.SUCCESS)

        if not ok_a or not ok_b:
            msgs = []
            if err_a:
                msgs.append("Report A: " + "; ".join(err_a))
            if err_b:
                msgs.append("Report B: " + "; ".join(err_b))

            self.set_status(" | ".join(msgs), theme.DANGER)
            self.next_button.configure(state="disabled")
            return False

        self.next_button.configure(state="normal")
        return True

    def get_paths(self):
        return (
            self.report_a_var.get().strip(),
            self.report_b_var.get().strip(),
            self.output_var.get().strip()
        )

    def _load_saved_paths(self):
        saved = self.load_paths_fn()
        self.report_a_var.set(saved.get("report_a", ""))
        self.report_b_var.set(saved.get("report_b", ""))
        self.output_var.set(saved.get("output_dir", ""))

    def _handle_next(self):
        if not self.validate_current_inputs():
            return
        paths = self.get_paths()
        self.save_paths_fn(*paths)
        self.on_next(*paths)
