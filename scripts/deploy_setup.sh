#!/bin/bash
# =============================================================================
# IAMKT - SCRIPT DE SETUP INICIAL DO SERVIDOR
# =============================================================================
# Este script automatiza a preparação do servidor para deploy
# Uso: sudo bash deploy_setup.sh
# Data: 09/02/2026

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    log_error "Este script precisa ser executado como root (sudo)"
    exit 1
fi

log_info "Iniciando setup do servidor para IAMKT..."

# =============================================================================
# 1. ATUALIZAR SISTEMA
# =============================================================================
log_info "Atualizando sistema operacional..."
apt update && apt upgrade -y
log_success "Sistema atualizado"

# =============================================================================
# 2. INSTALAR DEPENDÊNCIAS BÁSICAS
# =============================================================================
log_info "Instalando dependências básicas..."
apt install -y \
    curl \
    wget \
    git \
    make \
    htop \
    vim \
    nano \
    net-tools \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common
log_success "Dependências instaladas"

# =============================================================================
# 3. INSTALAR DOCKER
# =============================================================================
log_info "Verificando instalação do Docker..."

if command -v docker &> /dev/null; then
    log_warning "Docker já instalado: $(docker --version)"
else
    log_info "Instalando Docker..."
    
    # Remover versões antigas
    apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Adicionar repositório Docker
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Verificar instalação
    docker --version
    docker compose version
    
    log_success "Docker instalado com sucesso"
fi

# =============================================================================
# 4. CONFIGURAR DOCKER
# =============================================================================
log_info "Configurando Docker..."

# Criar arquivo de configuração
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "dns": ["8.8.8.8", "8.8.4.4"]
}
EOF

# Reiniciar Docker
systemctl restart docker
systemctl enable docker
log_success "Docker configurado"

# =============================================================================
# 5. CONFIGURAR FIREWALL
# =============================================================================
log_info "Configurando firewall UFW..."

# Habilitar UFW
ufw --force enable

# Regras básicas
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH
ufw allow 22/tcp

# Permitir HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# (Opcional) Dashboard Traefik
read -p "Deseja permitir acesso ao Dashboard Traefik (porta 8080)? [s/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    ufw allow 8080/tcp
    log_success "Porta 8080 (Traefik) liberada"
fi

# (Opcional) Portainer
read -p "Deseja permitir acesso ao Portainer (porta 9000)? [s/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    ufw allow 9000/tcp
    log_success "Porta 9000 (Portainer) liberada"
fi

ufw reload
log_success "Firewall configurado"

# =============================================================================
# 6. CONFIGURAR SWAP
# =============================================================================
log_info "Verificando swap..."

if [ $(swapon --show | wc -l) -eq 0 ]; then
    read -p "Deseja criar arquivo swap de 4GB? [S/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "Criando swap de 4GB..."
        fallocate -l 4G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        log_success "Swap criado e ativado"
    fi
else
    log_warning "Swap já configurado"
fi

# =============================================================================
# 7. CRIAR ESTRUTURA DE DIRETÓRIOS
# =============================================================================
log_info "Criando estrutura de diretórios..."

mkdir -p /opt/{iamkt,traefik}
mkdir -p /opt/traefik/{letsencrypt,oauth2}
mkdir -p /opt/backups/iamkt

log_success "Diretórios criados"

# =============================================================================
# 8. CRIAR REDE DOCKER
# =============================================================================
log_info "Criando rede Docker traefik_proxy..."

if docker network ls | grep -q traefik_proxy; then
    log_warning "Rede traefik_proxy já existe"
else
    docker network create traefik_proxy
    log_success "Rede traefik_proxy criada"
fi

# =============================================================================
# 9. ADICIONAR USUÁRIO AO GRUPO DOCKER
# =============================================================================
log_info "Configurando permissões Docker..."

# Obter usuário real (não root)
REAL_USER=${SUDO_USER:-$USER}

if [ "$REAL_USER" != "root" ]; then
    usermod -aG docker $REAL_USER
    log_success "Usuário $REAL_USER adicionado ao grupo docker"
    log_warning "IMPORTANTE: Faça logout e login novamente para aplicar as permissões"
fi

# =============================================================================
# 10. OTIMIZAÇÕES DO SISTEMA
# =============================================================================
log_info "Aplicando otimizações do sistema..."

# Aumentar limites de arquivos
cat >> /etc/security/limits.conf <<EOF
* soft nofile 65536
* hard nofile 65536
EOF

# Otimizações de rede
cat >> /etc/sysctl.conf <<EOF
# Otimizações para Docker e aplicações web
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 1024 65535
vm.swappiness = 10
EOF

sysctl -p
log_success "Otimizações aplicadas"

# =============================================================================
# RESUMO
# =============================================================================
echo ""
echo "========================================================================="
log_success "SETUP DO SERVIDOR CONCLUÍDO COM SUCESSO!"
echo "========================================================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1. Fazer logout e login novamente para aplicar permissões Docker"
echo "2. Configurar Traefik: cd /opt/traefik (se necessário)"
echo "3. Clonar repositório IAMKT:"
echo "   cd /opt && sudo git clone https://github.com/aisuites/novo_iamkt.git iamkt"
echo "   sudo chown -R \$USER:\$USER /opt/iamkt"
echo "4. Configurar variáveis de ambiente: cd /opt/iamkt && cp .env.example .env.development"
echo "5. Executar deploy: cd /opt/iamkt && make up"
echo ""
echo "Documentação completa: /opt/iamkt/docs/DEPLOY_NOVO_SERVIDOR.md"
echo ""
echo "========================================================================="
echo ""

# Informações do sistema
log_info "Informações do sistema:"
echo "  - Sistema: $(lsb_release -d | cut -f2)"
echo "  - Docker: $(docker --version)"
echo "  - Docker Compose: $(docker compose version)"
echo "  - Memória: $(free -h | grep Mem | awk '{print $2}')"
echo "  - Disco: $(df -h / | tail -1 | awk '{print $4}') disponível"
echo "  - Swap: $(free -h | grep Swap | awk '{print $2}')"
echo ""

log_warning "LEMBRE-SE: Faça logout e login novamente!"
