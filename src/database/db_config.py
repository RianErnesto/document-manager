"""Configuração de conexão de banco de dados via .env."""
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values


class ConfigError(Exception):
    """Erro de configuração — variável obrigatória ausente ou inválida."""


@dataclass(frozen=True)
class DBConfig:
    """Configuração imutável de conexão com o banco de dados em rede."""

    server: str
    share: str
    filename: str
    user: str
    password: str
    backup_dir: str
    backup_interval_hours: int
    backup_retention_days: int

    @property
    def unc_share(self) -> str:
        """Retorna \\\\server\\share."""
        return rf"\\{self.server}\{self.share}"

    @property
    def unc_path(self) -> str:
        """Retorna \\\\server\\share\\filename."""
        return rf"{self.unc_share}\{self.filename}"


REQUIRED_VARS = ["DB_SERVER", "DB_SHARE", "DB_FILENAME", "DB_USER", "DB_PASSWORD"]


def _default_env_path() -> Path:
    """Retorna o caminho do .env: ao lado do .exe (frozen) ou raiz do projeto (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / ".env"
    return Path(__file__).parent.parent.parent / ".env"


def load_db_config(env_path: Optional[Path] = None) -> DBConfig:
    """Carrega .env e retorna DBConfig validado.

    Lança ConfigError se .env não existe ou se faltar variável obrigatória.
    """
    path = env_path if env_path is not None else _default_env_path()

    if not path.exists():
        raise ConfigError(
            f"Arquivo .env não encontrado em {path}. "
            "Crie um .env baseado em .env.example."
        )

    values = dotenv_values(path)

    missing = [v for v in REQUIRED_VARS if not values.get(v)]
    if missing:
        raise ConfigError(
            f"Variáveis obrigatórias ausentes no .env: {', '.join(missing)}"
        )

    try:
        interval = int(values.get("BACKUP_INTERVAL_HOURS") or "24")
        retention = int(values.get("BACKUP_RETENTION_DAYS") or "30")
    except ValueError as e:
        raise ConfigError(
            f"BACKUP_INTERVAL_HOURS e BACKUP_RETENTION_DAYS devem ser inteiros: {e}"
        ) from e

    return DBConfig(
        server=values["DB_SERVER"],
        share=values["DB_SHARE"],
        filename=values["DB_FILENAME"],
        user=values["DB_USER"],
        password=values["DB_PASSWORD"],
        backup_dir=values.get("BACKUP_DIR") or r"C:\CPD\Backups",
        backup_interval_hours=interval,
        backup_retention_days=retention,
    )
