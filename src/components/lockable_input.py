"""
Componente de input com funcionalidade de trava (lock).
"""
import customtkinter as ctk
from typing import Callable, Optional, Tuple

from ..config import COLORS, FONTS, DIMENSIONS


class LockableInput(ctk.CTkFrame):
    """Input com funcionalidade de trava para manter valor após cadastro."""

    def __init__(
        self,
        master,
        label: str = "",
        placeholder: str = "",
        required: bool = False,
        validation_type: str = "number",
        width: int = 100,
        validator: Optional[Callable[[str], Tuple[bool, str]]] = None,
        on_change: Optional[Callable[[str], None]] = None,
        lockable: bool = True,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_text = label
        self._required = required
        self._validation_type = validation_type
        self._validator = validator
        self._on_change = on_change
        self._lockable = lockable
        self._is_locked = False
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

        # Container do input e botão de trava
        self._input_container = ctk.CTkFrame(self, fg_color="transparent")
        self._input_container.pack(fill="x")

        # Entry sem textvariable para placeholder funcionar
        self._entry = ctk.CTkEntry(
            self._input_container,
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
        self._entry.pack(side="left")

        # Setas de incremento/decremento para campos numéricos
        if self._validation_type == "number":
            spinner_frame = ctk.CTkFrame(
                self._input_container,
                fg_color=COLORS["surface"],
                border_color=COLORS["border"],
                border_width=1,
                corner_radius=4,
                width=20,
                height=DIMENSIONS["input_height"],
            )
            spinner_frame.pack(side="left", padx=(2, 0))
            spinner_frame.pack_propagate(False)

            btn_height = DIMENSIONS["input_height"] // 2

            self._up_button = ctk.CTkButton(
                spinner_frame,
                text="\u25B2",
                width=20,
                height=btn_height,
                font=("Segoe UI", 8),
                fg_color="transparent",
                hover_color=COLORS["primary_light"],
                text_color=COLORS["text_secondary"],
                corner_radius=2,
                command=self._increment,
            )
            self._up_button.pack(fill="x")

            self._down_button = ctk.CTkButton(
                spinner_frame,
                text="\u25BC",
                width=20,
                height=btn_height,
                font=("Segoe UI", 8),
                fg_color="transparent",
                hover_color=COLORS["primary_light"],
                text_color=COLORS["text_secondary"],
                corner_radius=2,
                command=self._decrement,
            )
            self._down_button.pack(fill="x")

        # Botão de trava
        if self._lockable:
            self._lock_button = ctk.CTkButton(
                self._input_container,
                text="\U0001f513",
                width=36,
                height=DIMENSIONS["input_height"],
                font=("Segoe UI", 14),
                fg_color="transparent",
                hover_color=COLORS["primary_light"],
                text_color=COLORS["text_secondary"],
                corner_radius=DIMENSIONS["border_radius"],
                command=self._toggle_lock,
            )
            self._lock_button.pack(side="left", padx=(4, 0))

        # Binds
        self._entry.bind("<KeyRelease>", self._on_key_release)

        # Label de erro
        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=FONTS["small"],
            text_color=COLORS["danger"],
            anchor="w",
        )

    def _increment(self):
        """Incrementa o valor numérico."""
        value = self._entry.get()
        num = int(value) if value.isdigit() else 0
        self._entry.delete(0, "end")
        self._entry.insert(0, str(num + 1))

    def _decrement(self):
        """Decrementa o valor numérico (mínimo 1)."""
        value = self._entry.get()
        num = int(value) if value.isdigit() else 2
        if num > 1:
            self._entry.delete(0, "end")
            self._entry.insert(0, str(num - 1))

    def _toggle_lock(self):
        """Alterna o estado de trava."""
        self._is_locked = not self._is_locked
        self._update_lock_visual()

    def _update_lock_visual(self):
        """Atualiza o visual baseado no estado de trava."""
        if self._is_locked:
            self._lock_button.configure(
                text="\U0001f512",
                fg_color=COLORS["locked"],
                text_color=COLORS["locked_border"],
            )
            self._entry.configure(
                fg_color=COLORS["locked"],
                border_color=COLORS["locked_border"],
            )
        else:
            self._lock_button.configure(
                text="\U0001f513",
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
            )
            self._entry.configure(
                fg_color=COLORS["surface"],
                border_color=COLORS["border"] if self._is_valid else COLORS["danger"],
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

        # Máscara para campo de processo (0000/00000...)
        elif self._validation_type == "process":
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) > 4:
                masked = digits[:4] + "/" + digits[4:]
            else:
                masked = digits
            if masked != value:
                self._entry.delete(0, "end")
                self._entry.insert(0, masked)
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

        # Validação de processo (mínimo 0000/0)
        elif self._validation_type == "process" and value:
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) < 5:
                self._is_valid = False
                self._error_message = "Formato mínimo: 0000/0"

        # Validação customizada
        elif self._validator and value:
            self._is_valid, self._error_message = self._validator(value)

        # Atualiza visual
        self._update_visual()
        return self._is_valid

    def _update_visual(self):
        """Atualiza o visual baseado no estado de validação."""
        if self._is_valid:
            if not self._is_locked:
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

    def clear(self, force: bool = False):
        """
        Limpa o campo.

        Args:
            force: Se True, limpa mesmo se estiver travado
        """
        if force or not self._is_locked:
            self._entry.delete(0, "end")
            if hasattr(self._entry, "_activate_placeholder"):
                self._entry._activate_placeholder()
            self._is_valid = True
            self._error_message = ""
            self._update_visual()

    def focus(self):
        """Coloca o foco no campo."""
        self._entry.focus()

    def is_valid(self) -> bool:
        """Retorna se o campo é válido."""
        return self._is_valid

    def is_locked(self) -> bool:
        """Retorna se o campo está travado."""
        return self._is_locked

    def set_locked(self, locked: bool):
        """Define o estado de trava."""
        self._is_locked = locked
        self._update_lock_visual()

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
