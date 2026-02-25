"""
Classe principal da aplicação Document Manager.
"""
import customtkinter as ctk
import os
import sys
from pathlib import Path

from .config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    COLORS,
)
from .services.audit_service import AuditLogger
from .views.main_view import MainView


class App(ctk.CTk):
    """Classe principal da aplicação."""

    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()

        self._logger = AuditLogger()
        self._logger.info(f"Sistema iniciado — versão {APP_VERSION}")

        self._configure_window()
        self._configure_appearance()
        self._create_main_view()

    def _configure_window(self):
        """Configura a janela principal."""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        # Ícone (se existir)
        icon_path = self._get_icon_path()
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                self._logger.warning(f"Erro ao carregar ícone: {e}")

        # Protocolo de fechamento
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _configure_appearance(self):
        """Configura a aparência da aplicação."""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Cor de fundo
        self.configure(fg_color=COLORS["background"])

    def _get_icon_path(self) -> str:
        """Retorna o caminho do ícone."""
        if getattr(sys, 'frozen', False):
            # Executável PyInstaller
            base_path = Path(sys.executable).parent
            return str(base_path / "assets" / "LogoAmazonSmall.ico")
        else:
            # Desenvolvimento
            base_path = Path(__file__).parent
            return str(base_path / "assets" / "LogoAmazonSmall.ico")

    def _create_main_view(self):
        """Cria a view principal."""
        self._main_view = MainView(self)
        self._main_view.pack(fill="both", expand=True)

    def _on_closing(self):
        """Callback ao fechar a aplicação."""
        self._logger.info("Sistema encerrado")
        self.destroy()

    def run(self):
        """Inicia o loop principal da aplicação."""
        self.mainloop()
