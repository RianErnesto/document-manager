"""Testes do BackupService."""
import os
import time
from pathlib import Path

import pytest

from src.database.db_config import DBConfig
from src.services.backup_service import BackupResult, BackupService


def _make_config(tmp_path, interval_h=24, retention_d=30, filename="documents.db"):
    return DBConfig(
        server="x",
        share="y",
        filename=filename,
        user="u",
        password="p",
        backup_dir=str(tmp_path / "backups"),
        backup_interval_hours=interval_h,
        backup_retention_days=retention_d,
    )


def test_creates_backup_when_dir_empty(file_db, tmp_path):
    conn, _ = file_db
    config = _make_config(tmp_path)
    svc = BackupService(conn, config)

    result = svc.maybe_backup()

    assert result.status == "CREATED"
    backups = list(Path(config.backup_dir).glob("documents-*.db"))
    assert len(backups) == 1


def test_skips_when_recent_backup_exists(file_db, tmp_path):
    conn, _ = file_db
    config = _make_config(tmp_path, interval_h=24)
    backup_dir = Path(config.backup_dir)
    backup_dir.mkdir(parents=True)

    # Cria um backup "recente" (mtime = agora)
    recent = backup_dir / "documents-2026-04-27_120000.db"
    recent.write_bytes(b"fake")

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "SKIPPED_RECENT"
    # Não criou novo
    assert len(list(backup_dir.glob("documents-*.db"))) == 1


def test_creates_when_recent_is_older_than_interval(file_db, tmp_path):
    conn, _ = file_db
    config = _make_config(tmp_path, interval_h=24)
    backup_dir = Path(config.backup_dir)
    backup_dir.mkdir(parents=True)

    old = backup_dir / "documents-2026-04-25_120000.db"
    old.write_bytes(b"fake")
    # Forçar mtime pra 30h atrás
    past = time.time() - 30 * 3600
    os.utime(old, (past, past))

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "CREATED"
    assert len(list(backup_dir.glob("documents-*.db"))) == 2


def test_retention_deletes_old_backups(file_db, tmp_path):
    conn, _ = file_db
    config = _make_config(tmp_path, interval_h=24, retention_d=7)
    backup_dir = Path(config.backup_dir)
    backup_dir.mkdir(parents=True)

    # Backup com 10 dias
    old = backup_dir / "documents-2026-04-17_000000.db"
    old.write_bytes(b"fake")
    past = time.time() - 10 * 86400
    os.utime(old, (past, past))

    # Backup com 3 dias (dentro da retenção)
    keep = backup_dir / "documents-2026-04-24_000000.db"
    keep.write_bytes(b"fake")
    near = time.time() - 3 * 86400
    os.utime(keep, (near, near))

    svc = BackupService(conn, config)
    svc.maybe_backup()

    remaining = sorted(p.name for p in backup_dir.glob("documents-*.db"))
    assert "documents-2026-04-17_000000.db" not in remaining
    assert "documents-2026-04-24_000000.db" in remaining


def test_failure_returns_failed_does_not_raise(file_db, tmp_path, mocker):
    conn, _ = file_db
    config = _make_config(tmp_path)
    # Força erro no makedirs
    mocker.patch("os.makedirs", side_effect=PermissionError("denied"))

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "FAILED"
    assert result.message  # tem alguma mensagem


def test_backup_filename_uses_db_filename_basename(file_db, tmp_path):
    """Se DB_FILENAME=foo.db, backups devem se chamar foo-*.db."""
    conn, _ = file_db
    config = _make_config(tmp_path, filename="foo.db")
    svc = BackupService(conn, config)
    svc.maybe_backup()

    backups = list((tmp_path / "backups").glob("foo-*.db"))
    assert len(backups) == 1


def test_atomic_rename_uses_tmp_then_replace(file_db, tmp_path, mocker):
    """A cópia vai pra .tmp e depois é renomeada — verificamos via os.replace."""
    conn, _ = file_db
    config = _make_config(tmp_path)
    spy = mocker.spy(os, "replace")

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "CREATED"
    assert spy.called
    src = spy.call_args.args[0]
    dst = spy.call_args.args[1]
    assert str(src).endswith(".tmp")
    assert str(dst).endswith(".db")


def test_glob_does_not_match_tmp_files(file_db, tmp_path):
    """Regressão: o glob 'prefix-*.db' não deve casar com '.db.tmp' órfãos.

    Se acidentalmente casasse, o throttle confundiria um .tmp velho de uma
    execução abortada com um backup recente e pularia o backup pra sempre.
    """
    conn, _ = file_db
    config = _make_config(tmp_path, interval_h=24)
    backup_dir = Path(config.backup_dir)
    backup_dir.mkdir(parents=True)

    # .tmp órfão de execução abortada, mtime AGORA
    orphan = backup_dir / "documents-2026-04-27_120000.db.tmp"
    orphan.write_bytes(b"orphan tmp")

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    # Deve ter criado um backup (.tmp órfão NÃO deve contar como recente).
    assert result.status == "CREATED"


def test_failed_replace_cleans_up_tmp(file_db, tmp_path, mocker):
    """Se os.replace falhar, o .tmp criado deve ser limpo pra não vazar."""
    conn, _ = file_db
    config = _make_config(tmp_path)

    mocker.patch("os.replace", side_effect=OSError("destination locked"))

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "FAILED"
    # Não deve haver .tmp órfão
    leftover_tmps = list(Path(config.backup_dir).glob("*.tmp"))
    assert leftover_tmps == []


def test_failed_message_is_truncated_and_typed(file_db, tmp_path, mocker):
    """FAILED.message inclui tipo da exceção e trunca strings longas."""
    conn, _ = file_db
    config = _make_config(tmp_path)
    long_msg = "x" * 500
    mocker.patch("os.makedirs", side_effect=PermissionError(long_msg))

    svc = BackupService(conn, config)
    result = svc.maybe_backup()

    assert result.status == "FAILED"
    assert result.message.startswith("PermissionError:")
    assert len(result.message) < 300
