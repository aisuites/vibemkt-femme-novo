# Alteração: Remoção de URL Hardcoded — APP_BASE_URL

**Data:** 2026-02-19  
**Autor:** Cascade (pair programming)  
**Branch:** main  

---

## Problema

A URL de callback enviada ao N8N no fluxo de **geração de pautas** estava hardcoded no código:

```python
# ANTES — app/apps/pautas/views_gerar_pauta.py (linha 68)
'webhook_return_url': f'https://iamkt-femmeintegra.aisuites.com.br/pautas/webhook/n8n/?organization_id={organization.id}&user_id={request.user.id}&rede_social={rede_social}'
```

Isso causava dois problemas:
1. O domínio `iamkt-femmeintegra.aisuites.com.br` não é o domínio real da aplicação (`vibemkt.aisuites.com.br`).
2. Qualquer mudança de domínio exigiria alteração direta no código.

---

## Solução

Introduzir a variável de ambiente `APP_BASE_URL` e usá-la para construir a URL dinamicamente, combinada com `reverse()` do Django para garantir o path correto do endpoint.

---

## Arquivos Alterados

### 1. `app/sistema/settings/base.py`

Adicionada leitura da nova variável de ambiente `APP_BASE_URL`:

```python
# ANTES
# N8N INTEGRATION
N8N_WEBHOOK_FUNDAMENTOS = config('N8N_WEBHOOK_FUNDAMENTOS', default='')
...

# DEPOIS
# URL base da aplicação (usada para montar callbacks internos)
APP_BASE_URL = config('APP_BASE_URL', default='https://vibemkt.aisuites.com.br').rstrip('/')

# N8N INTEGRATION
N8N_WEBHOOK_FUNDAMENTOS = config('N8N_WEBHOOK_FUNDAMENTOS', default='')
...
```

---

### 2. `.env.example`

Documentada a nova variável de ambiente:

```env
# URL base da aplicação (usada para montar callbacks internos enviados ao N8N)
APP_BASE_URL=https://vibemkt.aisuites.com.br
```

> **Ação necessária:** Adicionar `APP_BASE_URL=https://vibemkt.aisuites.com.br` no `.env.development` e no `.env` de produção.

---

### 3. `app/apps/pautas/views_gerar_pauta.py`

**Import adicionado:**

```python
# ANTES
from django.conf import settings
import requests

# DEPOIS
from django.conf import settings
from django.urls import reverse
import requests
```

**URL do callback corrigida:**

```python
# ANTES
'webhook_return_url': f'https://iamkt-femmeintegra.aisuites.com.br/pautas/webhook/n8n/?organization_id={organization.id}&user_id={request.user.id}&rede_social={rede_social}'

# DEPOIS
'webhook_return_url': f"{settings.APP_BASE_URL}{reverse('pautas:n8n_webhook')}?organization_id={organization.id}&user_id={request.user.id}&rede_social={rede_social}"
```

**Como funciona:**
- `settings.APP_BASE_URL` → lido do `.env` (ex: `https://vibemkt.aisuites.com.br`)
- `reverse('pautas:n8n_webhook')` → resolve o path `/pautas/webhook/n8n/` via roteamento Django
- Resultado final: `https://vibemkt.aisuites.com.br/pautas/webhook/n8n/?organization_id=X&user_id=Y&rede_social=Z`

---

## Como Configurar

Adicione ao `.env.development`:

```env
APP_BASE_URL=https://vibemkt.aisuites.com.br
```

Após adicionar, reinicie o container:

```bash
docker compose -f /opt/vibemkt/docker-compose.yml up -d --force-recreate vibemkt_web
```

---

## O que NÃO foi alterado

- Lógica de negócio do fluxo de geração de pautas
- Endpoint receptor `/pautas/webhook/n8n/` (sem alterações)
- Payload enviado ao N8N (apenas o valor de `webhook_return_url` foi corrigido)
- Nenhum outro fluxo (posts, knowledge) foi tocado nesta alteração
