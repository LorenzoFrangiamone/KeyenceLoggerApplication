import threading
import tkinter as tk
from tkinter import messagebox

from src.AICorrector import AICorrection
from . import theme


class AIPanel(tk.Frame):
    """AI correction widget: 'Correct' runs AICorrection in a background
    thread (it's a slow local LLM call) and marshals the result back to
    the Tk mainloop via self.after(); 'Accept' hands the corrected text
    up to the caller via on_accept_text.
    """

    def __init__(self, parent, get_comment, get_preview_markdown, on_accept_text):
        super().__init__(parent, bg=theme.CARD)
        self.get_comment = get_comment
        self.get_preview_markdown = get_preview_markdown
        self.on_accept_text = on_accept_text
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=theme.CARD)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="AI Correct & Suggest",
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w")

        btns = tk.Frame(header, bg=theme.CARD)
        btns.grid(row=0, column=1, sticky="e")

        self.correct_btn = tk.Button(
            btns,
            text="Correct",
            command=self.on_correct,
            width=10,
            bg="#e9eef5",
            font=theme.FONT_BUTTON,
            relief="flat"
        )
        self.correct_btn.pack(side="left", padx=(0, 6))

        self.accept_btn = tk.Button(
            btns,
            text="Accept Correction",
            command=self.on_accept,
            width=16,
            bg=theme.ACCENT2,
            fg=theme.TEXT,
            font=theme.FONT_BUTTON,
            relief="flat"
        )
        self.accept_btn.pack(side="left")

        notes_container = tk.Frame(self)
        notes_container.grid(row=1, column=0, sticky="nsew")

        notes_scroll = tk.Scrollbar(notes_container)
        notes_scroll.pack(side="right", fill="y")

        self.notes_box = tk.Text(
            notes_container,
            font=theme.FONT_COMMENT,
            relief="solid",
            bd=1,
            wrap="word",
            yscrollcommand=notes_scroll.set
        )
        self.notes_box.pack(side="left", fill="both", expand=True)

        notes_scroll.config(command=self.notes_box.yview)

    def on_correct(self):
        human = self.get_comment()
        auto = self.get_preview_markdown()

        if not human and not auto:
            messagebox.showwarning(
                "Missing content",
                "Non ci sono contenuti da inviare alla correzione AI."
            )
            return

        self.correct_btn.config(state="disabled")
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", "thinking ...")
        self.notes_box.update_idletasks()

        def worker():
            try:
                result = AICorrection(auto, human)
            except Exception as e:
                self.after(0, lambda: self._on_error(e))
                return

            result = "" if result is None else str(result)
            self.after(0, lambda: self._on_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, result):
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", result)
        self.correct_btn.config(state="normal")

    def _on_error(self, error):
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", f"Errore durante la correzione AI:\n{error}")
        self.correct_btn.config(state="normal")

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
