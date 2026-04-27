"""Testes do NetworkShareAuthenticator (subprocess mockado)."""
from unittest.mock import MagicMock

import pytest

from src.database.network_share import (
    AuthenticationError,
    NetworkShareAuthenticator,
    NetworkShareError,
    ServerUnreachableError,
    ShareNotFoundError,
)


def _mock_run(returncode: int, stderr: str = ""):
    """Helper pra construir um CompletedProcess mockado."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stderr = stderr
    mock.stdout = ""
    return mock


def test_connect_success(mocker):
    """Exit code 0 → sem exceção."""
    mock_run = mocker.patch(
        "src.database.network_share.subprocess.run",
        return_value=_mock_run(0),
    )
    auth = NetworkShareAuthenticator(
        server="192.168.3.180",
        share="BKP-Semas",
        user="admin",
        password="secret",
    )
    auth.connect()

    # Deve ter chamado net use /delete (ignorando falha) e depois net use com creds
    assert mock_run.call_count == 2
    auth_call = mock_run.call_args_list[1]
    cmd = auth_call.args[0]
    assert "net" in cmd[0].lower()
    assert "/user:admin" in cmd
    assert "secret" in cmd


def test_unc_share_property():
    auth = NetworkShareAuthenticator(
        server="192.168.3.180", share="BKP-Semas", user="admin", password="x"
    )
    assert auth.unc_share == r"\\192.168.3.180\BKP-Semas"


def _make_auth():
    return NetworkShareAuthenticator(
        server="192.168.3.180", share="BKP-Semas", user="admin", password="secret"
    )


@pytest.mark.parametrize("code,exc_class", [
    (1326, AuthenticationError),
    (53, ServerUnreachableError),
    (67, ServerUnreachableError),
    (2250, ShareNotFoundError),
    (86, ShareNotFoundError),
    (9999, NetworkShareError),  # Código desconhecido → exceção base
])
def test_exit_code_maps_to_exception(mocker, code, exc_class):
    """Cada exit code conhecido vira a exceção tipada correta."""
    # Primeira call (delete) ignorada; segunda (auth) retorna erro
    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=[_mock_run(0), _mock_run(code, stderr="some error")],
    )
    auth = _make_auth()
    with pytest.raises(exc_class):
        auth.connect()


def test_password_never_in_exception_message(mocker):
    """Senha jamais aparece na mensagem da exceção propagada."""
    stderr_with_secret = "command failed: net use ... secret /persistent:no"
    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=[_mock_run(0), _mock_run(9999, stderr=stderr_with_secret)],
    )
    auth = _make_auth()
    with pytest.raises(NetworkShareError) as exc_info:
        auth.connect()
    assert "secret" not in str(exc_info.value)


def test_disconnect_silences_failure(mocker):
    """disconnect() não propaga exceção mesmo se subprocess falhar."""
    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=Exception("boom"),
    )
    auth = _make_auth()
    auth.disconnect()  # não levanta


def test_connect_attempts_cleanup_first(mocker):
    """Primeira chamada de subprocess deve ser /delete; segunda é a auth."""
    mock_run = mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=[_mock_run(0), _mock_run(0)],
    )
    auth = _make_auth()
    auth.connect()

    delete_call = mock_run.call_args_list[0]
    assert "/delete" in delete_call.args[0]
    auth_call = mock_run.call_args_list[1]
    assert "/delete" not in auth_call.args[0]
    assert "/user:admin" in auth_call.args[0]


def test_connect_timeout_raises_server_unreachable(mocker):
    """Timeout na chamada de auth → ServerUnreachableError, não cria deadlock."""
    import subprocess

    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=[
            _mock_run(0),  # delete OK
            subprocess.TimeoutExpired(cmd="net use", timeout=30),
        ],
    )
    auth = _make_auth()
    with pytest.raises(ServerUnreachableError, match="Timeout"):
        auth.connect()


def test_connect_when_net_exe_missing(mocker):
    """FileNotFoundError em net.exe → NetworkShareError tipado."""
    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=FileNotFoundError("'net' not found"),
    )
    auth = _make_auth()
    with pytest.raises(NetworkShareError, match="net.exe"):
        auth.connect()


def test_generic_failure_message_does_not_leak_stderr(mocker):
    """Pra exit code desconhecido, mensagem nunca inclui stderr (mesmo se 'limpo')."""
    stderr_with_creds = "auth failed for admin with secret"
    mocker.patch(
        "src.database.network_share.subprocess.run",
        side_effect=[_mock_run(0), _mock_run(9999, stderr=stderr_with_creds)],
    )
    auth = _make_auth()
    with pytest.raises(NetworkShareError) as exc_info:
        auth.connect()
    msg = str(exc_info.value)
    assert "secret" not in msg
    assert "admin" not in msg
    assert "9999" in msg  # mas ainda mostra o código pra debug
