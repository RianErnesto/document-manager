"""
Sistema de auditoria e logging da aplicação.

Salva logs em C:\\CPD\\Logs\\document_manager.log com rotação por tamanho.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = r"C:\CPD\Logs"
LOG_FILE = os.path.join(LOG_DIR, "document_manager.log")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5


class AuditLogger:
    """Logger singleton para auditoria do sistema."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        os.makedirs(LOG_DIR, exist_ok=True)

        self._logger = logging.getLogger("document_manager")
        self._logger.setLevel(logging.DEBUG)

        # Evita handlers duplicados em caso de re-import
        if not self._logger.handlers:
            handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)

    def critical(self, message: str):
        self._logger.critical(message)
