# DEPLOY VIA GITHUB - IAMKT

**Repositório:** https://github.com/aisuites/novo_iamkt  
**Data:** 10/02/2026  
**Versão:** 1.0

---

## 🚀 DEPLOY RÁPIDO (1 COMANDO)

### Opção 1: Script Automatizado

```bash
# Baixar e executar script de setup
curl -fsSL https://raw.githubusercontent.com/aisuites/novo_iamkt/main/scripts/deploy_setup.sh | sudo bash

# Logout e login
exit
ssh usuario@servidor

# Clonar repositório
cd /opt
sudo git clone https://github.com/aisuites/novo_iamkt.git iamkt
cd iamkt
sudo chown -R $USER:$USER /opt/iamkt

# Configurar e iniciar
cp .env.example .env.development
nano .env.development  # Editar variáveis críticas
make up
```

---

## 📦 VANTAGENS DO DEPLOY VIA GITHUB

### ✅ Facilidades

1. **Versionamento:** Todo código rastreado e versionado
2. **Rollback fácil:** `git checkout <commit>` para voltar versões
3. **Atualizações simples:** `git pull` para atualizar
4. **Colaboração:** Múltiplos desenvolvedores podem contribuir
5. **CI/CD:** Possibilidade de automatizar testes e deploy
6. **Backup automático:** Código sempre seguro no GitHub

### 🔄 Fluxo de Trabalho

```
Desenvolvimento Local → Commit → Push → Pull no Servidor → Restart
```

---

## 🛠️ CONFIGURAÇÃO INICIAL

### 1. Configurar Git no Servidor

```bash
# Configurar usuário
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@dominio.com"

# Configurar credenciais (opcional)
git config --global credential.helper store
```

### 2. Autenticação GitHub

**Opção A: HTTPS com Token (Recomendado)**

```bash
# Gerar token em: https://github.com/settings/tokens
# Permissões: repo (full control)

# Ao fazer git clone, usar:
git clone https://TOKEN@github.com/aisuites/novo_iamkt.git iamkt

# Ou configurar credenciais:
git config --global credential.helper store
git pull  # Digitar token quando solicitado
```

**Opção B: SSH (Mais Seguro)**

```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu-email@dominio.com"

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# Adicionar em: https://github.com/settings/keys

# Clonar via SSH
git clone git@github.com:aisuites/novo_iamkt.git iamkt
```

---

## 📥 CLONE E SETUP

### Clone Completo

```bash
cd /opt
sudo git clone https://github.com/aisuites/novo_iamkt.git iamkt
cd iamkt

# Ajustar permissões
sudo chown -R $USER:$USER /opt/iamkt

# Verificar status
git status
git branch
git log --oneline -5
```

### Clone de Branch Específico

```bash
# Clonar branch específico
git clone -b nome-do-branch https://github.com/aisuites/novo_iamkt.git iamkt

# Ou trocar branch após clone
cd /opt/iamkt
git checkout nome-do-branch
```

---

## 🔄 ATUALIZAÇÃO DA APLICAÇÃO

### Atualização Simples

```bash
cd /opt/iamkt

# Backup antes de atualizar
docker exec -t iamkt_postgres pg_dump -U iamkt_user -Fc iamkt_db > /opt/backups/iamkt/backup_$(date +%Y%m%d_%H%M%S).dump

# Atualizar código
git pull origin main

# Verificar mudanças
git log --oneline -5
git diff HEAD~1 HEAD

# Rebuild se necessário
docker compose build

# Aplicar migrations
docker exec iamkt_web python manage.py migrate

# Coletar estáticos
docker exec iamkt_web python manage.py collectstatic --noinput

# Reiniciar
docker compose restart iamkt_web iamkt_celery
```

### Atualização com Verificação

```bash
cd /opt/iamkt

# Ver o que mudou antes de atualizar
git fetch origin
git log HEAD..origin/main --oneline

# Ver diferenças
git diff HEAD origin/main

# Atualizar
git pull origin main

# Verificar se precisa rebuild
# (se mudou Dockerfile, requirements.txt, etc)
docker compose build

# Reiniciar
docker compose restart
```

---

## 🔙 ROLLBACK

### Voltar para Versão Anterior

```bash
cd /opt/iamkt

# Ver histórico de commits
git log --oneline -10

# Voltar para commit específico
git checkout <commit-hash>

# Ou voltar 1 commit
git checkout HEAD~1

# Rebuild e reiniciar
docker compose build
docker compose restart

# Para voltar ao último commit
git checkout main
git pull
```

### Rollback com Tag

```bash
# Listar tags
git tag

# Voltar para tag específica
git checkout v1.0.0

# Rebuild e reiniciar
docker compose build
docker compose restart
```

---

## 🌿 GERENCIAMENTO DE BRANCHES

### Trabalhar com Branches

```bash
cd /opt/iamkt

# Listar branches
git branch -a

# Criar e trocar para nova branch
git checkout -b desenvolvimento

# Trocar entre branches
git checkout main
git checkout desenvolvimento

# Atualizar branch
git pull origin desenvolvimento
```

### Deploy de Branch Específico

```bash
# Servidor de desenvolvimento
cd /opt/iamkt
git checkout desenvolvimento
git pull origin desenvolvimento
docker compose restart

# Servidor de produção
cd /opt/iamkt
git checkout main
git pull origin main
docker compose restart
```

---

## 🔍 VERIFICAÇÃO E DEBUG

### Verificar Estado do Repositório

```bash
cd /opt/iamkt

# Status atual
git status

# Branch atual
git branch

# Último commit
git log -1

# Commits recentes
git log --oneline -10

# Ver mudanças não commitadas
git diff

# Ver arquivos modificados
git status --short
```

### Resolver Conflitos

```bash
cd /opt/iamkt

# Se houver conflitos ao fazer pull
git pull origin main

# Ver arquivos em conflito
git status

# Descartar mudanças locais e usar versão do GitHub
git reset --hard origin/main

# Ou manter mudanças locais
git stash
git pull origin main
git stash pop
```

---

## 🤖 AUTOMAÇÃO COM GITHUB ACTIONS (FUTURO)

### Exemplo de Workflow CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/iamkt
            git pull origin main
            docker compose build
            docker exec iamkt_web python manage.py migrate
            docker compose restart iamkt_web iamkt_celery
```

---

## 📋 CHECKLIST DE DEPLOY VIA GITHUB

### Primeira Vez

- [ ] Git instalado no servidor
- [ ] Git configurado (user.name, user.email)
- [ ] Autenticação configurada (HTTPS token ou SSH key)
- [ ] Repositório clonado em `/opt/iamkt`
- [ ] Permissões ajustadas
- [ ] `.env.development` configurado
- [ ] Docker compose funcionando

### Atualizações

- [ ] Backup do banco de dados
- [ ] `git pull origin main`
- [ ] Verificar mudanças: `git log`
- [ ] Rebuild se necessário: `docker compose build`
- [ ] Migrations: `docker exec iamkt_web python manage.py migrate`
- [ ] Estáticos: `docker exec iamkt_web python manage.py collectstatic`
- [ ] Restart: `docker compose restart`
- [ ] Testar aplicação

---

## 🔐 SEGURANÇA

### Boas Práticas

1. **Nunca commitar:**
   - `.env` ou `.env.development`
   - Senhas ou tokens
   - Chaves privadas
   - Dados sensíveis

2. **Usar `.gitignore`:**
   ```
   .env*
   *.log
   __pycache__/
   *.pyc
   media/
   staticfiles/
   ```

3. **Proteger credenciais:**
   - Usar GitHub Secrets para CI/CD
   - Usar variáveis de ambiente
   - Nunca hardcode

---

## 📞 COMANDOS ÚTEIS

```bash
# Status completo
cd /opt/iamkt && git status && git log -1

# Atualização rápida
cd /opt/iamkt && git pull && docker compose restart

# Ver mudanças antes de atualizar
cd /opt/iamkt && git fetch && git log HEAD..origin/main

# Forçar atualização (descarta mudanças locais)
cd /opt/iamkt && git fetch && git reset --hard origin/main && docker compose restart

# Ver tamanho do repositório
cd /opt/iamkt && du -sh .git

# Limpar cache do git
git gc --aggressive --prune=now
```

---

## 🆘 TROUBLESHOOTING

### Erro: "Permission denied"

```bash
# Ajustar permissões
sudo chown -R $USER:$USER /opt/iamkt
```

### Erro: "Authentication failed"

```bash
# Reconfigurar credenciais
git config --global credential.helper store
git pull  # Digitar token novamente
```

### Erro: "Conflitos ao fazer pull"

```bash
# Descartar mudanças locais
git reset --hard origin/main

# Ou salvar mudanças locais
git stash
git pull
git stash pop
```

### Repositório muito grande

```bash
# Clone shallow (apenas último commit)
git clone --depth 1 https://github.com/aisuites/novo_iamkt.git iamkt

# Buscar histórico completo depois (se necessário)
cd /opt/iamkt
git fetch --unshallow
```

---

## 📚 REFERÊNCIAS

- **Repositório:** https://github.com/aisuites/novo_iamkt
- **Git Docs:** https://git-scm.com/doc
- **GitHub Docs:** https://docs.github.com
- **Deploy Docs:** `/opt/iamkt/docs/DEPLOY_NOVO_SERVIDOR.md`

---

**Última atualização:** 10/02/2026
