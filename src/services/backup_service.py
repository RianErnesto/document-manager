"""Backup automático do SQLite via API online (sqlite3.Connection.backup).

Throttle: pula se o backup mais recente em BACKUP_DIR é mais novo que
BACKUP_INTERVAL_HOURS. Retenção: apaga backups com mtime > BACKUP_RETENTION_DAYS.

Falha NUNCA propaga — sempre retorna BackupResult, loga warning, e segue.
"""
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..database.db_config import DBConfig


@dataclass(frozen=True)
class BackupResult:
    """Resultado de uma tentativa de backup."""

    # Constantes pros valores válidos de `status` — consumidores comparam
    # contra estas em vez de strings literais, evitando typo-bugs silenciosos.
    STATUS_CREATED = "CREATED"
    STATUS_SKIPPED_RECENT = "SKIPPED_RECENT"
    STATUS_FAILED = "FAILED"

    status: str  # uma das três STATUS_* acima
    message: Optional[str] = None
    path: Optional[str] = None


def _safe_error(e: Exception, max_len: int = 200) -> str:
    """Formata uma exceção pra mensagem de log/UI sem propagar tudo cru.

    - Prefixa com tipo da exceção pra debug.
    - Trunca em max_len chars caso stderr/path seja gigante.
    """
    msg = str(e)
    if len(msg) > max_len:
        msg = msg[:max_len] + "..."
    return f"{type(e).__name__}: {msg}"


class BackupService:
    """Backup automático do banco via API online do sqlite3."""

    def __init__(self, source_conn: sqlite3.Connection, config: DBConfig):
        self._source = source_conn
        self._config = config

    def maybe_backup(self) -> BackupResult:
        """Faz backup se o último for mais antigo que interval. Limpa retenção.
        Nunca lança — todo erro vira BackupResult(status="FAILED", ...).
        """
        # Outer try: makedirs precisa ter sucesso pra qualquer trabalho prosseguir.
        try:
            backup_dir = Path(self._config.backup_dir)
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            return BackupResult(status=BackupResult.STATUS_FAILED, message=_safe_error(e))

        # Inner try: depois que o diretório existe, qualquer falha é recuperável
        # numa próxima execução; queremos cleanup mesmo no caminho SKIPPED.
        try:
            if self._has_recent_backup(backup_dir):
                self._cleanup_old(backup_dir)
                return BackupResult(
                    status=BackupResult.STATUS_SKIPPED_RECENT,
                    message=f"Último backup há menos de {self._config.backup_interval_hours}h",
                )

            backup_path = self._do_backup(backup_dir)
            self._cleanup_old(backup_dir)
            return BackupResult(
                status=BackupResult.STATUS_CREATED,
                message=f"Backup criado em {backup_path.name}",
                path=str(backup_path),
            )
        except Exception as e:
            return BackupResult(status=BackupResult.STATUS_FAILED, message=_safe_error(e))

    def _basename(self) -> str:
        """Prefixo do backup, derivado de DB_FILENAME sem a extensão."""
        return Path(self._config.filename).stem

    def _has_recent_backup(self, backup_dir: Path) -> bool:
        cutoff = time.time() - self._config.backup_interval_hours * 3600
        prefix = self._basename()
        for f in backup_dir.glob(f"{prefix}-*.db"):
            if f.stat().st_mtime >= cutoff:
                return True
        return False

    def _do_backup(self, backup_dir: Path) -> Path:
        prefix = self._basename()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        final_path = backup_dir / f"{prefix}-{timestamp}.db"
        tmp_path = backup_dir / f"{prefix}-{timestamp}.db.tmp"

        # Cópia online página-por-página (segura mesmo com escritas concorrentes).
        # No Windows, o connection precisa ser fechado explicitamente antes do rename
        # — o "with" do sqlite3 só faz commit/rollback, não close.
        target = sqlite3.connect(str(tmp_path))
        try:
            self._source.backup(target)
        finally:
            target.close()

        # Rename atômico — garante que o .db nunca exista parcial no diretório.
        # Se o rename falhar (destino bloqueado, perm flip mid-run), apaga o .tmp
        # pra não acumular órfãos numa share SMB instável.
        try:
            os.replace(str(tmp_path), str(final_path))
        except OSError:
            try:
                tmp_path.unlink(missing_ok=True)
            finally:
                raise
        return final_path

    def _cleanup_old(self, backup_dir: Path) -> None:
        cutoff = time.time() - self._config.backup_retention_days * 86400
        prefix = self._basename()
        for f in backup_dir.glob(f"{prefix}-*.db"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                continue  # falha individual de delete não é fatal
