# GUIA RÁPIDO DE DEPLOY - IAMKT

**Para quem tem pressa!** ⚡

---

## 🚀 DEPLOY EM 5 PASSOS

### 1️⃣ Preparar Servidor (10-15 min)

```bash
# Conectar ao servidor novo
ssh usuario@novo-servidor

# Executar script de setup
cd /tmp
wget https://raw.githubusercontent.com/seu-repo/iamkt/main/scripts/deploy_setup.sh
sudo bash deploy_setup.sh

# IMPORTANTE: Fazer logout e login
exit
ssh usuario@novo-servidor
```

### 2️⃣ Configurar Traefik (5 min)

**IMPORTANTE:** O Traefik já está rodando em `/opt/traefik/`. Se for servidor novo:

```bash
cd /opt/traefik

# Criar .env com credenciais Cloudflare
nano .env

# Criar docker-compose.yml (copiar do guia completo)
nano docker-compose.yml

# Iniciar Traefik
docker compose up -d
docker logs traefik
```

### 3️⃣ Deploy da Aplicação (10 min)

```bash
cd /opt
git clone https://github.com/aisuites/novo_iamkt.git iamkt
cd iamkt

# Configurar variáveis
cp .env.example .env.development
nano .env.development  # Editar valores críticos

# Atualizar domínio no docker-compose.yml
nano docker-compose.yml  # Alterar labels do Traefik

# Build e deploy
make setup
docker compose build
make up

# Aguardar 60 segundos
sleep 60
```

### 4️⃣ Configurar Django (5 min)

```bash
cd /opt/iamkt

# Migrations
make migrate

# Criar superusuário
docker exec -it iamkt_web python manage.py createsuperuser

# Coletar estáticos
docker exec iamkt_web python manage.py collectstatic --noinput
```

### 5️⃣ Migrar Dados (10-30 min)

```bash
cd /opt/iamkt

# Opção A: Script automatizado
bash scripts/deploy_migrate.sh
# Escolher opção 4 (migração completa)

# Opção B: Manual
# No servidor ANTIGO:
docker exec -t iamkt_postgres pg_dump -U iamkt_user -Fc iamkt_db > /tmp/backup.dump
scp /tmp/backup.dump usuario@novo-servidor:/tmp/

# No servidor NOVO:
cat /tmp/backup.dump | docker exec -i iamkt_postgres pg_restore -U iamkt_user -d iamkt_db --clean --if-exists
docker compose restart iamkt_web
```

---

## ✅ VALIDAR

```bash
cd /opt/iamkt

# Validação automatizada
bash scripts/deploy_validate.sh seu-dominio.com

# Testes rápidos
curl https://seu-dominio.com/health/
curl https://seu-dominio.com/admin/
docker ps | grep iamkt
make logs
```

---

## 🔑 VARIÁVEIS CRÍTICAS

**Editar em `.env.development`:**

```bash
# Gerar secrets
openssl rand -hex 32  # Para SECRET_KEY
openssl rand -hex 32  # Para N8N_WEBHOOK_SECRET

# Configurar obrigatoriamente:
SECRET_KEY=<secret-gerado>
ALLOWED_HOSTS=seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com
SITE_URL=https://seu-dominio.com
DATABASE_URL=postgresql://iamkt_user:SENHA_SEGURA@iamkt_postgres:5432/iamkt_db

# AWS S3 (obrigatório)
AWS_ACCESS_KEY_ID=sua-key
AWS_SECRET_ACCESS_KEY=sua-secret
AWS_STORAGE_BUCKET_NAME=seu-bucket

# OpenAI (obrigatório)
OPENAI_API_KEY=sua-key

# N8N
N8N_WEBHOOK_SECRET=<secret-gerado>
N8N_ALLOWED_IPS=IP_DO_N8N

# Email
EMAIL_HOST=smtp.provedor.com
EMAIL_HOST_USER=seu-email
EMAIL_HOST_PASSWORD=sua-senha
```

---

## 🆘 PROBLEMAS COMUNS

### Containers não iniciam

```bash
docker compose logs
docker compose down
docker compose up -d --force-recreate
```

### Erro de permissão

```bash
sudo chown -R $USER:$USER /opt/apps/iamkt
sudo chown -R 1000:1000 /opt/apps/iamkt/app/media
```

### PostgreSQL não conecta

```bash
docker logs iamkt_postgres
docker exec iamkt_postgres pg_isready -U iamkt_user
```

### HTTPS não funciona

```bash
docker logs traefik
docker network inspect traefik_proxy
# Verificar labels no docker-compose.yml
```

---

## 📚 DOCUMENTAÇÃO COMPLETA

- **Guia Detalhado:** `/opt/iamkt/docs/DEPLOY_NOVO_SERVIDOR.md`
- **Checklist:** `/opt/iamkt/docs/DEPLOY_CHECKLIST.md`
- **Scripts:** `/opt/iamkt/scripts/`

---

## 🎯 COMANDOS ÚTEIS

```bash
# Makefile
make help          # Ver comandos
make up            # Iniciar
make down          # Parar
make logs          # Ver logs
make shell         # Shell Django
make migrate       # Migrations
make backup        # Backup DB

# Docker
docker ps                              # Status
docker compose logs -f iamkt_web       # Logs
docker compose restart iamkt_web       # Reiniciar
docker exec iamkt_web bash             # Shell

# Validação
bash scripts/deploy_validate.sh seu-dominio.com
```

---

**Tempo total estimado: 40-70 minutos**

**Boa sorte! 🚀**
