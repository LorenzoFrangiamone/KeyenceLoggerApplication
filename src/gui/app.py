import ctypes
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from . import theme
from .page_input import InputPage
from .page_preview import PreviewPage
from .sidebar import Sidebar

ctk.set_appearance_mode("dark")


class CompareApp(ctk.CTk):
    def __init__(self, validate_fn, generate_fn, preview_fn, compare_fn, get_version, load_paths_fn, save_paths_fn):
        super().__init__()

        self.minsize(860, 700)
        self.title("Compare Export Agent v02")
        self.geometry("1120x760")
        self.configure(fg_color=theme.BG)
        self.resizable(True, True)

        self._apply_dark_titlebar()
        self._configure_ttk_theme()

        self._preview_ready = False

        container = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        container.pack(fill="both", expand=True)

        self.sidebar = Sidebar(container, on_select=self._on_sidebar_select)
        self.sidebar.pack(side="left", fill="y")

        tk.Frame(container, width=1, bg=theme.BORDER).pack(side="left", fill="y")

        content = ctk.CTkFrame(container, fg_color=theme.BG, corner_radius=0)
        content.pack(side="left", fill="both", expand=True)

        self.page1 = InputPage(
            content,
            validate_fn=validate_fn,
            load_paths_fn=load_paths_fn,
            save_paths_fn=save_paths_fn,
            on_next=self._go_to_preview
        )
        self.page2 = PreviewPage(
            content,
            preview_fn=preview_fn,
            compare_fn=compare_fn,
            generate_fn=generate_fn,
            get_version=get_version,
            on_back=self._go_to_input
        )

        self.page1.pack(fill="both", expand=True)

    def _apply_dark_titlebar(self):
        """La titlebar della finestra è disegnata da Windows (DWM), non da
        Tk: senza questa chiamata resta chiara anche con tutto il resto
        dell'app a tema scuro. Richiede Windows 10 1809+; su build più
        vecchie o sistemi non Windows fallisce silenziosamente.
        """
        try:
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value)
            )
        except (AttributeError, OSError):
            pass

    def _configure_ttk_theme(self):
        """Il DiffTree resta un ttk.Treeview (customtkinter non ha un
        equivalente): serve comunque il tema 'clam', l'unico che rispetta
        pienamente i colori custom su Windows a differenza di 'vista'.
        """
        style = ttk.Style(self)
        style.theme_use("clam")

    def _on_sidebar_select(self, which):
        if which == "input":
            self._go_to_input()
        elif which == "preview" and self._preview_ready:
            self.page1.pack_forget()
            self.page2.pack(fill="both", expand=True)
            self.sidebar.set_active("preview")

    def _go_to_preview(self, report_a, report_b, output_dir):
        self.page1.pack_forget()
        self.page2.pack(fill="both", expand=True)
        self.page2.load_preview(report_a, report_b, output_dir)
        self._preview_ready = True
        self.sidebar.set_preview_enabled(True)
        self.sidebar.set_active("preview")

    def _go_to_input(self):
        self.page2.pack_forget()
        self.page1.pack(fill="both", expand=True)
        self.sidebar.set_active("input")
