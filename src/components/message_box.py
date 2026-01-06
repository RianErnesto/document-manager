"""
Componente de caixa de mensagem.
"""
import customtkinter as ctk
from typing import Callable, Optional

from ..config import COLORS, FONTS, DIMENSIONS


class MessageBox(ctk.CTkToplevel):
    """Caixa de mensagem modal."""

    VARIANTS = {
        "success": {
            "icon": "✓",
            "icon_color": COLORS["success"],
            "title": "Sucesso",
        },
        "error": {
            "icon": "✕",
            "icon_color": COLORS["danger"],
            "title": "Erro",
        },
        "warning": {
            "icon": "⚠",
            "icon_color": COLORS["warning"],
            "title": "Atenção",
        },
        "info": {
            "icon": "ℹ",
            "icon_color": COLORS["primary"],
            "title": "Informação",
        },
        "confirm": {
            "icon": "?",
            "icon_color": COLORS["primary"],
            "title": "Confirmação",
        },
    }

    def __init__(
        self,
        master,
        message: str,
        variant: str = "info",
        title: Optional[str] = None,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "OK",
        cancel_text: str = "Cancelar",
        show_cancel: bool = False,
    ):
        """
        Inicializa a caixa de mensagem.

        Args:
            master: Widget pai
            message: Mensagem a exibir
            variant: Tipo de mensagem (success, error, warning, info, confirm)
            title: Título da janela (usa padrão da variante se não fornecido)
            on_confirm: Callback ao confirmar
            on_cancel: Callback ao cancelar
            confirm_text: Texto do botão de confirmação
            cancel_text: Texto do botão de cancelamento
            show_cancel: Exibir botão de cancelamento
        """
        super().__init__(master)

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._result = False

        # Configuração da variante
        variant_config = self.VARIANTS.get(variant, self.VARIANTS["info"])

        # Configuração da janela
        window_title = title or variant_config["title"]
        self.title(window_title)
        self.geometry("400x200")
        self.resizable(False, False)

        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"+{x}+{y}")

        # Modal
        self.transient(master)
        self.grab_set()

        # Configuração de fundo
        self.configure(fg_color=COLORS["surface"])

        # Cria os widgets
        self._create_widgets(message, variant_config, confirm_text, cancel_text, show_cancel)

        # Bind de teclas
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self._cancel())

        # Foco no botão
        self.focus()

    def _create_widgets(
        self,
        message: str,
        variant_config: dict,
        confirm_text: str,
        cancel_text: str,
        show_cancel: bool,
    ):
        """Cria os widgets da caixa de mensagem."""
        # Container principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Área de conteúdo
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Ícone
        icon_label = ctk.CTkLabel(
            content_frame,
            text=variant_config["icon"],
            font=("Segoe UI", 36),
            text_color=variant_config["icon_color"],
        )
        icon_label.pack(pady=(0, 10))

        # Mensagem
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=FONTS["body"],
            text_color=COLORS["text"],
            wraplength=350,
        )
        message_label.pack(pady=(0, 20))

        # Botões
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        # Botão de confirmação
        confirm_btn = ctk.CTkButton(
            button_frame,
            text=confirm_text,
            command=self._confirm,
            width=100,
            height=36,
            font=FONTS["button"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=DIMENSIONS["border_radius"],
        )

        if show_cancel:
            # Botão de cancelamento
            cancel_btn = ctk.CTkButton(
                button_frame,
                text=cancel_text,
                command=self._cancel,
                width=100,
                height=36,
                font=FONTS["button"],
                fg_color=COLORS["secondary"],
                hover_color=COLORS["secondary_hover"],
                corner_radius=DIMENSIONS["border_radius"],
            )
            cancel_btn.pack(side="right", padx=(10, 0))
            confirm_btn.pack(side="right")
        else:
            confirm_btn.pack(expand=True)

    def _confirm(self):
        """Ação de confirmação."""
        self._result = True
        if self._on_confirm:
            self._on_confirm()
        self.destroy()

    def _cancel(self):
        """Ação de cancelamento."""
        self._result = False
        if self._on_cancel:
            self._on_cancel()
        self.destroy()

    def get_result(self) -> bool:
        """Retorna o resultado da caixa de mensagem."""
        return self._result


def show_message(
    master,
    message: str,
    variant: str = "info",
    title: Optional[str] = None,
):
    """
    Exibe uma mensagem simples.

    Args:
        master: Widget pai
        message: Mensagem
        variant: Tipo (success, error, warning, info)
        title: Título opcional
    """
    dialog = MessageBox(master, message, variant, title)
    master.wait_window(dialog)


def show_confirm(
    master,
    message: str,
    title: str = "Confirmação",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
) -> bool:
    """
    Exibe uma caixa de confirmação.

    Args:
        master: Widget pai
        message: Mensagem
        title: Título
        on_confirm: Callback ao confirmar
        on_cancel: Callback ao cancelar

    Returns:
        True se confirmado, False se cancelado
    """
    dialog = MessageBox(
        master,
        message,
        variant="confirm",
        title=title,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        confirm_text="Sim",
        cancel_text="Não",
        show_cancel=True,
    )
    master.wait_window(dialog)
    return dialog._result
