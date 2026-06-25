import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterweb import HtmlFrame
import markdown
import threading
from src.AICorrector import AICorrection

class CompareApp(tk.Tk):
    def __init__(self, validate_fn, generate_fn, preview_fn):
        super().__init__()

        self.validate_fn = validate_fn
        self.generate_fn = generate_fn
        self.preview_fn = preview_fn

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

        # =========================
        # CARD ROOT
        # =========================
        card = tk.Frame(
            self.page2,
            bg=self.CARD,
            bd=1,
            relief="solid",
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        # layout del card:
        # riga 0 = header
        # riga 1 = main area espandibile
        # riga 2 = bottoni sempre visibili
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # =========================
        # HEADER
        # =========================
        header = tk.Frame(card, bg=self.CARD)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Preview & Comments",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Controlla le differenze e inserisci un commento finale.",
            bg=self.CARD,
            fg=self.MUTED,
            font=self.FONT_NORMAL
        ).pack(anchor="w", pady=(4, 0))

        # =========================
        # MAIN CONTENT AREA
        # =========================
        main_container = tk.Frame(card, bg=self.CARD)
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))

        # se vuoi un'altezza minima, meglio usare minsize
        card.grid_rowconfigure(1, minsize=340)

        # 2 colonne con stessa larghezza
        main_container.grid_columnconfigure(0, weight=1, uniform="col")
        main_container.grid_columnconfigure(1, weight=1, uniform="col")
        main_container.grid_rowconfigure(0, weight=1)

        # =========================
        # LEFT COLUMN
        # =========================
        left_frame = tk.Frame(main_container, bg=self.CARD)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            left_frame,
            text="Preview Differences",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        preview_container = tk.Frame(left_frame)
        preview_container.grid(row=1, column=0, sticky="nsew")

        preview_scroll = tk.Scrollbar(preview_container)
        preview_scroll.pack(side="right", fill="y")

        self.preview_box = tk.Text(
            preview_container,
            font=self.FONT_COMMENT,
            wrap="word",
            relief="solid",
            bd=1,
            yscrollcommand=preview_scroll.set
        )
        self.preview_box.pack(side="left", fill="both", expand=True)

        preview_scroll.config(command=self.preview_box.yview)

        # =========================
        # RIGHT COLUMN
        # =========================
        right_frame = tk.Frame(main_container, bg=self.CARD)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # due righe uguali = metà altezza sopra e metà sotto
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1, uniform="right_rows")
        right_frame.grid_rowconfigure(1, weight=1, uniform="right_rows")

        # -------------------------
        # TOP RIGHT: COMMENT
        # -------------------------
        top_right = tk.Frame(right_frame, bg=self.CARD)
        top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        top_right.grid_columnconfigure(0, weight=1)
        top_right.grid_rowconfigure(1, weight=1)

        tk.Label(
            top_right,
            text="Comment",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_LABEL
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        comment_container = tk.Frame(top_right)
        comment_container.grid(row=1, column=0, sticky="nsew")

        comment_scroll = tk.Scrollbar(comment_container)
        comment_scroll.pack(side="right", fill="y")

        self.comment_box = tk.Text(
            comment_container,
            font=self.FONT_COMMENT,
            relief="solid",
            bd=1,
            wrap="word",
            yscrollcommand=comment_scroll.set
        )
        self.comment_box.pack(side="left", fill="both", expand=True)

        comment_scroll.config(command=self.comment_box.yview)

        # -------------------------
        # BOTTOM RIGHT: AI HELPER
        # -------------------------
        AI_helper = tk.Frame(right_frame, bg=self.CARD)
        AI_helper.grid(row=1, column=0, sticky="nsew")

        AI_helper.grid_columnconfigure(0, weight=1)
        AI_helper.grid_rowconfigure(1, weight=1)

        # Header della sezione AI con titolo a sinistra e bottoni a destra
        ai_header = tk.Frame(AI_helper, bg=self.CARD)
        ai_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ai_header.grid_columnconfigure(0, weight=1)

        tk.Label(
            ai_header,
            text="AI Correct & Suggest",
            bg=self.CARD,
            fg=self.TEXT,
            font=self.FONT_LABEL
        ).grid(row=0, column=0, sticky="w")

        ai_btns = tk.Frame(ai_header, bg=self.CARD)
        ai_btns.grid(row=0, column=1, sticky="e")
        
        self.correct_btn = tk.Button(
            ai_btns,
            text="Correct",
            command=self.on_correct,
            width=10,
            bg="#e9eef5",
            font=self.FONT_BUTTON,
            relief="flat"
        )
        self.correct_btn.pack(side="left", padx=(0, 6))

        self.accept_btn = tk.Button(
            ai_btns,
            text="Accept Correction",
            command=self.on_accept_correction,
            width=16,
            bg=self.ACCENT2,
            fg=self.TEXT,
            font=self.FONT_BUTTON,
            relief="flat"
        )
        self.accept_btn.pack(side="left")

        notes_container = tk.Frame(AI_helper)
        notes_container.grid(row=1, column=0, sticky="nsew")

        notes_scroll = tk.Scrollbar(notes_container)
        notes_scroll.pack(side="right", fill="y")

        self.notes_box = tk.Text(
            notes_container,
            font=self.FONT_COMMENT,
            relief="solid",
            bd=1,
            wrap="word",
            yscrollcommand=notes_scroll.set
        )
        self.notes_box.pack(side="left", fill="both", expand=True)

        notes_scroll.config(command=self.notes_box.yview)

        # =========================
        # BUTTONS (SEMPRE VISIBILI)
        # =========================
        btn_frame = tk.Frame(card, bg=self.CARD)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))

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

        self.page1.pack_forget()
        self.page2.pack(fill="both", expand=True)

        try:
            preview_text = self.preview_fn(report_a, report_b)

            # ✅ abilita scrittura temporanea
            self.preview_box.config(state="normal")

            # ✅ scrive contenuto
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", preview_text)

            # ✅ applica colori
            self.apply_preview_formatting()

            # ✅ blocca editing (STEP 4)
            self.preview_box.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Errore preview", str(e))

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

    def apply_preview_formatting(self):
        text = self.preview_box.get("1.0", "end")

        # reset tag
        self.preview_box.tag_delete("added")
        self.preview_box.tag_delete("removed")
        self.preview_box.tag_delete("modified")
        self.preview_box.tag_delete("title")

        # crea tag colori
        self.preview_box.tag_config("added", foreground="green")
        self.preview_box.tag_config("removed", foreground="red")
        self.preview_box.tag_config("modified", foreground="orange")
        self.preview_box.tag_config("title", foreground="blue", font=("Consolas", 10, "bold"))

        lines = text.split("\n")

        for i, line in enumerate(lines):
            index_start = f"{i+1}.0"
            index_end = f"{i+1}.end"

            if "ADDED+" in line:
                self.preview_box.tag_add("added", index_start, index_end)
            elif "REMOVED-" in line:
                self.preview_box.tag_add("removed", index_start, index_end)
            elif "MODIFIED" in line:
                self.preview_box.tag_add("modified", index_start, index_end)
            elif line.startswith("##"):
                self.preview_box.tag_add("title", index_start, index_end)

    def on_correct(self):
        human = self.comment_box.get("1.0", "end").strip()
        auto = self.preview_box.get("1.0", "end").strip()

        # opzionale: validazione minima
        if not human and not auto:
            messagebox.showwarning(
                "Missing content",
                "Non ci sono contenuti da inviare alla correzione AI."
            )
            return

        # disattiva bottone Correct
        self.correct_btn.config(state="disabled")

        # mostra stato "thinking ..."
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", "thinking ...")
        self.notes_box.update_idletasks()

        def worker():
            try:
                # chiamata API / funzione AI
                result = AICorrection(auto, human)

                # se la risposta non è stringa, la converto
                if result is None:
                    result = ""
                else:
                    result = str(result)

                self.after(0, lambda: self._on_correct_success(result))

            except Exception as e:
                self.after(0, lambda: self._on_correct_error(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_correct_success(self, result):
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", result)
        self.correct_btn.config(state="normal")

    def _on_correct_error(self, error):
        self.notes_box.config(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", f"Errore durante la correzione AI:\n{error}")
        self.correct_btn.config(state="normal")

    def on_accept_correction(self):
        """
        Copia nel riquadro Comment solo la parte del testo AI
        che precede il marker '//Suggerimento:' (marker escluso).
        Se il marker non esiste, copia tutto il contenuto.
        """

        ai_text = self.notes_box.get("1.0", "end").strip()

        if not ai_text:
            return

        if ai_text.lower() == "thinking ...":
            return
        
        # Divide il testo in righe
        lines = ai_text.splitlines()

        # Prende il testo dalla seconda riga in poi
        if len(lines) < 2:
            return
        
        text_from_second_line = "\n".join(lines[1:]).strip()

        if not text_from_second_line:
            return

        marker = "//Suggerimento:"
        accepted_text = text_from_second_line.split(marker, 1)[0].rstrip()

        if not accepted_text:
            return

        self.comment_box.delete("1.0", "end")
        self.comment_box.insert("1.0", accepted_text)
