import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from src.AICorrector import AICorrection, MODELS_DIR, load_model
from src.modelSelector import detect_hardware, list_available_models, recommend_model
from . import theme
from .scrollbar import AutoHideScrollbar


class AIPanel(ctk.CTkFrame):
    """AI correction widget: 'Correct' runs AICorrection in a background
    thread (it's a slow local LLM call) and marshals the result back to
    the Tk mainloop via self.after(); 'Accept' hands the corrected text
    up to the caller via on_accept_text. The model dropdown lets the user
    override the auto-recommended GGUF model; (re)loading also runs in a
    background thread since it can take a while for multi-GB models.
    """

    def __init__(self, parent, get_comment, get_preview_markdown, on_accept_text):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.BORDER
        )
        self.get_comment = get_comment
        self.get_preview_markdown = get_preview_markdown
        self.on_accept_text = on_accept_text
        self._model_paths = {}
        self._build()
        self._init_model_selector()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 10))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="AI Correct & Suggest",
            text_color=theme.ACCENT_SOFT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w")

        self.model_var = tk.StringVar()
        self.model_combo = ctk.CTkComboBox(
            header_row,
            variable=self.model_var,
            state="disabled",
            width=260,
            height=40,
            fg_color=theme.FIELD,
            text_color=theme.TEXT,
            border_color=theme.BORDER_STRONG,
            button_color=theme.FIELD,
            button_hover_color=theme.BORDER_STRONG,
            dropdown_fg_color=theme.FIELD,
            dropdown_hover_color=theme.ACCENT,
            dropdown_text_color=theme.TEXT,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL,
            command=self.on_model_change
        )
        self.model_combo.grid(row=0, column=1, sticky="e")

        controls_row = ctk.CTkFrame(self, fg_color="transparent")
        controls_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        controls_row.grid_columnconfigure(0, weight=1, uniform="btns")
        controls_row.grid_columnconfigure(1, weight=1, uniform="btns")

        self.correct_btn = ctk.CTkButton(
            controls_row,
            text="✦ Correct",
            command=self.on_correct,
            height=40,
            fg_color=theme.ACCENT,
            text_color="white",
            text_color_disabled=theme.MUTED,
            hover_color=theme.ACCENT_ACTIVE,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL,
            state="disabled"
        )
        self.correct_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.accept_btn = ctk.CTkButton(
            controls_row,
            text="Accept Correction",
            command=self.on_accept,
            height=40,
            fg_color=theme.ACCENT2,
            text_color=theme.TEXT,
            hover_color=theme.ACCENT2_ACTIVE,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
        )
        self.accept_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        notes_container = ctk.CTkFrame(self, fg_color="transparent")
        notes_container.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        notes_scroll = AutoHideScrollbar(
            notes_container,
            orientation="vertical",
            fg_color="transparent",
            button_color=theme.BORDER_STRONG,
            button_hover_color=theme.MUTED,
            corner_radius=theme.RADIUS_CONTROL,
            width=12
        )
        notes_scroll.pack(side="right", fill="y")

        self.notes_box = ctk.CTkTextbox(
            notes_container,
            font=theme.FONT_COMMENT,
            fg_color=theme.FIELD,
            text_color=theme.TEXT,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            corner_radius=theme.RADIUS_CONTROL,
            wrap="word",
            activate_scrollbars=False,
            yscrollcommand=notes_scroll.set
        )
        self.notes_box.pack(side="left", fill="both", expand=True)

        notes_scroll.configure(command=self.notes_box.yview)

    # ============================================================
    # SELEZIONE MODELLO
    # ============================================================
    def _init_model_selector(self):
        try:
            models = list_available_models(str(MODELS_DIR))
        except Exception as e:
            messagebox.showerror("Errore modelli AI", f"Impossibile leggere la cartella modelli:\n{e}")
            return

        if not models:
            self.notes_box.configure(state="normal")
            self.notes_box.delete("1.0", "end")
            self.notes_box.insert(
                "1.0",
                "Nessun modello AI (.gguf) trovato nella cartella 'models'.\n"
                "Copia un modello in 'models' e riavvia l'app per usare la correzione AI."
            )
            return

        self._model_paths = {m["display_name"]: m["path"] for m in models}
        display_names = list(self._model_paths.keys())
        self.model_combo.configure(values=display_names)

        recommended = recommend_model(models, detect_hardware())
        default_name = recommended["display_name"] if recommended else display_names[0]
        self.model_var.set(default_name)

        self._load_model_in_background(self._model_paths[default_name])

    def on_model_change(self, choice=None):
        display_name = choice if choice is not None else self.model_var.get()
        path = self._model_paths.get(display_name)
        if path:
            self._load_model_in_background(path)

    def _load_model_in_background(self, model_path):
        self.model_combo.configure(state="disabled")
        self.correct_btn.configure(state="disabled")

        def worker():
            try:
                load_model(model_path)
            except Exception as e:
                error_message = str(e)
                self.after(0, lambda: self._on_model_load_error(error_message))
                return
            self.after(0, self._on_model_load_success)

        threading.Thread(target=worker, daemon=True).start()

    def _on_model_load_success(self):
        self.model_combo.configure(state="readonly")
        self.correct_btn.configure(state="normal")

    def _on_model_load_error(self, error):
        self.model_combo.configure(state="readonly")
        messagebox.showerror("Errore caricamento modello", str(error))

    def on_correct(self):
        human = self.get_comment()
        auto = self.get_preview_markdown()

        if not human and not auto:
            messagebox.showwarning(
                "Missing content",
                "Non ci sono contenuti da inviare alla correzione AI."
            )
            return

        self.correct_btn.configure(state="disabled")
        self.model_combo.configure(state="disabled")
        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", "thinking ...")
        self.notes_box.update_idletasks()

        def worker():
            try:
                result = AICorrection(auto, human)
            except Exception as e:
                error_message = str(e)
                self.after(0, lambda: self._on_error(error_message))
                return

            result = "" if result is None else str(result)
            self.after(0, lambda: self._on_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, result):
        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", result)
        self.correct_btn.configure(state="normal")
        self.model_combo.configure(state="readonly")

    def _on_error(self, error):
        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", f"Errore durante la correzione AI:\n{error}")
        self.correct_btn.configure(state="normal")
        self.model_combo.configure(state="readonly")

    def on_accept(self):
        """Copia nel callback solo la parte del testo AI che precede il
        marker '//Suggerimento:' (marker escluso). Se il marker non
        esiste, copia tutto il contenuto.
        """
        ai_text = self.notes_box.get("1.0", "end").strip()

        if not ai_text or ai_text.lower() == "thinking ...":
            return

        lines = ai_text.splitlines()
        if len(lines) < 2:
            return

        text_from_second_line = "\n".join(lines[1:]).strip()
        if not text_from_second_line:
            return

        marker = "//Suggerimento:"
        accepted_text = text_from_second_line.split(marker, 1)[0].rstrip()

        if not accepted_text:
            return

        self.on_accept_text(accepted_text)
