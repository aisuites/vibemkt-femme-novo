# CHECKLIST DE DEPLOY - IAMKT

**Data:** 09/02/2026  
**Versão:** 1.0

---

## 📋 PRÉ-DEPLOY

### Servidor Novo

- [ ] Sistema operacional atualizado (Ubuntu 22.04 LTS ou similar)
- [ ] Hardware atende requisitos mínimos (4GB RAM, 40GB disco)
- [ ] Acesso SSH configurado
- [ ] Usuário com permissões sudo criado
- [ ] Firewall configurado (portas 22, 80, 443)
- [ ] DNS apontando para o novo servidor (se aplicável)

### Servidor Antigo

- [ ] Backup do banco de dados criado
- [ ] Backup de arquivos de mídia criado
- [ ] Backup de arquivos estáticos criado (opcional)
- [ ] Backup de variáveis de ambiente (.env) salvo
- [ ] Lista de integrações externas documentada (N8N, AWS, etc)

---

## 🔧 PREPARAÇÃO DO SERVIDOR

### 1. Instalação de Dependências

```bash
# Executar script automatizado
sudo bash /opt/iamkt/scripts/deploy_setup.sh
```

**OU manualmente:**

- [ ] Docker Engine instalado (24.0+)
- [ ] Docker Compose instalado (2.20+)
- [ ] Git instalado
- [ ] Make instalado
- [ ] Curl/Wget instalado
- [ ] Usuário adicionado ao grupo docker
- [ ] **LOGOUT E LOGIN REALIZADO** (importante!)

### 2. Configuração do Sistema

- [ ] Firewall UFW habilitado e configurado
- [ ] Swap configurado (4GB recomendado)
- [ ] Limites de arquivos aumentados
- [ ] Otimizações de rede aplicadas
- [ ] Docker daemon configurado (logs, storage driver)

### 3. Estrutura de Diretórios

- [ ] `/opt/` existe
- [ ] `/opt/iamkt/` criado
- [ ] `/opt/traefik/` existe (já configurado)
- [ ] `/opt/backups/iamkt/` criado
- [ ] Permissões corretas aplicadas

---

## 🌐 CONFIGURAÇÃO DE INFRAESTRUTURA

### 1. Rede Docker

- [ ] Rede `traefik_proxy` criada
- [ ] Rede verificada: `docker network ls | grep traefik_proxy`

### 2. Traefik (Proxy Reverso)

**IMPORTANTE:** Traefik já está rodando em `/opt/traefik/`

- [ ] Arquivo `.env` com credenciais Cloudflare
- [ ] Arquivo `docker-compose.yml` configurado
- [ ] Cloudflare DNS Challenge configurado
- [ ] Domínio configurado nos labels das aplicações
- [ ] Traefik rodando: `docker ps | grep traefik`
- [ ] Logs verificados: `docker logs traefik`
- [ ] Certificados SSL gerados: `ls /opt/traefik/letsencrypt/`

### 3. Portainer

**IMPORTANTE:** Portainer já está instalado com OAuth2

- [ ] Portainer rodando: `docker ps | grep portainer`
- [ ] OAuth2 Proxy configurado
- [ ] Emails autorizados em `/opt/traefik/oauth2/authenticated-emails.txt`
- [ ] Acessível via: `https://portainer-femmeintegra.aisuites.com.br`

---

## 🚀 DEPLOY DA APLICAÇÃO

### 1. Código Fonte

- [ ] Repositório clonado: `git clone https://github.com/aisuites/novo_iamkt.git /opt/iamkt`
- [ ] Branch correto selecionado: `git branch`
- [ ] Permissões ajustadas: `chown -R $USER:$USER /opt/iamkt`
- [ ] Git configurado: `git config --global user.name` e `user.email`

### 2. Variáveis de Ambiente

- [ ] Arquivo `.env.development` criado (copiar de `.env.example`)
- [ ] `SECRET_KEY` gerado: `openssl rand -hex 32`
- [ ] `ALLOWED_HOSTS` configurado com domínio correto
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] `SITE_URL` configurado
- [ ] `DATABASE_URL` configurado (senha alterada)
- [ ] `AWS_ACCESS_KEY_ID` configurado
- [ ] `AWS_SECRET_ACCESS_KEY` configurado
- [ ] `AWS_STORAGE_BUCKET_NAME` configurado
- [ ] `OPENAI_API_KEY` configurado
- [ ] `GEMINI_API_KEY` configurado (se usar)
- [ ] `N8N_WEBHOOK_SECRET` gerado: `openssl rand -hex 32`
- [ ] `N8N_ALLOWED_IPS` configurado
- [ ] Webhooks N8N configurados
- [ ] Email SMTP configurado
- [ ] Emails de notificação configurados

### 3. Docker Compose

- [ ] Labels do Traefik atualizados com domínio correto
- [ ] Senha do PostgreSQL alterada (se necessário)
- [ ] Recursos (CPU/RAM) ajustados conforme servidor
- [ ] Arquivo validado: `docker compose config`

### 4. Build e Inicialização

- [ ] Setup executado: `make setup`
- [ ] Build realizado: `docker compose build`
- [ ] Containers iniciados: `make up` ou `make solo`
- [ ] Aguardado inicialização (60 segundos)
- [ ] Containers verificados: `docker ps | grep iamkt`
- [ ] Logs verificados: `make logs`

### 5. Migrations e Configuração

- [ ] Migrations executadas: `make migrate`
- [ ] Superusuário criado: `docker exec -it iamkt_web python manage.py createsuperuser`
- [ ] Arquivos estáticos coletados: `docker exec iamkt_web python manage.py collectstatic --noinput`
- [ ] Health check OK: `curl http://localhost:8000/health/`

---

## 📦 MIGRAÇÃO DE DADOS

### 1. Transferência de Backups

**Opção A - Script Automatizado:**
- [ ] Script executado: `bash /opt/iamkt/scripts/deploy_migrate.sh`
- [ ] Opção de migração escolhida (1-4)

**Opção B - Manual:**
- [ ] Backup transferido via SCP
- [ ] Backup de mídia transferido via SCP
- [ ] Arquivos salvos em `/opt/backups/iamkt/`

### 2. Restauração

- [ ] Banco de dados restaurado
- [ ] Arquivos de mídia restaurados
- [ ] Permissões ajustadas: `sudo chown -R 1000:1000 /opt/iamkt/app/media/`
- [ ] Aplicação reiniciada: `docker compose restart iamkt_web`

### 3. Validação de Dados

- [ ] Usuários no banco: `docker exec iamkt_postgres psql -U iamkt_user -d iamkt_db -c "SELECT COUNT(*) FROM auth_user;"`
- [ ] Arquivos de mídia presentes: `ls -lah /opt/iamkt/app/media/`
- [ ] Login no admin funcionando
- [ ] Dados visíveis na aplicação

---

## ✅ VALIDAÇÃO PÓS-DEPLOY

### 1. Validação Automatizada

- [ ] Script executado: `bash /opt/iamkt/scripts/deploy_validate.sh seu-dominio.com`
- [ ] Todos os testes passaram
- [ ] Avisos revisados e corrigidos

### 2. Validação Manual - Containers

- [ ] `iamkt_web` rodando
- [ ] `iamkt_postgres` rodando
- [ ] `iamkt_redis` rodando
- [ ] `iamkt_celery` rodando
- [ ] Health checks OK: `docker ps`

### 3. Validação Manual - Conectividade

- [ ] PostgreSQL acessível: `docker exec iamkt_postgres pg_isready`
- [ ] Redis acessível: `docker exec iamkt_redis redis-cli ping`
- [ ] Django respondendo: `curl http://localhost:8000/health/`
- [ ] Celery funcionando: `docker exec iamkt_celery celery -A sistema inspect ping`

### 4. Validação Manual - Segurança

- [ ] PostgreSQL NÃO exposto externamente: `netstat -tuln | grep 5432`
- [ ] Redis NÃO exposto externamente: `netstat -tuln | grep 6379`
- [ ] Firewall ativo: `sudo ufw status`
- [ ] HTTPS funcionando: `curl -I https://seu-dominio.com`
- [ ] Redirecionamento HTTP → HTTPS funcionando

### 5. Validação Manual - Funcionalidades

- [ ] Login no admin: `https://seu-dominio.com/admin/`
- [ ] Dashboard acessível
- [ ] Upload de arquivo funcionando
- [ ] Geração de post funcionando
- [ ] Webhooks N8N funcionando
- [ ] Envio de email funcionando
- [ ] Celery processando tasks

### 6. Validação Manual - Performance

- [ ] Tempo de resposta aceitável (< 2s)
- [ ] Uso de CPU normal (< 70%)
- [ ] Uso de memória normal (< 80%)
- [ ] Espaço em disco suficiente (> 20% livre)
- [ ] Logs sem erros críticos

---

## 🔒 SEGURANÇA

### Configurações Obrigatórias

- [ ] `SECRET_KEY` único e seguro (32+ caracteres)
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` restrito ao domínio
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] Senhas do banco alteradas (não usar padrão)
- [ ] Firewall configurado (apenas portas necessárias)
- [ ] SSL/TLS habilitado (HTTPS)
- [ ] Headers de segurança configurados (Traefik)

### Boas Práticas

- [ ] Backups automáticos configurados
- [ ] Monitoramento configurado (opcional)
- [ ] Logs centralizados (opcional)
- [ ] Rate limiting configurado (N8N)
- [ ] Secrets não commitados no Git
- [ ] `.env` no `.gitignore`

---

## 📊 MONITORAMENTO

### Logs

- [ ] Logs da aplicação: `docker logs iamkt_web`
- [ ] Logs do Celery: `docker logs iamkt_celery`
- [ ] Logs do PostgreSQL: `docker logs iamkt_postgres`
- [ ] Logs do Traefik: `docker logs traefik`

### Recursos

- [ ] Uso de CPU: `docker stats`
- [ ] Uso de memória: `free -h`
- [ ] Espaço em disco: `df -h`
- [ ] Volumes Docker: `docker system df`

### Health Checks

- [ ] Endpoint health: `curl https://seu-dominio.com/health/`
- [ ] Status containers: `docker ps`
- [ ] Traefik dashboard (se habilitado)

---

## 🔄 PÓS-DEPLOY

### Configurações Finais

- [ ] DNS propagado (verificar: `nslookup seu-dominio.com`)
- [ ] SSL/TLS válido (verificar: `https://www.ssllabs.com/ssltest/`)
- [ ] Backups agendados (cron ou script)
- [ ] Documentação atualizada
- [ ] Equipe notificada

### Limpeza

- [ ] Backups temporários removidos do `/tmp/`
- [ ] Containers órfãos removidos: `docker container prune`
- [ ] Imagens antigas removidas: `docker image prune`
- [ ] Volumes não usados verificados: `docker volume ls`
- [ ] Servidor antigo mantido por período de segurança (7-30 dias)

### Testes de Integração

- [ ] Webhooks N8N testados
- [ ] Geração de conteúdo testada
- [ ] Upload S3 testado
- [ ] Envio de emails testado
- [ ] Notificações testadas

---

## 📞 ROLLBACK (SE NECESSÁRIO)

### Procedimento de Emergência

1. [ ] Reverter DNS para servidor antigo
2. [ ] Parar containers: `cd /opt/iamkt && docker compose down`
3. [ ] Investigar problema nos logs
4. [ ] Corrigir e tentar novamente

### Backup do Servidor Novo

- [ ] Criar backup antes de rollback
- [ ] Documentar problema encontrado
- [ ] Planejar nova tentativa

---

## ✅ CONCLUSÃO

### Checklist Final

- [ ] Todos os containers rodando
- [ ] Todas as validações passaram
- [ ] Aplicação acessível via HTTPS
- [ ] Funcionalidades principais testadas
- [ ] Equipe treinada/notificada
- [ ] Documentação completa
- [ ] Backups configurados

### Próximos Passos

- [ ] Monitorar aplicação por 24-48h
- [ ] Ajustar recursos se necessário
- [ ] Configurar alertas (opcional)
- [ ] Desativar servidor antigo (após período de segurança)

---

**Deploy concluído com sucesso! 🎉**

---

## 📚 REFERÊNCIAS

- Documentação completa: `/opt/iamkt/docs/DEPLOY_NOVO_SERVIDOR.md`
- Scripts de deploy: `/opt/iamkt/scripts/`
- Makefile: `/opt/iamkt/Makefile`
- Docker Compose: `/opt/iamkt/docker-compose.yml`
- Traefik: `/opt/traefik/docker-compose.yml`

---

**Última atualização:** 09/02/2026
