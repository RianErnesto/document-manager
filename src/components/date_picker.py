"""
Componente de seletor de data.
"""
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, date
from typing import Optional, Callable

from ..config import COLORS, FONTS


class DatePicker(ctk.CTkFrame):
    """Seletor de data com calendário."""

    def __init__(
        self,
        master,
        label: str = "",
        required: bool = False,
        on_change: Optional[Callable[[Optional[date]], None]] = None,
        **kwargs
    ):
        """
        Inicializa o seletor de data.

        Args:
            master: Widget pai
            label: Texto do label
            required: Se o campo é obrigatório
            on_change: Callback quando a data muda
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_text = label
        self._required = required
        self._on_change = on_change
        self._selected_date: Optional[date] = None

        self._create_widgets()

    def _create_widgets(self):
        """Cria os widgets do componente."""
        # Label
        if self._label_text:
            label_text = f"{self._label_text} *" if self._required else self._label_text
            self._label = ctk.CTkLabel(
                self,
                text=label_text,
                font=FONTS["body_bold"],
                text_color=COLORS["text"],
                anchor="w",
            )
            self._label.pack(anchor="w", pady=(0, 4))

        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x")

        # DateEntry do tkcalendar
        self._date_entry = DateEntry(
            container,
            width=15,
            background=COLORS["primary"],
            foreground=COLORS["text_light"],
            borderwidth=1,
            font=FONTS["input"],
            date_pattern="dd/mm/yyyy",
            locale="pt_BR",
        )
        self._date_entry.pack(side="left")

        # Botão para limpar
        self._clear_btn = ctk.CTkButton(
            container,
            text="✕",
            width=30,
            height=28,
            font=("Segoe UI", 12),
            fg_color="transparent",
            hover_color=COLORS["danger"],
            text_color=COLORS["text_secondary"],
            corner_radius=4,
            command=self.clear,
        )
        self._clear_btn.pack(side="left", padx=(4, 0))

        # Bind para detectar mudanças
        self._date_entry.bind("<<DateEntrySelected>>", self._on_date_selected)

    def _on_date_selected(self, event=None):
        """Callback quando uma data é selecionada."""
        self._selected_date = self._date_entry.get_date()
        if self._on_change:
            self._on_change(self._selected_date)

    def get(self) -> Optional[date]:
        """Retorna a data selecionada."""
        try:
            return self._date_entry.get_date()
        except Exception:
            return None

    def get_datetime(self) -> Optional[datetime]:
        """Retorna a data como datetime."""
        d = self.get()
        if d:
            return datetime.combine(d, datetime.min.time())
        return None

    def set(self, value: Optional[date]):
        """Define a data."""
        if value:
            self._date_entry.set_date(value)
            self._selected_date = value
        else:
            self.clear()

    def clear(self):
        """Limpa a data selecionada."""
        self._selected_date = None
        # Define para a data atual como placeholder
        self._date_entry.set_date(date.today())
        if self._on_change:
            self._on_change(None)

    def validate(self) -> bool:
        """Valida se a data foi preenchida (se obrigatório)."""
        if self._required and not self._selected_date:
            return False
        return True
