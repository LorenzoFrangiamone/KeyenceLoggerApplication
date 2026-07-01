import customtkinter as ctk


class AutoHideScrollbar(ctk.CTkScrollbar):
    """CTkScrollbar che si nasconde da sola quando il widget collegato
    mostra già tutto il proprio contenuto, invece di restare sempre
    visibile come una scrollbar Tk/ttk standard.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._pack_kwargs = None
        self._grid_kwargs = None

    def pack(self, **kwargs):
        self._pack_kwargs = kwargs
        super().pack(**kwargs)

    def grid(self, **kwargs):
        self._grid_kwargs = kwargs
        super().grid(**kwargs)

    def set(self, start_value, end_value):
        if float(start_value) <= 0.0 and float(end_value) >= 1.0:
            if self._grid_kwargs is not None:
                self.grid_remove()
            elif self._pack_kwargs is not None:
                self.pack_forget()
        else:
            if self._grid_kwargs is not None:
                super().grid(**self._grid_kwargs)
            elif self._pack_kwargs is not None:
                super().pack(**self._pack_kwargs)
        super().set(start_value, end_value)
