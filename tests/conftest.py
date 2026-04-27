"""Fixtures compartilhadas entre testes."""
import sqlite3

import pytest


@pytest.fixture
def tmp_env_file(tmp_path):
    """Cria um caminho de .env temporário (não cria o arquivo, só retorna o Path)."""
    return tmp_path / ".env"


@pytest.fixture
def in_memory_db():
    """Conexão SQLite in-memory para testes de migrator/backup."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def file_db(tmp_path):
    """Conexão SQLite em arquivo temporário (para backup que precisa de arquivo real)."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Marca o arquivo como não-vazio sem assumir um schema específico —
    # consumidores que precisarem de tabelas devem criá-las no próprio teste.
    conn.execute("PRAGMA user_version = 1")
    conn.commit()
    yield conn, db_path
    conn.close()
