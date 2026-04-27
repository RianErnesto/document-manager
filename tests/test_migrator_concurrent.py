"""Testes do Migrator com cenários de concorrência simulada."""
import sqlite3

import pytest

from src.database.migrator import Migrator


def _setup_conn():
    """Conexão in-memory com row_factory e busy_timeout configurado."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def test_migrator_runs_pending_migrations(monkeypatch, tmp_path):
    """Migrator descobre e aplica migrations pendentes em ordem."""
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()
    (mig_dir / "001_first.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('CREATE TABLE foo (id INTEGER)')\n"
    )
    (mig_dir / "002_second.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('CREATE TABLE bar (id INTEGER)')\n"
    )

    monkeypatch.setattr(Migrator, "MIGRATIONS_DIR", mig_dir)

    conn = _setup_conn()
    Migrator(conn).run()

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "foo" in tables
    assert "bar" in tables

    versions = {r[0] for r in conn.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall()}
    assert versions == {"001", "002"}


def test_migrator_skips_already_applied(monkeypatch, tmp_path):
    """Se a versão já está em schema_migrations, não roda de novo."""
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()
    (mig_dir / "001_only.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('CREATE TABLE only_once (id INTEGER)')\n"
    )

    monkeypatch.setattr(Migrator, "MIGRATIONS_DIR", mig_dir)

    conn = _setup_conn()
    conn.execute("""
        CREATE TABLE schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO schema_migrations (version, name) VALUES ('001', 'only')")
    conn.commit()

    Migrator(conn).run()

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "only_once" not in tables


def test_migrator_double_check_after_lock(monkeypatch, tmp_path):
    """Simula 'outro processo aplicou enquanto esperávamos lock'.

    O migrator real adquire BEGIN IMMEDIATE e RELÊ schema_migrations. Aqui
    interceptamos o ponto de releitura pra fingir que outro processo aplicou
    a versão antes de a gente conseguir o lock.
    """
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()
    (mig_dir / "003_concurrent.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('CREATE TABLE concurrent_table (id INTEGER)')\n"
    )

    monkeypatch.setattr(Migrator, "MIGRATIONS_DIR", mig_dir)

    conn = _setup_conn()
    migrator = Migrator(conn)

    def fake_get_applied():
        return {"003"}

    monkeypatch.setattr(migrator, "_get_applied_versions", fake_get_applied)

    migrator.run()

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "concurrent_table" not in tables


def test_migrator_rolls_back_on_failure(monkeypatch, tmp_path):
    """Se uma migration falha, todo o sweep da transação volta atrás."""
    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()
    (mig_dir / "004_good.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('CREATE TABLE good_table (id INTEGER)')\n"
    )
    (mig_dir / "005_bad.py").write_text(
        "def up(cursor):\n"
        "    cursor.execute('THIS IS NOT VALID SQL')\n"
    )

    monkeypatch.setattr(Migrator, "MIGRATIONS_DIR", mig_dir)

    conn = _setup_conn()
    with pytest.raises(sqlite3.OperationalError):
        Migrator(conn).run()

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "good_table" not in tables
    versions = {r[0] for r in conn.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall()}
    assert versions == set()
