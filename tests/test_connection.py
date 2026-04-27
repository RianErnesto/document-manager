"""Testes de DatabaseConnection — foco nos PRAGMAs obrigatórios pra SMB."""
import sqlite3

import pytest

from src.database.connection import DatabaseConnection, DatabaseConnectionError
from src.database.db_config import DBConfig


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reseta o singleton entre testes pra cada teste construir do zero."""
    DatabaseConnection._instance = None
    DatabaseConnection._connection = None
    DatabaseConnection._db_config = None
    yield
    if DatabaseConnection._instance is not None:
        try:
            DatabaseConnection._instance.close()
        except Exception:
            pass
    DatabaseConnection._instance = None
    DatabaseConnection._connection = None
    DatabaseConnection._db_config = None


def _make_config(tmp_path) -> DBConfig:
    """DBConfig que aponta para um arquivo SQLite temporário local (não UNC)."""
    return DBConfig(
        server=str(tmp_path).replace("\\", "/"),
        share="ignored",
        filename="ignored.db",
        user="u",
        password="p",
        backup_dir=str(tmp_path),
        backup_interval_hours=24,
        backup_retention_days=30,
    )


def test_pragmas_applied_after_connect(tmp_path, monkeypatch):
    """Os 3 PRAGMAs obrigatórios devem estar setados na conexão aberta.

    journal_mode=DELETE → "delete" (lowercase no retorno do PRAGMA).
    busy_timeout=30000 → 30000.
    synchronous=FULL → 2 (constante interna do SQLite: OFF=0, NORMAL=1, FULL=2, EXTRA=3).
    """
    cfg = _make_config(tmp_path)
    local_db = tmp_path / "actual.db"

    real_connect = sqlite3.connect

    def fake_connect(unc_path, **kwargs):
        return real_connect(str(local_db), **kwargs)

    monkeypatch.setattr("src.database.connection.sqlite3.connect", fake_connect)

    db = DatabaseConnection(cfg)
    conn = db.get_connection()

    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 30000
    assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2


def test_first_init_without_config_raises(tmp_path):
    """Construtor sem DBConfig na primeira chamada deve levantar RuntimeError."""
    with pytest.raises(RuntimeError, match="DBConfig"):
        DatabaseConnection()


def test_subsequent_init_without_config_returns_existing(tmp_path, monkeypatch):
    """Após inicializado, chamadas extras de DatabaseConnection() retornam o mesmo singleton."""
    cfg = _make_config(tmp_path)
    local_db = tmp_path / "actual.db"
    real_connect = sqlite3.connect
    monkeypatch.setattr(
        "src.database.connection.sqlite3.connect",
        lambda unc_path, **kw: real_connect(str(local_db), **kw),
    )

    first = DatabaseConnection(cfg)
    second = DatabaseConnection()
    assert first is second
    assert second.get_connection() is first.get_connection()


def test_close_resets_singleton(tmp_path, monkeypatch):
    """close() deve permitir nova inicialização com config diferente."""
    cfg = _make_config(tmp_path)
    local_db = tmp_path / "actual.db"
    real_connect = sqlite3.connect
    monkeypatch.setattr(
        "src.database.connection.sqlite3.connect",
        lambda unc_path, **kw: real_connect(str(local_db), **kw),
    )

    first = DatabaseConnection(cfg)
    first.close()

    # Após close(), uma nova chamada deve aceitar/exigir DBConfig novamente.
    with pytest.raises(RuntimeError, match="DBConfig"):
        DatabaseConnection()


def test_unable_to_open_wraps_error(tmp_path, monkeypatch):
    """sqlite3.OperationalError 'unable to open' → DatabaseConnectionError amigável."""
    cfg = _make_config(tmp_path)

    def raising_connect(unc_path, **kwargs):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr("src.database.connection.sqlite3.connect", raising_connect)

    with pytest.raises(DatabaseConnectionError, match="Não foi possível abrir"):
        DatabaseConnection(cfg)


def test_locked_error_wraps_error(tmp_path, monkeypatch):
    """sqlite3.OperationalError 'database is locked' → DatabaseConnectionError amigável."""
    cfg = _make_config(tmp_path)

    def raising_connect(unc_path, **kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("src.database.connection.sqlite3.connect", raising_connect)

    with pytest.raises(DatabaseConnectionError, match="bloqueado"):
        DatabaseConnection(cfg)
