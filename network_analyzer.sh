#!/bin/bash

# Script para inicializar Banco de Dados e executar aplicações
# Autor: Diego
# Data: 2025-06

echo "=== Iniciando Banco de Dados ==="
sudo service mongod start

# Verifica se o Banco de dados foi iniciado com sucesso
if [ $? -eq 0 ]; then
    echo "✓ MongoDB iniciado com sucesso"
else
    echo "✗ Erro ao iniciar MongoDB"
    exit 1
fi

echo ""
echo "=== Executando Dashboard ==="
python3 <"diretório local do arquivo dashboard.py"> > /dev/null 2>&1 &
DASHBOARD_PID=$!
echo "✓ Dashboard iniciado (PID: $DASHBOARD_PID)"

echo ""
sleep 3

echo ""
echo "=== Executando Network Analyzer ==="
echo "-------------------------------------------"
python3 <"diretório local do arquivo network_analyzer.py">
NETWORK_PID=$!
echo ""
echo "=== Ambos os processos estão rodando ==="
echo "Dashboard (silencioso) PID: $DASHBOARD_PID"
echo "Network Analyzer (visível) executando..."
echo ""
echo "Para parar o Dashboard: kill $DASHBOARD_PID"
echo "Para parar o Network Analyzer: Ctrl+C"
echo ""
echo "Pressione Ctrl+C para parar todos os processos"

# Função para limpar processos ao receber SIGINT (Ctrl+C)
cleanup() {
    echo ""
    echo "=== Finalizando processos ==="
    kill $DASHBOARD_PID 2>/dev/null
    echo "✓ Dashboard finalizado"
    echo "✓ Network Analyzer finalizado"
    exit 0
}

# Captura o sinal SIGINT (Ctrl+C)
trap cleanup SIGINT

# O Network Analyzer roda em primeiro plano (exibe saída)
# O Dashboard roda silenciosamente em background
