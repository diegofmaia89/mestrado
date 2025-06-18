#!/bin/bash

# Script de instalação de dependências para Network Analyzer
# Este script instala todas as ferramentas e pacotes necessários para executar
# network_analyzer.py e dashboard.py

set -e  # Para o script se algum comando falhar

echo "==============================================="
echo "Network Analyzer - Instalação de Dependências"
echo "==============================================="

# Função para verificar se o comando foi executado com sucesso
check_command() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 instalado com sucesso"
    else
        echo "❌ Erro ao instalar $1"
        exit 1
    fi
}

# Atualizar repositórios do sistema
echo "🔄 Atualizando repositórios do sistema..."
sudo apt update
check_command "Atualização dos repositórios"

# Instalar Python3 e pip se não estiverem instalados
echo "🐍 Verificando instalação do Python3..."
if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip
    check_command "Python3 e pip"
else
    echo "✅ Python3 já está instalado"
fi

# Instalar ferramentas de rede necessárias
echo "🌐 Instalando ferramentas de rede..."
sudo apt install -y \
    iputils-ping \
    iproute2 \
    wireless-tools \
    iw \
    net-tools \
    netcat-openbsd \
    mtr-tiny \
    dnsutils
check_command "Ferramentas de rede"

# Instalar MongoDB
echo "🗄️ Instalando MongoDB..."
if ! command -v mongod &> /dev/null; then
    # Importar chave pública do MongoDB
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Adicionar repositório do MongoDB
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Atualizar repositórios e instalar MongoDB
    sudo apt update
    sudo apt install -y mongodb-org
    
    # Iniciar e habilitar MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    check_command "MongoDB"
else
    echo "✅ MongoDB já está instalado"
    # Garantir que o MongoDB está rodando
    sudo systemctl start mongod
fi

# Instalar dependências Python
echo "📦 Instalando dependências Python..."

# Criar arquivo requirements.txt temporário
cat > /tmp/requirements.txt << EOF
pymongo>=4.0.0
requests>=2.25.0
flask>=2.0.0
numpy>=1.21.0
EOF

# Instalar dependências Python
pip3 install -r /tmp/requirements.txt
check_command "Dependências Python"

# Remover arquivo temporário
rm /tmp/requirements.txt

# Verificar se todas as ferramentas estão funcionando
echo "🔍 Verificando instalações..."

# Verificar ferramentas de rede
commands_to_check=(
    "ping"
    "ip"
    "iwconfig"
    "iw"
    "nc"
    "mtr"
    "nslookup"
)

for cmd in "${commands_to_check[@]}"; do
    if command -v $cmd &> /dev/null; then
        echo "✅ $cmd disponível"
    else
        echo "❌ $cmd não encontrado"
    fi
done

# Verificar Python modules
echo "🐍 Verificando módulos Python..."
python3 -c "
import sys
modules = ['pymongo', 'requests', 'flask', 'numpy', 'subprocess', 're', 'os', 'platform', 'statistics', 'datetime', 'threading', 'time']
missing = []
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module} disponível')
    except ImportError:
        missing.append(module)
        print(f'❌ {module} não encontrado')

if missing:
    print(f'Módulos faltando: {missing}')
    sys.exit(1)
else:
    print('✅ Todos os módulos Python estão disponíveis')
"

# Verificar status do MongoDB
echo "🗄️ Verificando status do MongoDB..."
if sudo systemctl is-active --quiet mongod; then
    echo "✅ MongoDB está rodando"
else
    echo "⚠️ MongoDB não está rodando. Tentando iniciar..."
    sudo systemctl start mongod
    if sudo systemctl is-active --quiet mongod; then
        echo "✅ MongoDB iniciado com sucesso"
    else
        echo "❌ Erro ao iniciar MongoDB"
    fi
fi

# Criar diretório templates se não existir (necessário para o dashboard)
echo "📁 Criando diretório templates..."
mkdir -p templates
echo "✅ Diretório templates criado"

# Verificar permissões de rede (algumas ferramentas podem precisar de sudo)
echo "🔐 Verificando permissões..."
if [ "$EUID" -eq 0 ]; then
    echo "⚠️ Script executado como root. Algumas funcionalidades de rede podem funcionar melhor."
else
    echo "ℹ️ Script executado como usuário normal. Algumas funcionalidades podem precisar de sudo."
fi

echo ""
echo "=========================================="
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📋 Resumo das instalações:"
echo "• Ferramentas de rede: ping, ip, iwconfig, iw, nc, mtr, nslookup"
echo "• MongoDB: Instalado e configurado"
echo "• Python: pymongo, requests, flask, numpy"
echo ""
