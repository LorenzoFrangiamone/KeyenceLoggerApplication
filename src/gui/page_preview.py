import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterweb import HtmlFrame

from src.backEnd import append_change_record
from . import theme
from .ai_panel import AIPanel
from .html_render import render_markdown, wrap_html_body

DEFAULT_PREVIEW_MD = """
# Preview Differences

Nessun contenuto disponibile.

- Carica o genera una preview
- Controlla le modifiche
- Inserisci il commento finale
"""


class PreviewPage(tk.Frame):
    def __init__(self, parent, preview_fn, generate_fn, get_version, on_back):
        super().__init__(parent, bg=theme.BG)
        self.preview_fn = preview_fn
        self.generate_fn = generate_fn
        self.get_version = get_version
        self.on_back = on_back

        self.report_a = ""
        self.report_b = ""
        self.output_dir = ""
        self.preview_markdown = ""
        self.preview_html = ""

        self._build()
        self.set_preview_markdown(DEFAULT_PREVIEW_MD)

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

        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, minsize=340)

        header = tk.Frame(card, bg=theme.CARD)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Preview & Comments",
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Controlla le differenze e inserisci un commento finale.",
            bg=theme.CARD,
            fg=theme.MUTED,
            font=theme.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        main_container = tk.Frame(card, bg=theme.CARD)
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))

        main_container.grid_columnconfigure(0, weight=1, uniform="col")
        main_container.grid_columnconfigure(1, weight=1, uniform="col")
        main_container.grid_rowconfigure(0, weight=1)

        # LEFT COLUMN: PREVIEW
        left_frame = tk.Frame(main_container, bg=theme.CARD)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            left_frame,
            text="Preview Differences",
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        preview_container = tk.Frame(
            left_frame,
            bg=theme.BORDER,
            bd=1,
            relief="solid"
        )
        preview_container.grid(row=1, column=0, sticky="nsew")

        self.preview_box = HtmlFrame(
            preview_container,
            messages_enabled=False,
            horizontal_scrollbar="auto"
        )
        self.preview_box.pack(fill="both", expand=True, padx=1, pady=1)

        # RIGHT COLUMN: COMMENT + AI PANEL
        right_frame = tk.Frame(main_container, bg=theme.CARD)
        right_frame.grid(row=0, column=1, sticky="nsew")

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1, uniform="right_rows")
        right_frame.grid_rowconfigure(1, weight=1, uniform="right_rows")

        top_right = tk.Frame(right_frame, bg=theme.CARD)
        top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        top_right.grid_columnconfigure(0, weight=1)
        top_right.grid_rowconfigure(1, weight=1)

        tk.Label(
            top_right,
            text="Comment",
            bg=theme.CARD,
            fg=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        comment_container = tk.Frame(top_right)
        comment_container.grid(row=1, column=0, sticky="nsew")

        comment_scroll = tk.Scrollbar(comment_container)
        comment_scroll.pack(side="right", fill="y")

        self.comment_box = tk.Text(
            comment_container,
            font=theme.FONT_COMMENT,
            relief="solid",
            bd=1,
            wrap="word",
            yscrollcommand=comment_scroll.set
        )
        self.comment_box.pack(side="left", fill="both", expand=True)

        comment_scroll.config(command=self.comment_box.yview)

        self.ai_panel = AIPanel(
            right_frame,
            get_comment=lambda: self.comment_box.get("1.0", "end").strip(),
            get_preview_markdown=lambda: self.preview_markdown.strip(),
            on_accept_text=self._set_comment_text
        )
        self.ai_panel.grid(row=1, column=0, sticky="nsew")

        # BUTTONS
        btn_frame = tk.Frame(card, bg=theme.CARD)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))

        tk.Button(
            btn_frame,
            text="<< Back",
            command=self.on_back,
            width=14,
            height=2,
            bg="#e9eef5",
            font=theme.FONT_BUTTON,
            relief="flat"
        ).pack(side="left")

        tk.Button(
            btn_frame,
            text="Update Changes_*.csv",
            command=self.on_update_changes,
            width=18,
            height=2,
            bg=theme.ACCENT2,
            fg=theme.TEXT,
            font=theme.FONT_BUTTON,
            relief="flat"
        ).pack(side="right", padx=5)

        tk.Button(
            btn_frame,
            text="Generate Log",
            command=self.on_generate,
            width=18,
            height=2,
            bg=theme.ACCENT2,
            fg=theme.TEXT,
            font=theme.FONT_BUTTON,
            relief="flat"
        ).pack(side="right", padx=5)

    # ============================================================
    # PREVIEW LOADING / RENDERING
    # ============================================================
    def load_preview(self, report_a, report_b, output_dir):
        self.report_a = report_a
        self.report_b = report_b
        self.output_dir = output_dir

        try:
            preview_text = self.preview_fn(report_a, report_b)
            self.set_preview_markdown(preview_text)
        except Exception as e:
            messagebox.showerror("Errore preview", str(e))

    def set_preview_markdown(self, md_text: str):
        self.preview_markdown = md_text
        self.preview_html = render_markdown(md_text)
        self.preview_box.load_html(self.preview_html)

    def set_preview_html(self, html_body: str):
        self.preview_markdown = ""
        self.preview_html = wrap_html_body(html_body)
        self.preview_box.load_html(self.preview_html)

    def _set_comment_text(self, text):
        self.comment_box.delete("1.0", "end")
        self.comment_box.insert("1.0", text)

    # ============================================================
    # CALLBACKS
    # ============================================================
    def on_generate(self):
        comment_text = self.comment_box.get("1.0", "end").strip()

        try:
            output_file = self.generate_fn(self.report_a, self.report_b, self.output_dir, comment_text)
            messagebox.showinfo("Completato", f"Change log creato con successo:\n\n{output_file}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione:\n\n{e}")

    def on_update_changes(self):
        csv_path = filedialog.asksaveasfilename(
            title="Seleziona o crea un file Changes CSV",
            defaultextension=".csv",
            initialfile="Changes_.csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not csv_path:
            return

        comment_text = self.comment_box.get("1.0", "end-1c").strip()
        version = self.get_version(self.report_b)

        try:
            append_change_record(csv_path, self.report_b, version, comment_text)
            messagebox.showinfo(
                "CSV aggiornato",
                f"Riga aggiunta correttamente al file:\n{csv_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore durante l'aggiornamento del CSV:\n{e}"
            )
