"""
Script para gerar o executável da aplicação com PyInstaller.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """Limpa diretórios de build anteriores."""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Removendo diretório: {dir_name}")
            shutil.rmtree(dir_path)

    # Remove spec file
    spec_file = Path("DocumentManager.spec")
    if spec_file.exists():
        print("Removendo arquivo spec anterior")
        spec_file.unlink()


def build_exe():
    """Gera o executável."""
    print("=" * 50)
    print("DOCUMENT MANAGER - Build Script")
    print("=" * 50)

    # Limpa builds anteriores
    print("\n[1/4] Limpando builds anteriores...")
    clean_build_dirs()

    # Verifica se o ícone existe
    icon_path = Path("assets/icon.ico")
    icon_option = f"--icon={icon_path}" if icon_path.exists() else ""

    # Comando PyInstaller
    print("\n[2/4] Gerando executável com PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DocumentManager",
        "--onefile",
        "--windowed",
        "--noconsole",
        "--clean",
        "--add-data=src;src",
    ]

    if icon_option:
        cmd.append(icon_option)

    # Hidden imports necessários
    hidden_imports = [
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "tkcalendar",
        "babel.numbers",
        "reportlab",
        "reportlab.lib",
        "reportlab.platypus",
        "openpyxl",
    ]

    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # Collect all para customtkinter
    cmd.append("--collect-all=customtkinter")
    cmd.append("--collect-all=tkcalendar")

    # Arquivo principal
    cmd.append("src/main.py")

    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n[ERRO] Falha ao gerar executável!")
        return False

    print("\n[3/4] Copiando arquivos adicionais...")

    # Cria pasta assets no dist se necessário
    dist_assets = Path("dist/assets")
    if icon_path.exists():
        dist_assets.mkdir(parents=True, exist_ok=True)
        shutil.copy(icon_path, dist_assets / "icon.ico")
        print("  - Copiado: icon.ico")

    print("\n[4/4] Build concluído!")
    print("=" * 50)
    print(f"Executável gerado em: dist/DocumentManager.exe")
    print("=" * 50)

    return True


if __name__ == "__main__":
    # Muda para o diretório do script
    os.chdir(Path(__file__).parent)

    success = build_exe()
    sys.exit(0 if success else 1)
