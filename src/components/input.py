"""
Componente de input estilizado com validação.
"""
import customtkinter as ctk
from typing import Callable, Optional, Tuple

from ..config import COLORS, FONTS, DIMENSIONS


class StyledInput(ctk.CTkFrame):
    """Input estilizado com label e validação."""

    def __init__(
        self,
        master,
        label: str = "",
        placeholder: str = "",
        required: bool = False,
        validation_type: str = "text",
        width: int = 200,
        validator: Optional[Callable[[str], Tuple[bool, str]]] = None,
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_text = label
        self._required = required
        self._validation_type = validation_type
        self._validator = validator
        self._on_change = on_change
        self._is_valid = True
        self._error_message = ""

        self._create_widgets(label, placeholder, width)

    def _create_widgets(self, label: str, placeholder: str, width: int):
        """Cria os widgets do componente."""
        # Label
        if label:
            label_text = f"{label} *" if self._required else label
            self._label = ctk.CTkLabel(
                self,
                text=label_text,
                font=FONTS["body_bold"],
                text_color=COLORS["text"],
                anchor="w",
            )
            self._label.pack(anchor="w", pady=(0, 4))

        # Container do input
        self._input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._input_frame.pack(fill="x")

        # Entry sem textvariable para placeholder funcionar
        self._entry = ctk.CTkEntry(
            self._input_frame,
            placeholder_text=placeholder,
            width=width,
            height=DIMENSIONS["input_height"],
            font=FONTS["input"],
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=DIMENSIONS["border_radius"],
            text_color=COLORS["text"],
        )
        self._entry.pack(side="left", fill="x", expand=True)

        # Binds
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)

        # Label de erro (inicialmente oculto)
        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=FONTS["small"],
            text_color=COLORS["danger"],
            anchor="w",
        )

    def _on_key_release(self, event=None):
        """Callback quando o valor muda."""
        value = self._entry.get()

        # Filtra caracteres para campos numéricos
        if self._validation_type == "number":
            filtered = "".join(c for c in value if c.isdigit())
            if filtered != value:
                self._entry.delete(0, "end")
                self._entry.insert(0, filtered)
                return

        # Callback externo
        if self._on_change:
            self._on_change(value)

    def _on_focus_out(self, event):
        """Valida quando perde o foco."""
        self.validate()

    def validate(self) -> bool:
        """Valida o valor do campo."""
        value = self._entry.get()
        self._is_valid = True
        self._error_message = ""

        # Validação de obrigatório
        if self._required and not value.strip():
            self._is_valid = False
            self._error_message = "Este campo é obrigatório"

        # Validação de número
        elif self._validation_type == "number" and value:
            try:
                num = int(value)
                if num <= 0:
                    self._is_valid = False
                    self._error_message = "O valor deve ser maior que zero"
            except ValueError:
                self._is_valid = False
                self._error_message = "Apenas números são permitidos"

        # Validação customizada
        elif self._validator and value:
            self._is_valid, self._error_message = self._validator(value)

        # Atualiza visual
        self._update_visual()
        return self._is_valid

    def _update_visual(self):
        """Atualiza o visual baseado no estado de validação."""
        if self._is_valid:
            self._entry.configure(border_color=COLORS["border"])
            self._error_label.pack_forget()
        else:
            self._entry.configure(border_color=COLORS["danger"])
            self._error_label.configure(text=self._error_message)
            self._error_label.pack(anchor="w", pady=(4, 0))

    def get(self) -> str:
        """Retorna o valor do campo."""
        return self._entry.get()

    def set(self, value: str):
        """Define o valor do campo."""
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def clear(self):
        """Limpa o campo."""
        self._entry.delete(0, "end")
        self._is_valid = True
        self._error_message = ""
        self._update_visual()

    def focus(self):
        """Coloca o foco no campo."""
        self._entry.focus()

    def is_valid(self) -> bool:
        """Retorna se o campo é válido."""
        return self._is_valid

    def get_error(self) -> str:
        """Retorna a mensagem de erro."""
        return self._error_message

    def set_error(self, message: str):
        """Define uma mensagem de erro manualmente."""
        self._is_valid = False
        self._error_message = message
        self._update_visual()

    def clear_error(self):
        """Limpa o erro."""
        self._is_valid = True
        self._error_message = ""
        self._update_visual()
