"""
Ponto de entrada da aplicação Document Manager.
"""
import sys
import os
import traceback
from datetime import datetime

# Adiciona o diretório src ao path para importações
if getattr(sys, 'frozen', False):
    # Executável PyInstaller
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    # Desenvolvimento
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _write_crash_log(exc_text: str) -> None:
    """Escreve crash em C:\\CPD\\Logs\\crash.log mesmo se console estiver suprimido.

    Útil pra debugar build PyInstaller com console=False onde stderr some.
    """
    try:
        log_dir = r"C:\CPD\Logs"
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(log_dir, "crash.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{ts}] ============ CRASH ============\n")
            f.write(exc_text)
            f.write("\n")
    except Exception:
        pass  # último recurso silencioso


def main():
    """Função principal."""
    try:
        from src.app import App
        app = App()
        if not app.initialized_ok():
            # Backend falhou; modal já mostrado e janela já destruída.
            return
        app.run()
    except Exception:
        _write_crash_log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
