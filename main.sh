#!/bin/bash
set -e  # Para encerrar o script caso haja erro

# Atualizando e instalando dependências
echo "📦 Instalando dependências..."
pip install --no-cache-dir -r requirements.txt

# Rodando o servidor Flask com Gunicorn (mais eficiente)
echo "🚀 Iniciando servidor Flask..."
gunicorn -w 4 -b 0.0.0.0:5000 app:app
