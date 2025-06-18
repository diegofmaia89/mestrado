# Dissertação de mestrado - UTFPR | Diego Fernando Maia

# Network Analyzer

Um sistema completo de análise de rede com dashboard web e ferramentas de monitoramento em tempo real.

## 📋 Visão Geral

Este projeto consiste em um analisador de rede que combina:
- **Dashboard Web**: Interface gráfica para visualização de dados
- **Network Analyzer**: Ferramenta de análise e monitoramento de rede
- **Banco de Dados MongoDB**: Armazenamento de dados de análise

## 🚀 Instalação Automática

### Pré-requisitos
- Sistema Linux (Ubuntu/Debian, Fedora/CentOS/RHEL, ou Arch Linux)
- Acesso sudo
- Conexão com a internet

### Instalação Completa

Execute o script de instalação para configurar automaticamente todo o ambiente:

```bash
chmod +x install.sh
./install.sh
```

O script irá:
- ✅ Detectar automaticamente o sistema operacional
- ✅ Instalar pacotes do sistema necessários
- ✅ Configurar MongoDB
- ✅ Criar ambiente virtual Python
- ✅ Instalar dependências Python
- ✅ Configurar estrutura do projeto

### Pacotes Instalados

**Pacotes do Sistema:**
- Python3 e ferramentas de desenvolvimento
- MongoDB
- Ferramentas de rede (wireless-tools, net-tools, iw, mtr, etc.)
- Utilitários essenciais (curl, wget, git)

**Dependências Python:**
- Flask (framework web)
- PyMongo (driver MongoDB)
- NumPy (computação científica)
- Requests (requisições HTTP)
- Gunicorn (servidor WSGI)

## 🎯 Uso

### Execução do Sistema

Use o script principal para executar o sistema completo:

```bash
chmod +x network_analyzer.sh
./network_analyzer.sh
```

### O que acontece na execução:

1. **Inicialização do MongoDB**
   ```
   === Iniciando Banco de Dados ===
   ✓ MongoDB iniciado com sucesso
   ```

2. **Execução do Dashboard** (em background)
   ```
   === Executando Dashboard ===
   ✓ Dashboard iniciado (PID: XXXX)
   ```

3. **Execução do Network Analyzer** (em primeiro plano)
   ```
   === Executando Network Analyzer ===
   -------------------------------------------
   [Saída do analisador de rede aqui]
   ```

### Controle dos Processos

- **Dashboard**: Roda silenciosamente em background
- **Network Analyzer**: Exibe saída em tempo real
- **Parar tudo**: Pressione `Ctrl+C` para finalizar ambos os processos
- **Parar apenas Dashboard**: `kill PID_DO_DASHBOARD`

## 📁 Estrutura do Projeto

```
network-analyzer/
├── venv/                   # Ambiente virtual Python
├── templates/              # Templates HTML do dashboard
├── static/                 # Arquivos estáticos (CSS, JS)
├── logs/                   # Arquivos de log
├── dashboard.py            # Aplicação web do dashboard
├── network_analyzer.py     # Analisador de rede principal
├── network_analyzer.sh     # Script de execução
└── install.sh             # Script de instalação
```

## 🛠️ Configuração Manual

Se preferir instalar manualmente ou personalizar a instalação:

### 1. Instalar MongoDB
```bash
# Ubuntu/Debian
sudo apt install mongodb

# Fedora/CentOS
sudo dnf install mongodb-server

# Arch Linux
sudo pacman -S mongodb
```

### 2. Configurar Ambiente Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask pymongo numpy requests gunicorn
```

### 3. Iniciar Serviços
```bash
sudo systemctl start mongod
sudo systemctl enable mongod
```

## 🔧 Troubleshooting

### MongoDB não inicia
```bash
# Verificar status do serviço
sudo systemctl status mongod

# Verificar logs
sudo journalctl -u mongod

# Reiniciar serviço
sudo systemctl restart mongod
```

### Problemas de Permissão
```bash
# Verificar se o usuário está no grupo correto
groups $USER

# Adicionar permissões se necessário
sudo usermod -a -G mongodb $USER
```

### Porta em Uso
Se a porta do dashboard estiver em uso, verifique processos rodando:
```bash
sudo netstat -tulpn | grep :5000
sudo lsof -i :5000
```

## 📊 Funcionalidades

### Dashboard Web
- Interface gráfica para visualização de dados
- Monitoramento em tempo real
- Histórico de análises
- Gráficos e métricas

### Network Analyzer
- Análise de conectividade
- Monitoramento de latência
- Detecção de problemas de rede
- Relatórios detalhados

### Banco de Dados
- Armazenamento persistente de dados
- Consultas otimizadas
- Backup automático de informações

### Informações adicionais
- Dashboard será acessível em: http://localhost:5000
- Certifique-se de ter uma interface de rede wireless ativa
- Algumas funcionalidades podem precisar de privilégios sudo
- O MongoDB precisa estar rodando para salvar os dados"


## 🔒 Segurança

- Execute sempre como usuário não-root
- MongoDB configurado para acesso local
- Logs de segurança ativados
- Validação de entrada de dados

## 🤝 Contribuição

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto possui código aberto, para fins acadêmicos.

## 👨‍💻 Autor

**Diego Fernando Maia**  
Projeto desenvolvido como parte da dissertação de mestrado.

---

**Nota**: Este sistema requer privilégios administrativos para algumas operações de rede. Use com responsabilidade e em conformidade com as políticas de segurança da sua organização.
