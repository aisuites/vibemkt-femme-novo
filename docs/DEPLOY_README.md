# DOCUMENTAÇÃO DE DEPLOY - IAMKT

**Versão:** 1.0  
**Data:** 09/02/2026  
**Ambiente:** Desenvolvimento

---

## � REPOSITÓRIO GITHUB

**URL:** https://github.com/aisuites/novo_iamkt

### Clone Rápido

```bash
cd /opt
sudo git clone https://github.com/aisuites/novo_iamkt.git iamkt
cd iamkt
sudo chown -R $USER:$USER /opt/iamkt
```

### Atualizar Código

```bash
cd /opt/iamkt
git pull origin main
docker compose build
docker compose restart
```

---

## �📚 ÍNDICE DE DOCUMENTAÇÃO

Este diretório contém toda a documentação necessária para realizar o deploy da aplicação IAMKT em um novo servidor.

### Documentos Disponíveis

1. **[DEPLOY_QUICK_START.md](DEPLOY_QUICK_START.md)** ⚡
   - Guia rápido em 5 passos
   - Para quem tem pressa
   - Tempo estimado: 40-70 minutos

2. **[DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)** 🐙 **NOVO!**
   - Deploy via GitHub
   - Clone, atualização e rollback
   - Automação com Git

3. **[DEPLOY_NOVO_SERVIDOR.md](DEPLOY_NOVO_SERVIDOR.md)** 📖
   - Guia completo e detalhado
   - Todas as etapas explicadas
   - Troubleshooting incluído

4. **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** ✅
   - Checklist passo a passo
   - Validação completa
   - Não esqueça nada

5. **[TRAEFIK_CONFIG_EXAMPLES.md](TRAEFIK_CONFIG_EXAMPLES.md)** 🌐
   - Exemplos de configuração Traefik
   - SSL/TLS com Let's Encrypt
   - Cloudflare DNS Challenge

---

## 🚀 INÍCIO RÁPIDO

### Para Iniciantes

1. Leia: [DEPLOY_QUICK_START.md](DEPLOY_QUICK_START.md)
2. Use: [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
3. Consulte: [DEPLOY_NOVO_SERVIDOR.md](DEPLOY_NOVO_SERVIDOR.md) quando tiver dúvidas

### Para Experientes

1. Execute: `sudo bash /opt/iamkt/scripts/deploy_setup.sh`
2. Configure: Variáveis de ambiente (Traefik já existe)
3. Deploy: `cd /opt/iamkt && make up`
4. Valide: `bash /opt/iamkt/scripts/deploy_validate.sh seu-dominio.com`

---

## 🛠️ SCRIPTS DISPONÍVEIS

Todos os scripts estão em `/opt/iamkt/scripts/`:

### 1. deploy_setup.sh
**Propósito:** Preparação inicial do servidor  
**Uso:** `sudo bash scripts/deploy_setup.sh`  
**Tempo:** ~15 minutos

**Funcionalidades:**
- Atualiza sistema operacional
- Instala Docker e dependências
- Configura firewall UFW
- Cria swap (opcional)
- Configura estrutura de diretórios
- Cria rede Docker traefik_proxy
- Aplica otimizações do sistema

### 2. deploy_migrate.sh
**Propósito:** Migração de dados entre servidores  
**Uso:** `bash scripts/deploy_migrate.sh`  
**Tempo:** 10-30 minutos

**Opções:**
1. Criar backup do servidor atual
2. Restaurar backup de arquivo local
3. Restaurar backup de servidor remoto (via SCP)
4. Migração completa (automatizada)

### 3. deploy_validate.sh
**Propósito:** Validação pós-deploy  
**Uso:** `bash scripts/deploy_validate.sh [dominio]`  
**Tempo:** ~2 minutos

**Validações:**
- Status dos containers
- Health checks
- Conectividade dos serviços
- Migrations aplicadas
- Volumes e redes
- Isolamento de portas
- Logs de erros
- Acesso HTTP/HTTPS
- Recursos do sistema

---

## 📋 FLUXO DE DEPLOY RECOMENDADO

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PREPARAÇÃO DO SERVIDOR                                   │
│    └─ sudo bash scripts/deploy_setup.sh                     │
│    └─ Logout e login novamente                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. TRAEFIK (JÁ EXISTE)                                      │
│    └─ Verificar: docker ps | grep traefik                  │
│    └─ Configurado em /opt/traefik/                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DEPLOY DA APLICAÇÃO                                      │
│    └─ git clone <repo> /opt/iamkt                           │
│    └─ cp .env.example .env.development                      │
│    └─ Editar .env.development                               │
│    └─ Atualizar docker-compose.yml (labels Traefik)         │
│    └─ make up                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONFIGURAÇÃO DJANGO                                      │
│    └─ docker exec iamkt_web python manage.py migrate       │
│    └─ docker exec -it iamkt_web python manage.py           │
│       createsuperuser                                        │
│    └─ docker exec iamkt_web python manage.py               │
│       collectstatic --noinput                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. MIGRAÇÃO DE DADOS                                        │
│    └─ bash /opt/iamkt/scripts/deploy_migrate.sh            │
│    └─ Escolher opção 4 (migração completa)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. VALIDAÇÃO                                                │
│    └─ bash /opt/iamkt/scripts/deploy_validate.sh           │
│       seu-dominio.com                                       │
│    └─ Testar funcionalidades principais                     │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ ARQUITETURA DO DEPLOY

### Containers

```
┌──────────────────────────────────────────────────────────────┐
│                         TRAEFIK                              │
│                    (Proxy Reverso)                           │
│                    Porta 80, 443                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                      IAMKT_WEB                               │
│                   (Django + Gunicorn)                        │
│                      Porta 8000                              │
└─────┬────────────────────────────────────────────────────────┘
      │
      ├─────→ IAMKT_POSTGRES (PostgreSQL 15)
      │       └─ Volume: iamkt_postgres_data
      │
      ├─────→ IAMKT_REDIS (Redis 7)
      │       └─ Volume: iamkt_redis_data
      │
      └─────→ IAMKT_CELERY (Worker)
              └─ Processa tasks assíncronas
```

### Redes

```
┌─────────────────────────────────────────────────────────────┐
│ traefik_proxy (externa)                                     │
│ └─ Traefik                                                  │
│ └─ iamkt_web                                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ iamkt_internal (privada - 172.23.0.0/24)                    │
│ └─ iamkt_web                                                │
│ └─ iamkt_postgres                                           │
│ └─ iamkt_redis                                              │
│ └─ iamkt_celery                                             │
└─────────────────────────────────────────────────────────────┘
```

### Volumes Persistentes

- `iamkt_postgres_data` → Dados do banco de dados
- `iamkt_redis_data` → Cache e filas
- `iamkt_media` → Arquivos de mídia (uploads)
- `iamkt_static` → Arquivos estáticos (CSS, JS)

---

## 🔑 VARIÁVEIS DE AMBIENTE CRÍTICAS

### Segurança

```bash
SECRET_KEY=<gerar-com-openssl-rand-hex-32>
DEBUG=False  # SEMPRE False em produção
ALLOWED_HOSTS=seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com
```

### Banco de Dados

```bash
DATABASE_URL=postgresql://iamkt_user:SENHA_SEGURA@iamkt_postgres:5432/iamkt_db
```

### AWS S3 (Obrigatório)

```bash
AWS_ACCESS_KEY_ID=sua-access-key
AWS_SECRET_ACCESS_KEY=sua-secret-key
AWS_STORAGE_BUCKET_NAME=iamkt-assets-dev
AWS_S3_REGION_NAME=us-east-1
```

### OpenAI (Obrigatório)

```bash
OPENAI_API_KEY=sua-openai-key
OPENAI_MODEL_TEXT=gpt-4
OPENAI_MODEL_IMAGE=dall-e-3
```

### N8N Webhooks

```bash
N8N_WEBHOOK_SECRET=<gerar-com-openssl-rand-hex-32>
N8N_ALLOWED_IPS=IP_DO_SERVIDOR_N8N
```

### Email

```bash
EMAIL_HOST=smtp.provedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@dominio.com
EMAIL_HOST_PASSWORD=sua-senha
```

---

## 🔒 CHECKLIST DE SEGURANÇA

### Obrigatório

- [ ] `SECRET_KEY` único e forte (32+ caracteres)
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` restrito
- [ ] Senha do PostgreSQL alterada
- [ ] Firewall configurado (apenas portas necessárias)
- [ ] PostgreSQL e Redis NÃO expostos externamente
- [ ] SSL/TLS habilitado (HTTPS)
- [ ] Headers de segurança configurados

### Recomendado

- [ ] Backups automáticos configurados
- [ ] Monitoramento configurado
- [ ] Rate limiting habilitado
- [ ] Autenticação de dois fatores (admin)
- [ ] Logs centralizados

---

## 🆘 SUPORTE E TROUBLESHOOTING

### Problemas Comuns

1. **Containers não iniciam**
   - Verificar logs: `docker compose logs`
   - Recriar: `make recreate`

2. **Erro de conexão com banco**
   - Verificar: `docker logs iamkt_postgres`
   - Testar: `docker exec iamkt_postgres pg_isready`

3. **HTTPS não funciona**
   - Verificar Traefik: `docker logs traefik`
   - Verificar labels: `docker inspect iamkt_web | grep traefik`

4. **Aplicação lenta**
   - Verificar recursos: `docker stats`
   - Aumentar workers Gunicorn

### Comandos Úteis

```bash
# Status geral
docker ps
make logs
docker stats

# Reiniciar serviços
make down
make up
docker compose restart iamkt_web

# Shell
make shell          # Django shell
make dbshell        # PostgreSQL shell
docker exec iamkt_web bash

# Backup
make backup
bash scripts/deploy_migrate.sh

# Validação
bash scripts/deploy_validate.sh seu-dominio.com
```

---

## 📊 REQUISITOS DO SERVIDOR

### Mínimo (Desenvolvimento)

- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disco:** 40 GB SSD
- **SO:** Ubuntu 20.04+

### Recomendado (Desenvolvimento)

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 80 GB SSD
- **SO:** Ubuntu 22.04 LTS

### Produção

- **CPU:** 4-8 cores
- **RAM:** 16 GB
- **Disco:** 160 GB SSD
- **SO:** Ubuntu 22.04 LTS

---

## 📞 CONTATO E SUPORTE

- **Repositório GitHub:** https://github.com/aisuites/novo_iamkt
- **Documentação completa:** `/opt/iamkt/docs/DEPLOY_NOVO_SERVIDOR.md`
- **Scripts de deploy:** `/opt/iamkt/scripts/`
- **Makefile:** `/opt/iamkt/Makefile`
- **Docker Compose:** `/opt/iamkt/docker-compose.yml`
- **Traefik:** `/opt/traefik/docker-compose.yml`

---

## 🔄 ATUALIZAÇÕES

### Como Atualizar a Aplicação

```bash
cd /opt/iamkt

# Backup antes de atualizar
make backup

# Atualizar código
git pull origin main

# Rebuild
docker compose build

# Aplicar migrations
make migrate

# Coletar estáticos
docker exec iamkt_web python manage.py collectstatic --noinput

# Reiniciar
docker compose restart iamkt_web
```

---

## 📝 CHANGELOG

### Versão 1.0 (09/02/2026)

- Documentação inicial de deploy
- Scripts de automação criados
- Exemplos de configuração Traefik
- Checklist completo
- Guia rápido

---

**Última atualização:** 09/02/2026  
**Mantido por:** Equipe IAMKT
