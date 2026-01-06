"""
Componente de botão estilizado.
"""
import customtkinter as ctk
from typing import Callable, Optional

from ..config import COLORS, FONTS, DIMENSIONS


class StyledButton(ctk.CTkButton):
    """Botão estilizado com variantes de cor."""

    VARIANTS = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["primary_hover"],
            "text_color": COLORS["text_light"],
        },
        "secondary": {
            "fg_color": COLORS["secondary"],
            "hover_color": COLORS["secondary_hover"],
            "text_color": COLORS["text_light"],
        },
        "success": {
            "fg_color": COLORS["success"],
            "hover_color": COLORS["success_hover"],
            "text_color": COLORS["text_light"],
        },
        "danger": {
            "fg_color": COLORS["danger"],
            "hover_color": COLORS["danger_hover"],
            "text_color": COLORS["text_light"],
        },
        "warning": {
            "fg_color": COLORS["warning"],
            "hover_color": COLORS["warning_hover"],
            "text_color": COLORS["text"],
        },
        "outline": {
            "fg_color": "transparent",
            "hover_color": COLORS["primary_light"],
            "text_color": COLORS["primary"],
            "border_width": 2,
            "border_color": COLORS["primary"],
        },
    }

    def __init__(
        self,
        master,
        text: str = "Button",
        command: Optional[Callable] = None,
        variant: str = "primary",
        width: int = 120,
        height: int = DIMENSIONS["button_height"],
        **kwargs
    ):
        """
        Inicializa o botão estilizado.

        Args:
            master: Widget pai
            text: Texto do botão
            command: Função a ser executada ao clicar
            variant: Variante de cor (primary, secondary, success, danger, warning, outline)
            width: Largura do botão
            height: Altura do botão
        """
        # Obtém configurações da variante
        variant_config = self.VARIANTS.get(variant, self.VARIANTS["primary"])

        # Prepara argumentos do botão
        button_args = {
            "master": master,
            "text": text,
            "command": command,
            "width": width,
            "height": height,
            "font": FONTS["button"],
            "corner_radius": DIMENSIONS["border_radius"],
            "fg_color": variant_config["fg_color"],
            "hover_color": variant_config["hover_color"],
            "text_color": variant_config["text_color"],
        }

        # Adiciona borda apenas se especificada
        if "border_width" in variant_config:
            button_args["border_width"] = variant_config["border_width"]
        if "border_color" in variant_config:
            button_args["border_color"] = variant_config["border_color"]

        # Configura o botão
        super().__init__(**button_args, **kwargs)

    def set_loading(self, loading: bool = True):
        """Define estado de carregamento do botão."""
        if loading:
            self._original_text = self.cget("text")
            self.configure(text="Aguarde...", state="disabled")
        else:
            if hasattr(self, "_original_text"):
                self.configure(text=self._original_text, state="normal")
            else:
                self.configure(state="normal")
