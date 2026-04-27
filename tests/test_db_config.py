"""Testes do loader de configuração de banco de dados."""
import pytest

from src.database.db_config import DBConfig, ConfigError, load_db_config


def test_load_db_config_happy_path(tmp_env_file):
    """Carrega .env válido e retorna DBConfig com todos os campos."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=secret\n"
    )
    config = load_db_config(env_path=tmp_env_file)

    assert config.server == "192.168.3.180"
    assert config.share == "BKP-Semas"
    assert config.filename == "documents.db"
    assert config.user == "admin"
    assert config.password == "secret"
    # Defaults aplicados
    assert config.backup_dir == r"C:\CPD\Backups"
    assert config.backup_interval_hours == 24
    assert config.backup_retention_days == 30


def test_unc_path_property(tmp_env_file):
    """unc_path monta \\\\server\\share\\filename corretamente."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
    )
    config = load_db_config(env_path=tmp_env_file)
    assert config.unc_path == r"\\192.168.3.180\BKP-Semas\documents.db"


def test_unc_share_property(tmp_env_file):
    """unc_share monta \\\\server\\share (sem filename)."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
    )
    config = load_db_config(env_path=tmp_env_file)
    assert config.unc_share == r"\\192.168.3.180\BKP-Semas"


def test_missing_required_var_raises_config_error(tmp_env_file):
    """Faltar uma variável obrigatória → ConfigError com nome da variável."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        # DB_USER ausente
        "DB_PASSWORD=x\n"
    )
    with pytest.raises(ConfigError, match="DB_USER"):
        load_db_config(env_path=tmp_env_file)


def test_empty_value_treated_as_missing(tmp_env_file):
    """Variável presente mas vazia conta como ausente."""
    tmp_env_file.write_text(
        "DB_SERVER=\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
    )
    with pytest.raises(ConfigError, match="DB_SERVER"):
        load_db_config(env_path=tmp_env_file)


def test_env_file_not_found(tmp_path):
    """Arquivo .env inexistente → ConfigError descritivo."""
    nonexistent = tmp_path / "nope.env"
    with pytest.raises(ConfigError, match="não encontrado"):
        load_db_config(env_path=nonexistent)


def test_backup_defaults_applied_when_omitted(tmp_env_file):
    """Sem BACKUP_*, defaults são aplicados."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
    )
    config = load_db_config(env_path=tmp_env_file)
    assert config.backup_dir == r"C:\CPD\Backups"
    assert config.backup_interval_hours == 24
    assert config.backup_retention_days == 30


def test_backup_overrides_respected(tmp_env_file):
    """BACKUP_* presentes no .env têm precedência sobre os defaults."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
        "BACKUP_DIR=D:\\custom\\backup\n"
        "BACKUP_INTERVAL_HOURS=12\n"
        "BACKUP_RETENTION_DAYS=7\n"
    )
    config = load_db_config(env_path=tmp_env_file)
    assert config.backup_dir == r"D:\custom\backup"
    assert config.backup_interval_hours == 12
    assert config.backup_retention_days == 7


def test_invalid_int_in_backup_var_raises_config_error(tmp_env_file):
    """BACKUP_INTERVAL_HOURS não-numérico → ConfigError, não ValueError."""
    tmp_env_file.write_text(
        "DB_SERVER=192.168.3.180\n"
        "DB_SHARE=BKP-Semas\n"
        "DB_FILENAME=documents.db\n"
        "DB_USER=admin\n"
        "DB_PASSWORD=x\n"
        "BACKUP_INTERVAL_HOURS=abc\n"
    )
    with pytest.raises(ConfigError, match="inteiros"):
        load_db_config(env_path=tmp_env_file)
