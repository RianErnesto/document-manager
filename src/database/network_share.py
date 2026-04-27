"""Autenticação no compartilhamento SMB via `net use`.

Não loga senha em hipótese alguma.
"""
import subprocess


# Hierarquia de exceções
class NetworkShareError(Exception):
    """Erro genérico ao autenticar/desconectar do compartilhamento."""


class AuthenticationError(NetworkShareError):
    """Usuário ou senha inválidos."""


class ServerUnreachableError(NetworkShareError):
    """Servidor não respondeu (rede caída, IP errado, máquina desligada)."""


class ShareNotFoundError(NetworkShareError):
    """Compartilhamento não existe no servidor."""


# Mapeamento de exit codes do `net use` para exceções tipadas.
# Referência: códigos NET HELPMSG (Windows).
_EXIT_CODE_MAP = {
    1326: AuthenticationError,    # Logon failure: unknown user name or bad password
    53: ServerUnreachableError,   # Network path was not found
    67: ServerUnreachableError,   # Network name cannot be found
    2250: ShareNotFoundError,     # Network connection does not exist
    86: ShareNotFoundError,       # Specified network password is not correct (raro)
}


# Flag para suprimir janela de console no Windows (subprocess sem CMD piscando).
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Timeout (em segundos) pra cada chamada de `net use`. Cobre lentidão de SMB
# sem travar o startup do app indefinidamente em rede meio-quebrada.
_SUBPROCESS_TIMEOUT = 30


class NetworkShareAuthenticator:
    """Garante que o compartilhamento SMB está autenticado antes do SQLite acessá-lo."""

    def __init__(self, server: str, share: str, user: str, password: str):
        self._server = server
        self._share = share
        self._user = user
        self._password = password

    @property
    def unc_share(self) -> str:
        """Retorna \\\\server\\share — sem nome de arquivo."""
        return rf"\\{self._server}\{self._share}"

    def connect(self) -> None:
        """Autentica no share. Lança subclasse de NetworkShareError em caso de falha.

        Antes de autenticar, remove qualquer mapeamento prévio (silencioso) pra evitar
        o erro 1219 (Multiple connections... are not allowed).
        """
        # 1. Limpa mapeamento prévio (best-effort, com timeout pra não travar)
        try:
            subprocess.run(
                ["net", "use", self.unc_share, "/delete", "/y"],
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            pass  # cleanup é best-effort
        except FileNotFoundError as e:
            raise NetworkShareError("net.exe não encontrado no PATH") from e

        # 2. Autentica
        try:
            result = subprocess.run(
                [
                    "net", "use", self.unc_share,
                    f"/user:{self._user}", self._password,
                    "/persistent:no",
                ],
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired as e:
            raise ServerUnreachableError(
                f"Timeout ao autenticar em {self.unc_share} "
                f"({_SUBPROCESS_TIMEOUT}s) — servidor pode estar inacessível"
            ) from e
        except FileNotFoundError as e:
            raise NetworkShareError("net.exe não encontrado no PATH") from e

        if result.returncode == 0:
            return

        exc_class = _EXIT_CODE_MAP.get(result.returncode, NetworkShareError)
        # NUNCA inclua self._password em mensagem ou stderr propagado
        raise exc_class(self._friendly_message(result.returncode))

    def disconnect(self) -> None:
        """Remove o mapeamento. Best-effort, silencia falha."""
        try:
            subprocess.run(
                ["net", "use", self.unc_share, "/delete", "/y"],
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except Exception:
            pass  # silencia: Windows limpa quando a sessão encerra

    def _friendly_message(self, code: int) -> str:
        """Mensagem amigável por código. NUNCA propaga stderr — o stderr do
        `net use` pode conter o password em casos exóticos, então pra códigos
        desconhecidos retornamos só uma mensagem genérica.
        """
        if code == 1326:
            return f"Usuário ou senha inválidos para {self.unc_share}"
        if code in (53, 67):
            return f"Servidor não respondeu: {self._server}"
        if code in (2250, 86):
            return f"Compartilhamento não existe: {self._share}"
        return f"Falha ao conectar (código {code}). Verifique os logs do sistema."
