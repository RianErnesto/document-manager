"""
Ponto de entrada da aplicação Document Manager.
"""
import sys
import os

# Adiciona o diretório src ao path para importações
if getattr(sys, 'frozen', False):
    # Executável PyInstaller
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    # Desenvolvimento
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import App


def main():
    """Função principal."""
    app = App()
    if not app.initialized_ok():
        # Backend de banco falhou no startup; o modal de erro já foi mostrado
        # e a janela já foi destruída. Saída limpa sem entrar no mainloop.
        return
    app.run()


if __name__ == "__main__":
    main()
