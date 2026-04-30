import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "sync_local_to_server.py"


@pytest.fixture
def sync_module():
    spec = importlib.util.spec_from_file_location("sync_local_to_server", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_db_with_schema(path, columns):
    conn = sqlite3.connect(str(path))
    cols_sql = ", ".join(f"{c} TEXT" for c in columns)
    conn.execute(f"CREATE TABLE documents (id INTEGER PRIMARY KEY, {cols_sql})")
    conn.commit()
    conn.close()


def test_validate_source_schema_passes_when_all_columns_present(tmp_path, sync_module):
    db = tmp_path / "src.db"
    _make_db_with_schema(db, sync_module.BUSINESS_COLUMNS)
    sync_module.validate_source_schema(db)


def test_validate_source_schema_fails_when_process_missing(tmp_path, sync_module):
    db = tmp_path / "src.db"
    _make_db_with_schema(db, [c for c in sync_module.BUSINESS_COLUMNS if c != "process"])
    with pytest.raises(SystemExit, match="process"):
        sync_module.validate_source_schema(db)


def test_validate_source_schema_fails_when_table_missing(tmp_path, sync_module):
    db = tmp_path / "src.db"
    sqlite3.connect(str(db)).close()
    with pytest.raises(SystemExit, match="documents"):
        sync_module.validate_source_schema(db)


def test_sync_logger_writes_to_file_and_stdout(tmp_path, sync_module, capsys):
    log_dir = tmp_path / "logs"
    with sync_module.SyncLogger(log_dir) as logger:
        logger.info("ola mundo")
        logger.warn("alerta")

    log_files = list(log_dir.glob("sync_*.log"))
    assert len(log_files) == 1
    content = log_files[0].read_text(encoding="utf-8")
    assert "[INFO] ola mundo" in content
    assert "[WARN] alerta" in content

    captured = capsys.readouterr()
    assert "[INFO] ola mundo" in captured.out
    assert "[WARN] alerta" in captured.out


def test_sync_logger_creates_dir_if_missing(tmp_path, sync_module):
    log_dir = tmp_path / "deeply" / "nested" / "logs"
    with sync_module.SyncLogger(log_dir) as logger:
        logger.info("x")
    assert log_dir.is_dir()
    assert len(list(log_dir.glob("sync_*.log"))) == 1


def _make_full_schema_db(path):
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT NOT NULL UNIQUE,
            shelf INTEGER NOT NULL,
            box INTEGER NOT NULL,
            rack INTEGER NOT NULL,
            classification TEXT NOT NULL DEFAULT '',
            process TEXT NOT NULL DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


@pytest.fixture
def silent_logger():
    class _NullLogger:
        def info(self, msg): pass
        def warn(self, msg): pass
    return _NullLogger()


@pytest.fixture
def db_pair(tmp_path):
    src_path = tmp_path / "src.db"
    dst_path = tmp_path / "dst.db"
    src_conn = _make_full_schema_db(src_path)
    dst_conn = _make_full_schema_db(dst_path)
    src_conn.row_factory = sqlite3.Row
    dst_conn.row_factory = sqlite3.Row
    yield src_conn, dst_conn
    src_conn.close()
    dst_conn.close()


def _insert_doc(conn, qr_code, shelf=1, box=1, rack=1, classification="A", process="2025/00001"):
    conn.execute(
        "INSERT INTO documents (qr_code, shelf, box, rack, classification, process) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (qr_code, shelf, box, rack, classification, process),
    )
    conn.commit()


def test_sync_inserts_new_rows(sync_module, db_pair, silent_logger):
    src, dst = db_pair
    _insert_doc(src, "DOC001")
    _insert_doc(src, "DOC002")

    counters = sync_module.sync_rows(src, dst, force=False, logger=silent_logger)

    assert counters == {"inserted": 2, "same": 0, "conflict": 0, "overwritten": 0}
    rows = dst.execute("SELECT qr_code FROM documents ORDER BY qr_code").fetchall()
    assert [r["qr_code"] for r in rows] == ["DOC001", "DOC002"]


def test_sync_skips_identical_rows(sync_module, db_pair, silent_logger):
    src, dst = db_pair
    _insert_doc(src, "DOC001", shelf=5)
    _insert_doc(dst, "DOC001", shelf=5)

    counters = sync_module.sync_rows(src, dst, force=False, logger=silent_logger)

    assert counters == {"inserted": 0, "same": 1, "conflict": 0, "overwritten": 0}


def test_sync_conflict_default_keeps_server(sync_module, db_pair, silent_logger):
    src, dst = db_pair
    _insert_doc(src, "DOC001", shelf=5)
    _insert_doc(dst, "DOC001", shelf=7)

    counters = sync_module.sync_rows(src, dst, force=False, logger=silent_logger)

    assert counters == {"inserted": 0, "same": 0, "conflict": 1, "overwritten": 0}
    row = dst.execute("SELECT shelf FROM documents WHERE qr_code = 'DOC001'").fetchone()
    assert row["shelf"] == 7


def test_sync_conflict_force_overwrites_server(sync_module, db_pair, silent_logger):
    src, dst = db_pair
    _insert_doc(src, "DOC001", shelf=5)
    _insert_doc(dst, "DOC001", shelf=7)

    counters = sync_module.sync_rows(src, dst, force=True, logger=silent_logger)

    assert counters == {"inserted": 0, "same": 0, "conflict": 0, "overwritten": 1}
    row = dst.execute("SELECT shelf FROM documents WHERE qr_code = 'DOC001'").fetchone()
    assert row["shelf"] == 5


def test_sync_empty_source_returns_zero_counters(sync_module, db_pair, silent_logger):
    src, dst = db_pair
    counters = sync_module.sync_rows(src, dst, force=False, logger=silent_logger)
    assert counters == {"inserted": 0, "same": 0, "conflict": 0, "overwritten": 0}
