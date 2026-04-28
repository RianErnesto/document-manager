"""Classe principal da aplicação Document Manager."""
import customtkinter as ctk
import os
import sys
from pathlib import Path
from typing import Optional

from .components.message_box import MessageBox
from .config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    COLORS,
)
from .database import (
    AuthenticationError,
    ConfigError,
    DatabaseConnection,
    DatabaseConnectionError,
    DBConfig,
    NetworkShareAuthenticator,
    NetworkShareError,
    ServerUnreachableError,
    ShareNotFoundError,
    load_db_config,
)
from .services.audit_service import AuditLogger
from .services.backup_service import BackupResult, BackupService
from .views.main_view import MainView


class App(ctk.CTk):
    """Classe principal da aplicação."""

    def __init__(self):
        super().__init__()

        self._logger = AuditLogger()
        self._logger.info(f"Sistema iniciado — versão {APP_VERSION}")

        self._db_config: Optional[DBConfig] = None
        self._authenticator: Optional[NetworkShareAuthenticator] = None
        self._db: Optional[DatabaseConnection] = None
        self._main_view: Optional[MainView] = None
        self._initialized_ok = False

        # Configura a aparência sempre. A janela é configurada só se o backend
        # subir; durante a inicialização ela fica withdraw'd pra evitar:
        # 1) flash de janela vazia antes do modal de erro
        # 2) erros "wm command: application has been destroyed" ao destruir
        #    a root sem nunca ter rodado mainloop.
        self._configure_appearance()
        self._configure_window()
        self.withdraw()

        if not self._initialize_backend():
            # Backend falhou; remove handlers que poderiam disparar pós-destroy
            # e destrói a janela imediatamente. main.py checa initialized_ok()
            # antes de chamar mainloop, então não entramos no loop aqui.
            self.protocol("WM_DELETE_WINDOW", lambda: None)
            try:
                self.destroy()
            except Exception:
                pass
            return

        # Backend OK: revela a janela e cria a view principal.
        self.deiconify()
        self._create_main_view()
        self._initialized_ok = True

    def initialized_ok(self) -> bool:
        """True se o backend subiu e a UI principal foi criada."""
        return self._initialized_ok

    # ----- Backend bootstrap -----

    def _initialize_backend(self) -> bool:
        """Carrega config → autentica share → abre DB → backup.

        True = OK. False = falha fatal (config inválida ou usuário desistiu).
        """
        # 1) Config (não retentável — exige editar .env)
        try:
            self._db_config = load_db_config()
        except ConfigError as e:
            self._logger.critical(f"Falha ao carregar config: {e}")
            self._show_fatal_error(
                "Arquivo .env não encontrado ou incompleto. Verifique se o "
                "arquivo existe ao lado de DocumentManager.exe e contém todas "
                "as variáveis obrigatórias. Veja .env.example como referência."
            )
            return False

        # 2-4) Retentáveis (rede/DB)
        return self._connect_with_retry()

    def _connect_with_retry(self) -> bool:
        """Tenta autenticar share + abrir DB + backup. Loop até sucesso ou desistência."""
        while True:
            try:
                # Autenticar share
                self._authenticator = NetworkShareAuthenticator(
                    server=self._db_config.server,
                    share=self._db_config.share,
                    user=self._db_config.user,
                    password=self._db_config.password,
                )
                self._authenticator.connect()
                self._logger.info(
                    f"Conectado em {self._authenticator.unc_share} "
                    f"como {self._db_config.user}"
                )

                # Abrir DB (executa migrations internamente)
                self._db = DatabaseConnection(self._db_config)
                self._logger.info(f"Banco aberto: {self._db_config.unc_path}")

                # Backup (best-effort)
                backup_svc = BackupService(self._db.get_connection(), self._db_config)
                result = backup_svc.maybe_backup()
                if result.status == BackupResult.STATUS_CREATED:
                    self._logger.info(f"Backup: {result.message}")
                elif result.status == BackupResult.STATUS_SKIPPED_RECENT:
                    self._logger.info(f"Backup pulado: {result.message}")
                else:
                    self._logger.warning(f"Backup falhou: {result.message}")

                return True

            except AuthenticationError as e:
                self._logger.critical(f"Auth falhou: {type(e).__name__}")
                self._show_fatal_error(
                    "Usuário ou senha do servidor estão incorretos. "
                    "Atualize o arquivo .env com as credenciais corretas."
                )
                return False

            except (ServerUnreachableError, ShareNotFoundError) as e:
                self._logger.error(f"Servidor inacessível: {type(e).__name__}: {e}")
                if not self._show_retryable_error(
                    f"Não foi possível conectar ao servidor "
                    f"{self._db_config.server}. Verifique a rede e tente novamente."
                ):
                    return False

            except NetworkShareError as e:
                self._logger.error(f"Erro de rede: {type(e).__name__}: {e}")
                if not self._show_retryable_error(
                    f"Erro ao conectar no compartilhamento. Detalhes: {e}"
                ):
                    return False

            except DatabaseConnectionError as e:
                self._logger.error(f"DB falhou: {e}")
                if not self._show_retryable_error(
                    "Não foi possível abrir o banco de dados. Tente novamente "
                    "em alguns segundos. Se o problema persistir, contate o suporte."
                ):
                    return False

    def _show_fatal_error(self, message: str) -> None:
        """Modal de erro fatal — só botão OK. Bloqueia até o usuário fechar."""
        modal = MessageBox(self, message=message, variant="error")
        try:
            self.wait_window(modal)
        except Exception:
            pass

    def _show_retryable_error(self, message: str) -> bool:
        """Modal com Tentar Novamente / Sair. Retorna True se o usuário clicou retry."""
        modal = MessageBox(
            self,
            message=message,
            variant="error",
            confirm_text="Tentar Novamente",
            cancel_text="Sair",
            show_cancel=True,
        )
        try:
            self.wait_window(modal)
        except Exception:
            pass

        return modal.get_result()

    # ----- Configuração visual (inalterado) -----

    def _configure_window(self):
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        icon_path = self._get_icon_path()
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                self._logger.warning(f"Erro ao carregar ícone: {e}")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _configure_appearance(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["background"])

    def _get_icon_path(self) -> str:
        if getattr(sys, "frozen", False):
            base_path = Path(sys.executable).parent
            return str(base_path / "assets" / "LogoAmazonSmall.ico")
        else:
            base_path = Path(__file__).parent
            return str(base_path / "assets" / "LogoAmazonSmall.ico")

    def _create_main_view(self):
        self._main_view = MainView(self)
        self._main_view.pack(fill="both", expand=True)

    # ----- Shutdown -----

    def _on_closing(self):
        """Callback ao fechar a janela. Ordem importa: DB antes do share."""
        try:
            if self._db is not None:
                self._db.close()
        except Exception as e:
            self._logger.warning(f"Erro ao fechar conexão DB: {e}")

        try:
            if self._authenticator is not None:
                self._authenticator.disconnect()
        except Exception as e:
            self._logger.warning(f"Erro ao desconectar share: {e}")

        self._logger.info("Sistema encerrado")
        self.destroy()

    def run(self):
        self.mainloop()
