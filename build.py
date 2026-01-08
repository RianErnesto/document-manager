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


def build_exe():
    """Gera o executável."""
    print("=" * 50)
    print("AMAZON INFORMÁTICA - Document Manager Build")
    print("=" * 50)

    # Limpa builds anteriores
    print("\n[1/3] Limpando builds anteriores...")
    clean_build_dirs()

    # Verifica se o arquivo .spec existe
    spec_file = Path("DocumentManager.spec")
    if not spec_file.exists():
        print("\n[ERRO] Arquivo DocumentManager.spec não encontrado!")
        return False

    # Comando PyInstaller usando o .spec
    print("\n[2/3] Gerando executável com PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        str(spec_file),
    ]

    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n[ERRO] Falha ao gerar executável!")
        return False

    # Copia o ícone para dist/assets
    print("\n[3/3] Copiando arquivos adicionais...")
    icon_path = Path("src/assets/LogoAmazonSmall.ico")
    dist_assets = Path("dist/assets")
    if icon_path.exists():
        dist_assets.mkdir(parents=True, exist_ok=True)
        shutil.copy(icon_path, dist_assets / "LogoAmazonSmall.ico")
        print("  - Copiado: LogoAmazonSmall.ico")

    print("\n[BUILD CONCLUÍDO!]")
    print("=" * 50)
    print(f"Executável gerado em: dist/DocumentManager.exe")
    print("=" * 50)

    return True


if __name__ == "__main__":
    # Muda para o diretório do script
    os.chdir(Path(__file__).parent)

    success = build_exe()
    sys.exit(0 if success else 1)
