import urllib.request
import os
import sys
import subprocess

def install_pip():
    # Verifica se o pip já existe
    try:
        import pip
        print("   [Setup] Pip já está instalado.")
        return
    except ImportError:
        pass

    print("   [Setup] Baixando get-pip.py...")
    url = "https://bootstrap.pypa.io/get-pip.py"
    try:
        urllib.request.urlretrieve(url, "get-pip.py")
    except Exception as e:
        print(f"   [Erro] Falha ao baixar pip: {e}")
        return

    print("   [Setup] Instalando pip no ambiente virtual...")
    # Usa o executável atual (do venv) para rodar o script baixado
    subprocess.check_call([sys.executable, "get-pip.py"])
    
    # Limpeza
    if os.path.exists("get-pip.py"):
        os.remove("get-pip.py")

if __name__ == "__main__":
    install_pip()