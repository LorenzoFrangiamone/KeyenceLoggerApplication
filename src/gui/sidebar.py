import tkinter as tk

import customtkinter as ctk

from . import theme

SIDEBAR_WIDTH = 72
BUTTON_SIZE = 48


class _NavButton(tk.Canvas):
    """Icona di navigazione disegnata a mano su Canvas (niente font/emoji:
    così il glifo resta un semplice outline monocromatico, coerente col
    tema scuro, senza dipendere dalla copertura Unicode del font di sistema).
    """

    def __init__(self, parent, icon_kind, command):
        super().__init__(
            parent,
            width=BUTTON_SIZE,
            height=BUTTON_SIZE,
            bg=theme.BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.icon_kind = icon_kind
        self.command = command
        self._active = False
        self._enabled = True
        self.bind("<Button-1>", lambda e: self.command())
        self._draw()

    def set_active(self, active):
        self._active = active
        self._draw()

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def _draw(self):
        self.delete("all")
        c = BUTTON_SIZE / 2
        pad = 6

        if self._active:
            self.create_rectangle(
                pad, pad, BUTTON_SIZE - pad, BUTTON_SIZE - pad,
                fill=theme.ACCENT_MUTED_BG, outline=""
            )
            color = theme.ACCENT_SOFT
        elif not self._enabled:
            color = theme.BORDER_STRONG
        else:
            color = theme.MUTED

        if self.icon_kind == "input":
            self._draw_folder(c, color)
        else:
            self._draw_compare(c, color)

    def _draw_folder(self, c, color):
        self.create_rectangle(c - 10, c - 5, c - 2, c - 9, outline=color, width=1.6)
        self.create_rectangle(c - 10, c - 5, c + 10, c + 8, outline=color, width=1.6)

    def _draw_compare(self, c, color):
        self.create_rectangle(c - 10, c - 8, c - 2, c + 8, outline=color, width=1.6)
        self.create_rectangle(c + 2, c - 8, c + 10, c + 8, outline=color, width=1.6)


class Sidebar(ctk.CTkFrame):
    """Banda di navigazione persistente a sinistra, con un'icona per
    ciascuna delle due schermate. 'Preview' resta disabilitata finché
    non è stato completato almeno un passaggio da InputPage.
    """

    def __init__(self, parent, on_select):
        super().__init__(parent, fg_color=theme.BG, corner_radius=0, width=SIDEBAR_WIDTH)
        self.pack_propagate(False)
        self.on_select = on_select
        self._preview_enabled = False

        self.input_btn = _NavButton(self, "input", lambda: self.on_select("input"))
        self.input_btn.pack(pady=(20, 12))

        self.preview_btn = _NavButton(self, "preview", self._handle_preview_click)
        self.preview_btn.pack(pady=(0, 12))
        self.preview_btn.set_enabled(False)

        self.set_active("input")

    def _handle_preview_click(self):
        if self._preview_enabled:
            self.on_select("preview")

    def set_preview_enabled(self, enabled):
        self._preview_enabled = enabled
        self.preview_btn.set_enabled(enabled)

    def set_active(self, which):
        self.input_btn.set_active(which == "input")
        self.preview_btn.set_active(which == "preview")
