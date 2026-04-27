"""
Sistema de migrations para o banco de dados SQLite.

Escaneia arquivos NNN_descricao.py em src/database/migrations/,
compara com o que já foi aplicado (tabela schema_migrations)
e executa os pendentes em ordem.
"""
import re
import sqlite3
from pathlib import Path

from ..services.audit_service import AuditLogger


class Migrator:
    """Executa migrations pendentes no banco de dados."""

    MIGRATIONS_DIR = Path(__file__).parent / "migrations"

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection
        self._logger = AuditLogger()
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
        """Executa todas as migrations pendentes em ordem (concorrência-safe).

        Adquire lock exclusivo de escrita via BEGIN IMMEDIATE. Espera até
        busy_timeout (configurado na connection) caso outro processo tenha lock.
        Após adquirir, RELÊ schema_migrations — outro processo pode ter
        aplicado entre o nosso `_ensure_migrations_table` e a entrada no lock.
        """
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            applied = self._get_applied_versions()
            migrations = self._discover_migrations()

            pending = [(v, n, p) for v, n, p in migrations if v not in applied]
            if not pending:
                self._logger.info(
                    f"Nenhuma migration pendente (aplicadas: {len(applied)})"
                )
                self._conn.commit()
                return

            for version, name, path in pending:
                self._apply_migration(version, name, path)

            self._conn.commit()
        except Exception as e:
            try:
                self._conn.rollback()
            except sqlite3.Error:
                pass  # rollback é no-op se BEGIN nunca completou
            self._logger.critical(f"Erro durante migration sweep: {e}")
            raise

    def _apply_migration(self, version: str, name: str, path):
        """Carrega o módulo e executa up() + INSERT em schema_migrations.

        Não comita — quem chama é responsável pelo commit/rollback do sweep todo.
        """
        import importlib.util

        module_name = f"src.database.migrations.{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cursor = self._conn.cursor()
        module.up(cursor)
        cursor.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
            (version, name),
        )
        self._logger.info(f"Migration aplicada: {version}_{name}")
