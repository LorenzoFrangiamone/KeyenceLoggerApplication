import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.backEnd import append_change_record, list_autocomplete_terms
from . import theme
from .ai_panel import AIPanel
from .diff_tree import DiffTree
from .scrollbar import AutoHideScrollbar

PLACEHOLDER_TEXT = "Seleziona Report A e Report B, poi premi Next per generare la preview."


class PreviewPage(ctk.CTkFrame):
    def __init__(self, parent, preview_fn, compare_fn, generate_fn, get_version, on_back):
        super().__init__(parent, fg_color=theme.BG, corner_radius=0)
        self.preview_fn = preview_fn
        self.compare_fn = compare_fn
        self.generate_fn = generate_fn
        self.get_version = get_version
        self.on_back = on_back

        self.report_a = ""
        self.report_b = ""
        self.output_dir = ""
        self.preview_markdown = ""
        self.autocomplete_terms = []
        self._tab_complete_state = None

        self._build()
        self.diff_tree.show_placeholder(PLACEHOLDER_TEXT)

    def _build(self):
        card = ctk.CTkFrame(
            self,
            fg_color=theme.CARD,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.BORDER
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, minsize=460)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            header,
            text="Preview & Comments",
            text_color=theme.TEXT,
            font=theme.FONT_TITLE
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Controlla le differenze e inserisci un commento finale.",
            text_color=theme.MUTED,
            font=theme.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        main_container = ctk.CTkFrame(card, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))

        main_container.grid_columnconfigure(0, weight=2, uniform="col")
        main_container.grid_columnconfigure(1, weight=3, uniform="col")
        main_container.grid_rowconfigure(0, weight=1)

        # LEFT COLUMN: DIFF TREE
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame,
            text="Preview Differences",
            text_color=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        preview_container = ctk.CTkFrame(
            left_frame,
            fg_color=theme.CARD,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.BORDER
        )
        preview_container.grid(row=1, column=0, sticky="nsew")
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)

        self.diff_tree = DiffTree(preview_container)
        self.diff_tree.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)

        tree_scroll = AutoHideScrollbar(
            preview_container,
            orientation="vertical",
            command=self.diff_tree.yview,
            fg_color="transparent",
            button_color=theme.BORDER_STRONG,
            button_hover_color=theme.MUTED,
            corner_radius=theme.RADIUS_CONTROL,
            width=12
        )
        tree_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=10)
        self.diff_tree.configure(yscrollcommand=tree_scroll.set)

        # RIGHT COLUMN: COMMENT + AI PANEL
        right_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew")

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1, uniform="right_rows")
        right_frame.grid_rowconfigure(1, weight=1, uniform="right_rows")

        top_right = ctk.CTkFrame(right_frame, fg_color="transparent")
        top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        top_right.grid_columnconfigure(0, weight=1)
        top_right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            top_right,
            text="Comment",
            text_color=theme.TEXT,
            font=theme.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        comment_container = ctk.CTkFrame(top_right, fg_color="transparent")
        comment_container.grid(row=1, column=0, sticky="nsew")

        comment_scroll = AutoHideScrollbar(
            comment_container,
            orientation="vertical",
            fg_color="transparent",
            button_color=theme.BORDER_STRONG,
            button_hover_color=theme.MUTED,
            corner_radius=theme.RADIUS_CONTROL,
            width=12
        )
        comment_scroll.pack(side="right", fill="y")

        self.comment_box = ctk.CTkTextbox(
            comment_container,
            font=theme.FONT_COMMENT,
            fg_color=theme.FIELD,
            text_color=theme.TEXT,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            corner_radius=theme.RADIUS_CONTROL,
            wrap="word",
            activate_scrollbars=False,
            yscrollcommand=comment_scroll.set
        )
        self.comment_box.pack(side="left", fill="both", expand=True)
        self.comment_box.bind("<Tab>", self._on_comment_tab)

        comment_scroll.configure(command=self.comment_box.yview)

        self.ai_panel = AIPanel(
            right_frame,
            get_comment=lambda: self.comment_box.get("1.0", "end").strip(),
            get_preview_markdown=lambda: self.preview_markdown.strip(),
            on_accept_text=self._set_comment_text
        )
        self.ai_panel.grid(row=1, column=0, sticky="nsew")

        # BUTTONS
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))
        btn_frame.grid_columnconfigure(0, weight=2, uniform="col")
        btn_frame.grid_columnconfigure(1, weight=3, uniform="col")

        ctk.CTkButton(
            btn_frame,
            text="<< Back",
            command=self.on_back,
            width=170,
            height=58,
            fg_color=theme.ACCENT2,
            text_color=theme.TEXT,
            hover_color=theme.ACCENT2_ACTIVE,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
        ).grid(row=0, column=0, sticky="w")

        # Generate Log + Update Changes fill the whole right column and
        # split its width in half, dynamically (same pattern as Correct /
        # Accept Correction in ai_panel.py's controls_row).
        right_btns = ctk.CTkFrame(btn_frame, fg_color="transparent")
        right_btns.grid(row=0, column=1, sticky="ew")
        right_btns.grid_columnconfigure(0, weight=1, uniform="right_btns")
        right_btns.grid_columnconfigure(1, weight=1, uniform="right_btns")

        ctk.CTkButton(
            right_btns,
            text="Generate Log",
            command=self.on_generate,
            height=58,
            fg_color=theme.ACCENT,
            text_color="white",
            hover_color=theme.ACCENT_ACTIVE,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            right_btns,
            text="Update Changes_*.csv",
            command=self.on_update_changes,
            height=58,
            fg_color=theme.ACCENT2,
            text_color=theme.TEXT,
            hover_color=theme.ACCENT2_ACTIVE,
            border_color=theme.BORDER_STRONG,
            border_width=1,
            font=theme.FONT_BUTTON,
            corner_radius=theme.RADIUS_CONTROL
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    # ============================================================
    # PREVIEW LOADING
    # ============================================================
    def load_preview(self, report_a, report_b, output_dir):
        self.report_a = report_a
        self.report_b = report_b
        self.output_dir = output_dir

        try:
            self.preview_markdown = self.preview_fn(report_a, report_b)
            comparison = self.compare_fn(report_a, report_b)
            terms = list_autocomplete_terms(report_a) | list_autocomplete_terms(report_b)
        except Exception as e:
            messagebox.showerror("Errore preview", str(e))
            return

        self.diff_tree.load_comparison(comparison)
        self.autocomplete_terms = sorted(terms, key=str.lower)
        self._tab_complete_state = None

    def _set_comment_text(self, text):
        self.comment_box.delete("1.0", "end")
        self.comment_box.insert("1.0", text)

    # ============================================================
    # AUTOCOMPLETAMENTO COMMENTO (TAB)
    # ============================================================
    def _on_comment_tab(self, event):
        text = self.comment_box
        insert_idx = text.index("insert")

        state = self._tab_complete_state
        if state and text.compare(insert_idx, "==", state["end"]):
            state["current"] = (state["current"] + 1) % len(state["matches"])
            return self._apply_completion(state["start"], insert_idx, state["matches"][state["current"]], state)

        line_start = text.index("insert linestart")
        line_text = text.get(line_start, insert_idx)

        found = self._find_completion_matches(line_text)
        if found is None:
            self._tab_complete_state = None
            return None

        offset, matches = found
        start_idx = text.index(f"{line_start} +{offset}c")
        new_state = {"start": start_idx, "matches": matches, "current": 0}
        return self._apply_completion(start_idx, insert_idx, matches[0], new_state)

    def _find_completion_matches(self, line_text):
        """
        Cerca, fra tutti i suffissi non vuoti della porzione di riga già
        digitata (dal più lungo al più corto), il primo che è prefisso
        (case-insensitive) di almeno un termine noto. Questo permette il
        completamento ovunque nella riga, non solo a inizio riga.
        """
        for offset in range(len(line_text)):
            fragment = line_text[offset:]
            matches = [t for t in self.autocomplete_terms if t.lower().startswith(fragment.lower())]
            if matches:
                return offset, matches
        return None

    def _apply_completion(self, start_idx, old_end, replacement, state):
        text = self.comment_box
        text.delete(start_idx, old_end)
        text.insert(start_idx, replacement)
        state["end"] = text.index(f"{start_idx} +{len(replacement)}c")
        self._tab_complete_state = state
        return "break"

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
        folder_name = os.path.basename(os.path.normpath(self.report_b))

        try:
            append_change_record(csv_path, folder_name, version, comment_text)
            messagebox.showinfo(
                "CSV aggiornato",
                f"Riga aggiunta correttamente al file:\n{csv_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore durante l'aggiornamento del CSV:\n{e}"
            )
