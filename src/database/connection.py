"""Gerenciamento de conexão com banco de dados SQLite via UNC path."""
import sqlite3
from typing import Optional

from .db_config import DBConfig


class DatabaseConnectionError(Exception):
    """Erro ao abrir/manter conexão com o banco. Mensagem é amigável pra UI."""


class DatabaseConnection:
    """Singleton que gerencia a conexão SQLite via UNC path."""

    _instance = None
    _connection: Optional[sqlite3.Connection] = None
    _db_config: Optional[DBConfig] = None

    def __new__(cls, db_config: Optional[DBConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_config: Optional[DBConfig] = None):
        if self._connection is not None:
            return  # já inicializado

        if db_config is None:
            raise RuntimeError(
                "DatabaseConnection requires DBConfig on first initialization"
            )

        self._db_config = db_config
        self._connection = self._create_connection()
        self._apply_pragmas()
        self._run_migrations()

    def _create_connection(self) -> sqlite3.Connection:
        """Abre conexão SQLite via UNC path. Erros mapeados pra DatabaseConnectionError."""
        try:
            conn = sqlite3.connect(
                self._db_config.unc_path,
                check_same_thread=False,
                timeout=30.0,
                isolation_level="DEFERRED",
            )
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if "unable to open" in msg:
                raise DatabaseConnectionError(
                    f"Não foi possível abrir o banco em {self._db_config.unc_path}. "
                    "Verifique se o servidor está acessível e o arquivo existe ou pode ser criado."
                ) from e
            if "locked" in msg:
                raise DatabaseConnectionError(
                    "Banco de dados está bloqueado por outro processo. "
                    "Tente novamente em alguns segundos."
                ) from e
            raise DatabaseConnectionError(f"Erro ao abrir banco: {e}") from e

    def _apply_pragmas(self) -> None:
        """Aplica PRAGMAs obrigatórios pra operação segura em SMB.

        - journal_mode=DELETE: rollback journal padrão. NUNCA WAL em rede
          (WAL exige memória compartilhada entre processos, que não funciona em SMB).
        - busy_timeout=30000: 30s de espera por lock antes de SQLITE_BUSY.
        - synchronous=FULL: fsync após commit; durabilidade > performance.
        """
        self._connection.execute("PRAGMA journal_mode = DELETE")
        self._connection.execute("PRAGMA busy_timeout = 30000")
        self._connection.execute("PRAGMA synchronous = FULL")

    def _run_migrations(self) -> None:
        """Executa as migrations pendentes do banco de dados."""
        from .migrator import Migrator

        migrator = Migrator(self._connection)
        migrator.run()

    def get_connection(self) -> sqlite3.Connection:
        """Retorna a conexão com o banco de dados."""
        return self._connection

    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            self._connection.close()
            self._connection = None
            DatabaseConnection._instance = None
            DatabaseConnection._db_config = None
