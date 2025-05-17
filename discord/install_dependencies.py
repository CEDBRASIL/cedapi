import os

def install_dependencies():
    print("📦 Instalando dependências necessárias para o bot...")
    os.system("pip install -r requirements.txt")

if __name__ == "__main__":
    install_dependencies()
