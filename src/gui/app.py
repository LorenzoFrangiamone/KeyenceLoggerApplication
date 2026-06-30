import tkinter as tk

from . import theme
from .page_input import InputPage
from .page_preview import PreviewPage


class CompareApp(tk.Tk):
    def __init__(self, validate_fn, generate_fn, preview_fn, compare_fn, get_version, load_paths_fn, save_paths_fn):
        super().__init__()

        self.minsize(600, 600)
        self.title("Compare Export Agent v3")
        self.geometry("860x520")
        self.configure(bg=theme.BG)
        self.resizable(True, True)

        self.page1 = InputPage(
            self,
            validate_fn=validate_fn,
            load_paths_fn=load_paths_fn,
            save_paths_fn=save_paths_fn,
            on_next=self._go_to_preview
        )
        self.page2 = PreviewPage(
            self,
            preview_fn=preview_fn,
            compare_fn=compare_fn,
            generate_fn=generate_fn,
            get_version=get_version,
            on_back=self._go_to_input
        )

        self.page1.pack(fill="both", expand=True)

    def _go_to_preview(self, report_a, report_b, output_dir):
        self.page1.pack_forget()
        self.page2.pack(fill="both", expand=True)
        self.page2.load_preview(report_a, report_b, output_dir)

    def _go_to_input(self):
        self.page2.pack_forget()
        self.page1.pack(fill="both", expand=True)
