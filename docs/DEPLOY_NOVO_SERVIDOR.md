# GUIA DE DEPLOY - IAMKT PARA NOVO SERVIDOR

**Data:** 09/02/2026  
**Versão:** 1.0  
**Ambiente:** Desenvolvimento (novo servidor)

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Requisitos do Servidor](#requisitos-do-servidor)
3. [Preparação do Servidor](#preparação-do-servidor)
4. [Configuração da Infraestrutura](#configuração-da-infraestrutura)
5. [Deploy da Aplicação](#deploy-da-aplicação)
6. [Migração de Dados](#migração-de-dados)
7. [Validação e Testes](#validação-e-testes)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 VISÃO GERAL

### Arquitetura Atual

A aplicação IAMKT utiliza:

- **Aplicação:** Django 4.2+ com Gunicorn
- **Banco de Dados:** PostgreSQL 15 (Alpine)
- **Cache/Queue:** Redis 7 (Alpine)
- **Worker:** Celery
- **Proxy Reverso:** Traefik 2.x
- **Orquestração:** Docker Compose
- **Gerenciamento:** Portainer (opcional)

### Estrutura de Containers

```
iamkt_web         → Aplicação Django (porta 8000)
iamkt_celery      → Worker Celery
iamkt_postgres    → Banco de dados PostgreSQL
iamkt_redis       → Cache e message broker
```

### Redes Docker

```
iamkt_internal    → Rede privada (172.23.0.0/24)
traefik_proxy     → Rede externa (compartilhada)
```

### Volumes Persistentes

```
iamkt_postgres_data  → Dados do PostgreSQL
iamkt_redis_data     → Dados do Redis
iamkt_media          → Arquivos de mídia
iamkt_static         → Arquivos estáticos
```

---

## 💻 REQUISITOS DO SERVIDOR

### Sistema Operacional

- **Recomendado:** Ubuntu 22.04 LTS ou Debian 12
- **Mínimo:** Ubuntu 20.04 LTS

### Hardware Mínimo (Desenvolvimento)

- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disco:** 40 GB SSD
- **Rede:** 100 Mbps

### Hardware Recomendado (Desenvolvimento)

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 80 GB SSD
- **Rede:** 1 Gbps

### Software Necessário

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git 2.30+
- Make (opcional, mas recomendado)
- Curl/Wget

### Portas Necessárias

- **80:** HTTP (Traefik)
- **443:** HTTPS (Traefik)
- **8080:** Dashboard Traefik (opcional)
- **9000:** Portainer (opcional)

**IMPORTANTE:** PostgreSQL (5432) e Redis (6379) NÃO devem ser expostos externamente.

---

## PREPARAÇÃO DO SERVIDOR

### 1. Atualizar Sistema

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar utilitários básicos
sudo apt install -y \
    curl \
    wget \
    git \
    make \
    htop \
    vim \
    net-tools \
    ufw
```

### 2. Instalar Docker

```bash
# Remover versões antigas
sudo apt remove docker docker-engine docker.io containerd runc

# Adicionar repositório Docker
sudo apt install -y ca-certificates gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar instalação
docker --version
docker compose version

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Testar
docker run hello-world
```

### 3. Configurar Firewall

```bash
# Habilitar UFW
sudo ufw --force enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# (Opcional) Dashboard Traefik
sudo ufw allow 8080/tcp

# (Opcional) Portainer
sudo ufw allow 9000/tcp

# Verificar status
sudo ufw status verbose
```

### 4. Configurar Swap (Opcional mas Recomendado)

```bash
# Criar arquivo swap de 4GB
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verificar
free -h
```

### 5. Otimizar Docker

```bash
# Criar arquivo de configuração
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
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
sudo systemctl restart docker
```

---

## 🌐 CONFIGURAÇÃO DA INFRAESTRUTURA

### 1. Criar Estrutura de Diretórios

```bash
# Criar diretório base (se não existir)
sudo mkdir -p /opt
cd /opt

# Estrutura padrão do servidor
# /opt/
# ├── iamkt/          → Aplicação IAMKT
# ├── traefik/        → Configuração Traefik (já existe)
# ├── bot/            → Outras aplicações
# ├── nto/            → Outras aplicações
# └── vibemkt/        → Outras aplicações
```

### 2. Configurar Traefik

**IMPORTANTE:** O Traefik já está instalado e rodando em `/opt/traefik/`. Se for um servidor novo, siga os passos abaixo:

```bash
# Criar diretório
sudo mkdir -p /opt/traefik/{letsencrypt,oauth2}
cd /opt/traefik

# Criar rede compartilhada
docker network create traefik_proxy

# Criar .env
nano .env
```

**Criar arquivo:** `/opt/traefik/.env`

```bash
# Email para Let's Encrypt
ACME_EMAIL=seu-email@dominio.com

# Cloudflare API Token (para DNS Challenge)
CF_DNS_API_TOKEN=seu-cloudflare-token

# OAuth2 Proxy (opcional - para proteger Portainer)
OAUTH2_PROXY_CLIENT_ID=seu-google-client-id
OAUTH2_PROXY_CLIENT_SECRET=seu-google-client-secret
OAUTH2_PROXY_COOKIE_SECRET=gerar-com-openssl-rand-base64-32
```

**Criar arquivo:** `/opt/traefik/docker-compose.yml`

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.endpoint=unix:///var/run/docker.sock
      
      # Entrypoints HTTP/HTTPS
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      
      # Redirecionar tudo de HTTP -> HTTPS
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      
      # Let's Encrypt via Cloudflare DNS-01
      - --certificatesresolvers.cloudflare.acme.dnschallenge=true
      - --certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare
      - --certificatesresolvers.cloudflare.acme.email=${ACME_EMAIL}
      - --certificatesresolvers.cloudflare.acme.storage=/letsencrypt/acme.json
      
      # Logs
      - --log.level=INFO
    
    ports:
      - "80:80"
      - "443:443"
    
    environment:
      - CF_DNS_API_TOKEN=${CF_DNS_API_TOKEN}
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/traefik/letsencrypt:/letsencrypt
    
    networks:
      - traefik_proxy
    
    restart: always

networks:
  traefik_proxy:
    external: true
```

**Iniciar Traefik:**

```bash
cd /opt/traefik
docker compose up -d
docker logs traefik -f
```

### 3. Portainer

**IMPORTANTE:** O Portainer já está instalado e rodando em `/opt/traefik/docker-compose.yml` com autenticação OAuth2 via Google.

- **URL:** https://portainer-femmeintegra.aisuites.com.br (ajustar domínio)
- **Autenticação:** Google OAuth2 (configurado no oauth2-proxy)
- **Acesso:** Apenas emails autorizados em `/opt/traefik/oauth2/authenticated-emails.txt`

Se precisar adicionar usuários autorizados:

```bash
cd /opt/traefik
nano oauth2/authenticated-emails.txt
# Adicionar emails, um por linha
docker compose restart oauth2-proxy
```

---

## 🚀 DEPLOY DA APLICAÇÃO

### 1. Clonar Repositório

```bash
cd /opt
sudo git clone https://github.com/aisuites/novo_iamkt.git iamkt
cd iamkt

# Ajustar permissões
sudo chown -R $USER:$USER /opt/iamkt

# Verificar branch
git branch
git status
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar exemplo
cp .env.example .env.development

# Editar arquivo
nano .env.development
```

**Variáveis CRÍTICAS a configurar:**

```bash
# Django Security
SECRET_KEY=<gerar-com-openssl-rand-hex-32>
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
SITE_URL=https://seu-dominio.com

# Database (manter padrão ou alterar senha)
DATABASE_URL=postgresql://iamkt_user:SENHA_SEGURA@iamkt_postgres:5432/iamkt_db

# AWS S3 (obrigatório para upload de arquivos)
AWS_ACCESS_KEY_ID=sua-access-key
AWS_SECRET_ACCESS_KEY=sua-secret-key
AWS_STORAGE_BUCKET_NAME=iamkt-assets-dev
AWS_S3_REGION_NAME=us-east-1

# OpenAI (obrigatório para geração de conteúdo)
OPENAI_API_KEY=sua-openai-key

# N8N Webhooks
N8N_WEBHOOK_SECRET=<gerar-com-openssl-rand-hex-32>
N8N_ALLOWED_IPS=IP_DO_SERVIDOR_N8N

# Email (configurar SMTP)
EMAIL_HOST=smtp.seu-provedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@dominio.com
EMAIL_HOST_PASSWORD=sua-senha
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
```

**Gerar secrets:**

```bash
# Secret Key Django
openssl rand -hex 32

# N8N Webhook Secret
openssl rand -hex 32
```

### 3. Atualizar docker-compose.yml

Editar labels do Traefik no `docker-compose.yml`:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik_proxy"
  - "traefik.http.routers.iamkt-https.rule=Host(`seu-dominio.com`)"
  - "traefik.http.routers.iamkt-https.entrypoints=websecure"
  - "traefik.http.routers.iamkt-https.tls=true"
  - "traefik.http.routers.iamkt-http.rule=Host(`seu-dominio.com`)"
  - "traefik.http.routers.iamkt-http.entrypoints=web"
  - "traefik.http.routers.iamkt-http.middlewares=https-redirect"
  - "traefik.http.services.iamkt.loadbalancer.server.port=8000"
```

### 4. Build e Deploy

```bash
# Verificar configuração
make setup

# Build da imagem
docker compose build

# Iniciar serviços
make up

# Ou modo solo (mais recursos)
make solo

# Verificar logs
make logs
```

### 5. Executar Migrations

```bash
# Aguardar containers iniciarem (30-60s)
sleep 60

# Executar migrations
make migrate

# Ou manualmente
docker exec iamkt_web python manage.py migrate

# Criar superusuário
docker exec -it iamkt_web python manage.py createsuperuser

# Coletar arquivos estáticos
docker exec iamkt_web python manage.py collectstatic --noinput
```

### 6. Validar Deploy

```bash
# Verificar containers
docker ps | grep iamkt

# Verificar logs
docker compose logs -f iamkt_web

# Verificar saúde
docker inspect iamkt_web | grep -A 10 Health

# Testar endpoint
curl -I http://localhost:8000/health/

# Validar isolamento
make validate
```

---

## 📦 MIGRAÇÃO DE DADOS

### 1. Backup do Servidor Antigo

**No servidor ANTIGO:**

```bash
cd /opt/iamkt

# Backup PostgreSQL
make backup

# Ou manualmente
docker exec -t iamkt_postgres pg_dump -U iamkt_user -Fc iamkt_db > backup_$(date +%Y%m%d_%H%M%S).dump

# Backup de arquivos de mídia
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C app media/

# Backup de arquivos estáticos (se necessário)
tar -czf static_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C app staticfiles/
```

### 2. Transferir Backups

```bash
# Do servidor ANTIGO para o NOVO
scp backup_*.dump usuario@novo-servidor:/tmp/
scp media_backup_*.tar.gz usuario@novo-servidor:/tmp/
```

### 3. Restaurar no Servidor Novo

**No servidor NOVO:**

```bash
cd /opt/iamkt

# Restaurar PostgreSQL
cat /tmp/backup_*.dump | docker exec -i iamkt_postgres pg_restore -U iamkt_user -d iamkt_db --clean --if-exists

# Ou com arquivo .sql
cat /tmp/backup_*.sql | docker exec -i iamkt_postgres psql -U iamkt_user -d iamkt_db

# Restaurar mídia
tar -xzf /tmp/media_backup_*.tar.gz -C app/

# Ajustar permissões
sudo chown -R 1000:1000 app/media/

# Reiniciar aplicação
cd /opt/iamkt
docker compose restart iamkt_web
```

### 4. Validar Migração

```bash
# Verificar dados no banco
docker exec -it iamkt_postgres psql -U iamkt_user -d iamkt_db -c "SELECT COUNT(*) FROM auth_user;"

# Verificar arquivos de mídia
ls -lah app/media/

# Testar aplicação
curl -I https://seu-dominio.com/
```

---

## ✅ VALIDAÇÃO E TESTES

### Checklist de Validação

- [ ] Containers rodando: `docker ps | grep iamkt`
- [ ] Health checks OK: `docker inspect iamkt_web | grep Health`
- [ ] PostgreSQL acessível: `docker exec iamkt_postgres pg_isready`
- [ ] Redis acessível: `docker exec iamkt_redis redis-cli ping`
- [ ] Celery funcionando: `docker logs iamkt_celery`
- [ ] Migrations aplicadas: `docker exec iamkt_web python manage.py showmigrations`
- [ ] Superusuário criado: Login no admin
- [ ] Arquivos estáticos servidos: Acessar /static/
- [ ] Upload de arquivos funcionando: Testar upload
- [ ] SSL/HTTPS funcionando: Acessar https://seu-dominio.com
- [ ] Logs sem erros críticos: `docker compose logs`
- [ ] Traefik funcionando: `docker logs traefik`

### Testes Funcionais

```bash
# 1. Testar health endpoint
curl https://seu-dominio.com/health/

# 2. Testar admin
curl -I https://seu-dominio.com/admin/

# 3. Testar login
# Acessar via browser e fazer login

# 4. Testar upload de arquivo
# Via interface da aplicação

# 5. Testar geração de post
# Via interface da aplicação

# 6. Verificar emails
# Testar funcionalidade de envio de email
```

### Monitoramento

```bash
# Logs em tempo real
make logs

# Logs específicos
docker compose logs -f iamkt_web
docker compose logs -f iamkt_celery
docker compose logs -f iamkt_postgres

# Recursos
docker stats

# Espaço em disco
df -h
docker system df
```

---

## 🔧 TROUBLESHOOTING

### Containers não iniciam

```bash
# Verificar logs
docker compose logs

# Verificar portas em uso
sudo netstat -tulpn | grep -E ':(80|443|5432|6379)'

# Recriar containers
docker compose down
docker compose up -d --force-recreate
```

### Erro de conexão com PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Verificar logs
docker logs iamkt_postgres

# Testar conexão
docker exec iamkt_postgres psql -U iamkt_user -d iamkt_db -c "SELECT 1;"

# Verificar variáveis de ambiente
docker exec iamkt_web env | grep DATABASE
```

### Erro de permissão em volumes

```bash
# Ajustar permissões
sudo chown -R 1000:1000 app/media app/staticfiles

# Recriar volumes (CUIDADO: apaga dados)
docker compose down -v
docker compose up -d
```

### SSL/HTTPS não funciona

```bash
# Verificar Traefik
docker logs traefik

# Verificar labels
docker inspect iamkt_web | grep traefik

# Verificar rede
docker network inspect traefik_proxy
```

### Aplicação lenta

```bash
# Verificar recursos
docker stats

# Aumentar workers Gunicorn (docker-compose.yml)
CMD ["gunicorn", "sistema.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]

# Verificar queries lentas no PostgreSQL
docker exec iamkt_postgres psql -U iamkt_user -d iamkt_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Limpar espaço em disco

```bash
# Limpar containers parados
docker container prune -f

# Limpar imagens não usadas
docker image prune -a -f

# Limpar volumes não usados (CUIDADO)
docker volume prune -f

# Limpar tudo (CUIDADO)
docker system prune -a --volumes -f
```

---

## 📚 COMANDOS ÚTEIS

```bash
# Makefile
make help          # Ver todos os comandos
make up            # Iniciar aplicação
make down          # Parar aplicação
make logs          # Ver logs
make shell         # Shell Django
make dbshell       # Shell PostgreSQL
make migrate       # Executar migrations
make backup        # Backup do banco

# Docker Compose
docker compose ps                    # Status dos containers
docker compose logs -f               # Logs em tempo real
docker compose restart iamkt_web     # Reiniciar container
docker compose exec iamkt_web bash   # Shell no container

# Django
docker exec iamkt_web python manage.py migrate
docker exec iamkt_web python manage.py createsuperuser
docker exec iamkt_web python manage.py collectstatic
docker exec iamkt_web python manage.py shell

# PostgreSQL
docker exec -it iamkt_postgres psql -U iamkt_user -d iamkt_db
docker exec iamkt_postgres pg_dump -U iamkt_user iamkt_db > backup.sql

# Redis
docker exec iamkt_redis redis-cli ping
docker exec iamkt_redis redis-cli INFO
```

---

## 📞 SUPORTE

Em caso de problemas:

1. Verificar logs: `docker compose logs`
2. Verificar health checks: `docker ps`
3. Consultar documentação em `/opt/iamkt/docs/`
4. Verificar issues conhecidos

---

**Fim do Guia de Deploy**
