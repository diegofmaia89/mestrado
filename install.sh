#!/bin/bash

# Network Analyzer Installer Script
# Instala e configura o sistema completo de análise de rede

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="network-analyzer"
PROJECT_DIR="$HOME/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="network-analyzer"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        DISTRO=$ID
    else
        print_error "Cannot detect operating system"
        exit 1
    fi
    print_status "Detected OS: $OS"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root"
        exit 1
    fi
}

# Function to install system packages
install_system_packages() {
    print_status "Installing system packages..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                mongodb \
                wireless-tools \
                net-tools \
                iputils-ping \
                mtr-tiny \
                netcat-openbsd \
                iw \
                build-essential \
                curl \
                wget \
                git
            ;;
        fedora|centos|rhel)
            sudo dnf install -y \
                python3 \
                python3-pip \
                python3-devel \
                mongodb-server \
                wireless-tools \
                net-tools \
                iputils \
                mtr \
                nc \
                iw \
                gcc \
                gcc-c++ \
                make \
                curl \
                wget \
                git
            ;;
        arch)
            sudo pacman -S --noconfirm \
                python \
                python-pip \
                mongodb \
                wireless_tools \
                net-tools \
                iputils \
                mtr \
                openbsd-netcat \
                iw \
                base-devel \
                curl \
                wget \
                git
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
    
    print_success "System packages installed successfully"
}

# Function to setup MongoDB
setup_mongodb() {
    print_status "Setting up MongoDB..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo systemctl start mongod
            sudo systemctl enable mongod
            ;;
        fedora|centos|rhel)
            sudo systemctl start mongod
            sudo systemctl enable mongod
            ;;
        arch)
            sudo systemctl start mongodb
            sudo systemctl enable mongodb
            ;;
    esac
    
    # Wait for MongoDB to start
    sleep 5
    
    # Test MongoDB connection
    if mongo --eval "db.adminCommand('ismaster')" >/dev/null 2>&1; then
        print_success "MongoDB is running successfully"
    else
        print_warning "MongoDB may not be running properly. Please check manually."
    fi
}

# Function to create project directory structure
create_project_structure() {
    print_status "Creating project directory structure..."
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Create subdirectories
    mkdir -p templates static logs
    
    print_success "Project structure created at $PROJECT_DIR"
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    cd "$PROJECT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required Python packages
    pip install \
        flask \
        pymongo \
        numpy \
        requests \
        gunicorn
    
    print_success "Python virtual environment setup complete"
}
