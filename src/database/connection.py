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
            self._create_tables()

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

    def _create_tables(self):
        """Cria as tabelas necessárias."""
        cursor = self._connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qr_code TEXT NOT NULL UNIQUE,
                shelf INTEGER NOT NULL,
                box INTEGER NOT NULL,
                rack INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Criar índices para melhorar performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_qr_code ON documents(qr_code)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
        """)

        self._connection.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Retorna a conexão com o banco de dados."""
        return self._connection

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            self._connection.close()
            self._connection = None
            DatabaseConnection._instance = None
