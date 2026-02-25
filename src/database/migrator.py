"""
Sistema de migrations para o banco de dados SQLite.

Escaneia arquivos NNN_descricao.py em src/database/migrations/,
compara com o que já foi aplicado (tabela schema_migrations)
e executa os pendentes em ordem.
"""
import importlib
import re
import sqlite3
from pathlib import Path


class Migrator:
    """Executa migrations pendentes no banco de dados."""

    MIGRATIONS_DIR = Path(__file__).parent / "migrations"

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Cria a tabela de controle de migrations se não existir."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def _get_applied_versions(self) -> set[str]:
        """Retorna as versões já aplicadas."""
        cursor = self._conn.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}

    def _discover_migrations(self) -> list[tuple[str, str, Path]]:
        """
        Descobre arquivos de migration no diretório.
        Retorna lista de (version, name, path) ordenada por version.
        """
        pattern = re.compile(r"^(\d{3})_(.+)\.py$")
        migrations = []

        for file in sorted(self.MIGRATIONS_DIR.iterdir()):
            match = pattern.match(file.name)
            if match:
                version = match.group(1)
                name = match.group(2)
                migrations.append((version, name, file))

        return migrations

    def run(self):
        """Executa todas as migrations pendentes em ordem."""
        applied = self._get_applied_versions()
        migrations = self._discover_migrations()

        for version, name, path in migrations:
            if version in applied:
                continue

            module_name = f"src.database.migrations.{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            cursor = self._conn.cursor()
            try:
                module.up(cursor)
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (version, name),
                )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
