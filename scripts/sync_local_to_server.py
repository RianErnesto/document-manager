import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values

from src.database.db_config import load_db_config, ConfigError
from src.database.network_share import (
    NetworkShareAuthenticator,
    NetworkShareError,
)


BUSINESS_COLUMNS = ("qr_code", "shelf", "box", "rack", "classification", "process")
DEFAULT_LOG_DIR = r"C:\CPD\Logs"
COMMIT_INTERVAL = 100


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sincroniza um .db local com o banco em rede configurado no .env."
    )
    parser.add_argument(
        "source_db_path",
        type=Path,
        help="Caminho do .db local a ser consolidado",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Em conflito de qr_code, source sobrescreve servidor (default: servidor vence)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(DEFAULT_LOG_DIR),
        help=f"Diretório do log de execução (default: {DEFAULT_LOG_DIR})",
    )
    return parser.parse_args()


class SyncLogger:
    """Tee de prints pra stdout + arquivo de log timestamp'd em log_dir."""

    def __init__(self, log_dir: Path):
        self._log_dir = Path(log_dir)
        self._file = None
        self.path: Path | None = None

    def __enter__(self):
        self._log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.path = self._log_dir / f"sync_{ts}.log"
        self._file = open(self.path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write(self, level: str, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {message}"
        print(line)
        if self._file is not None:
            self._file.write(line + "\n")
            self._file.flush()

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def warn(self, message: str) -> None:
        self._write("WARN", message)


def validate_source_schema(source_path: Path) -> None:
    conn = sqlite3.connect(str(source_path))
    try:
        cursor = conn.execute("PRAGMA table_info(documents)")
        existing = {row[1] for row in cursor.fetchall()}
    finally:
        conn.close()

    if not existing:
        raise SystemExit(
            f"Source DB não tem tabela 'documents': {source_path}. "
            "Arquivo é um SQLite válido com schema compatível?"
        )

    missing = [c for c in BUSINESS_COLUMNS if c not in existing]
    if missing:
        raise SystemExit(
            f"Source DB tem schema antigo (faltam colunas: {', '.join(missing)}). "
            "Aplique migrations no source antes de sincronizar."
        )


def sync_rows(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    force: bool,
    logger,
) -> dict:
    cols_csv = ", ".join(BUSINESS_COLUMNS)
    placeholders = ", ".join(["?"] * len(BUSINESS_COLUMNS))
    insert_sql = f"INSERT INTO documents ({cols_csv}) VALUES ({placeholders})"
    update_sql = (
        "UPDATE documents SET "
        + ", ".join(f"{c} = ?" for c in BUSINESS_COLUMNS if c != "qr_code")
        + ", updated_at = CURRENT_TIMESTAMP WHERE qr_code = ?"
    )

    src_rows = src_conn.execute(f"SELECT {cols_csv} FROM documents").fetchall()
    total = len(src_rows)
    logger.info(f"Linhas no source: {total}")
    if total == 0:
        return {"inserted": 0, "same": 0, "conflict": 0, "overwritten": 0}

    counters = {"inserted": 0, "same": 0, "conflict": 0, "overwritten": 0}

    for idx, row in enumerate(src_rows, 1):
        qr = row["qr_code"]
        existing = dst_conn.execute(
            f"SELECT {cols_csv} FROM documents WHERE qr_code = ?",
            (qr,),
        ).fetchone()

        if existing is None:
            dst_conn.execute(insert_sql, tuple(row[c] for c in BUSINESS_COLUMNS))
            counters["inserted"] += 1
        else:
            same = all(row[c] == existing[c] for c in BUSINESS_COLUMNS)
            if same:
                counters["same"] += 1
            elif force:
                update_values = tuple(row[c] for c in BUSINESS_COLUMNS if c != "qr_code") + (qr,)
                dst_conn.execute(update_sql, update_values)
                counters["overwritten"] += 1
                logger.info(f"Sobrescrito qr_code={qr}")
            else:
                _log_conflict(logger, qr, row, existing)
                counters["conflict"] += 1

        if idx % COMMIT_INTERVAL == 0:
            dst_conn.commit()
            logger.info(f"Progresso: {idx}/{total}")

    dst_conn.commit()
    return counters


def _log_conflict(logger, qr, src_row, dst_row):
    src_repr = ", ".join(f"{c}={src_row[c]!r}" for c in BUSINESS_COLUMNS if c != "qr_code")
    dst_repr = ", ".join(f"{c}={dst_row[c]!r}" for c in BUSINESS_COLUMNS if c != "qr_code")
    logger.warn(
        f"Conflito qr_code={qr}\n"
        f"                              source:   {src_repr}\n"
        f"                              servidor: {dst_repr}\n"
        f"                              ação: mantido servidor (rode com -f pra sobrescrever)"
    )


def main():
    args = parse_args()

    if not args.source_db_path.exists():
        raise SystemExit(f"Banco de origem não existe: {args.source_db_path}")

    try:
        config = load_db_config()
    except ConfigError as e:
        raise SystemExit(f"Erro de configuração: {e}")

    validate_source_schema(args.source_db_path)

    started = time.monotonic()

    with SyncLogger(args.log_dir) as logger:
        mode = "source-wins (-f)" if args.force else "server-wins (default)"
        logger.info("=== Sync iniciado ===")
        logger.info(f"Source:  {args.source_db_path}")
        logger.info(f"Destino: {config.unc_path}")
        logger.info(f"Modo:    {mode}")
        logger.info(f"Schema do source validado: {len(BUSINESS_COLUMNS)} colunas OK")

        logger.info(f"Autenticando em {config.unc_share}...")
        auth = NetworkShareAuthenticator(
            server=config.server,
            share=config.share,
            user=config.user,
            password=config.password,
        )
        try:
            auth.connect()
        except NetworkShareError as e:
            logger.warn(f"Falha ao autenticar: {type(e).__name__}: {e}")
            raise SystemExit(1)
        logger.info("Conectado")

        src_conn = None
        dst_conn = None
        try:
            src_conn = sqlite3.connect(
                f"file:{args.source_db_path}?mode=ro",
                uri=True,
            )
            src_conn.row_factory = sqlite3.Row

            dst_conn = sqlite3.connect(
                config.unc_path,
                check_same_thread=False,
                timeout=30.0,
            )
            dst_conn.execute("PRAGMA busy_timeout = 30000")
            dst_conn.row_factory = sqlite3.Row

            counters = sync_rows(src_conn, dst_conn, force=args.force, logger=logger)

            elapsed = time.monotonic() - started
            logger.info("=== Resumo ===")
            logger.info(f"Total processado:  {sum(counters.values())}")
            logger.info(f"Inseridos:         {counters['inserted']}")
            logger.info(f"Idênticos (skip):  {counters['same']}")
            logger.info(f"Conflitos (skip):  {counters['conflict']}")
            logger.info(f"Sobrescritos:      {counters['overwritten']}")
            logger.info(f"Sync finalizado em {elapsed:.1f}s")
            logger.info(f"Log salvo em: {logger.path}")

        except KeyboardInterrupt:
            if dst_conn is not None:
                try:
                    dst_conn.rollback()
                except sqlite3.Error:
                    pass
            logger.warn("Sync abortado pelo usuário (Ctrl+C)")
            raise SystemExit(130)
        except sqlite3.OperationalError as e:
            if dst_conn is not None:
                try:
                    dst_conn.rollback()
                except sqlite3.Error:
                    pass
            logger.warn(f"Erro de banco durante sync: {e}")
            raise SystemExit(2)
        except Exception as e:
            if dst_conn is not None:
                try:
                    dst_conn.rollback()
                except sqlite3.Error:
                    pass
            logger.warn(f"Erro inesperado: {type(e).__name__}: {e}")
            raise
        finally:
            if src_conn is not None:
                try:
                    src_conn.close()
                except sqlite3.Error:
                    pass
            if dst_conn is not None:
                try:
                    dst_conn.close()
                except sqlite3.Error:
                    pass
            try:
                auth.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    main()
