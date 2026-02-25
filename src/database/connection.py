"""
Gerenciamento de conexão com banco de dados SQLite.
"""
import sqlite3
import os
from pathlib import Path


class DatabaseConnection:
    """Classe para gerenciar conexão com SQLite."""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._db_path = self._get_db_path()
            self._connection = self._create_connection()
            self._run_migrations()

    def _get_db_path(self) -> str:
        """Retorna o caminho do banco de dados."""
        # Usa a pasta do executável ou do script
        if getattr(os.sys, 'frozen', False):
            # Executável PyInstaller
            base_path = Path(os.sys.executable).parent
        else:
            # Desenvolvimento
            base_path = Path(__file__).parent.parent.parent

        db_path = base_path / "documents.db"
        return str(db_path)

    def _create_connection(self) -> sqlite3.Connection:
        """Cria conexão com o banco de dados."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _run_migrations(self):
        """Executa as migrations pendentes do banco de dados."""
        from .migrator import Migrator

        migrator = Migrator(self._connection)
        migrator.run()

    def get_connection(self) -> sqlite3.Connection:
        """Retorna a conexão com o banco de dados."""
        return self._connection

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            self._connection.close()
            self._connection = None
            DatabaseConnection._instance = None
