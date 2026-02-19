# Registro de Alterações — Sessão 2026-02-19

**Data:** 2026-02-19  
**Autor:** Cascade (pair programming)  
**Branch:** main  
**Commits:** `8e0c551`, `b9fbf28`, `4af8c48`

---

## Alteração 1 — Remoção de URL Hardcoded (APP_BASE_URL)

**Commit:** `8e0c551`

### Problema

A URL de callback enviada ao N8N no fluxo de **geração de pautas** estava hardcoded no código:

```python
# ANTES — app/apps/pautas/views_gerar_pauta.py (linha 68)
'webhook_return_url': f'https://iamkt-femmeintegra.aisuites.com.br/pautas/webhook/n8n/?organization_id={organization.id}&user_id={request.user.id}&rede_social={rede_social}'
```

Problemas:
1. O domínio `iamkt-femmeintegra.aisuites.com.br` não é o domínio real da aplicação (`vibemkt.aisuites.com.br`).
2. Qualquer mudança de domínio exigiria alteração direta no código.

### Solução

Introduzir a variável de ambiente `APP_BASE_URL` e usá-la para construir a URL dinamicamente, combinada com `reverse()` do Django.

### Arquivos Alterados

#### `app/sistema/settings/base.py`

```python
# ADICIONADO (linha 214)
APP_BASE_URL = config('APP_BASE_URL', default='https://vibemkt.aisuites.com.br').rstrip('/')
```

#### `.env.example`

```env
# URL base da aplicação (usada para montar callbacks internos enviados ao N8N)
APP_BASE_URL=https://vibemkt.aisuites.com.br
```

#### `app/apps/pautas/views_gerar_pauta.py`

Import adicionado:
```python
from django.urls import reverse
```

URL do callback corrigida:
```python
# ANTES
'webhook_return_url': f'https://iamkt-femmeintegra.aisuites.com.br/pautas/webhook/n8n/?...'

# DEPOIS
'webhook_return_url': f"{settings.APP_BASE_URL}{reverse('pautas:n8n_webhook')}?organization_id={organization.id}&user_id={request.user.id}&rede_social={rede_social}"
```

**Como funciona:**
- `settings.APP_BASE_URL` → lido do `.env` (ex: `https://vibemkt.aisuites.com.br`)
- `reverse('pautas:n8n_webhook')` → resolve o path `/pautas/webhook/n8n/` via roteamento Django
- Resultado: `https://vibemkt.aisuites.com.br/pautas/webhook/n8n/?organization_id=X&user_id=Y&rede_social=Z`

### Configuração necessária

Adicione ao `.env.development`:
```env
APP_BASE_URL=https://vibemkt.aisuites.com.br
```

---

## Alteração 2 — Correção de Import em content/tasks.py (Celery)

**Commit:** `b9fbf28`

### Problema

O Celery falhava ao iniciar com `ImportError`:

```
cannot import name 'Post' from 'apps.content.models'
```

O model `Post` não existe em `apps.content.models` — ele está em `apps.posts.models`.

### Arquivo Alterado

#### `app/apps/content/tasks.py`

```python
# ANTES (linha 11-13)
from apps.content.models import (
    Pauta, IAModelUsage, ContentMetrics, TrendMonitor
)
from apps.content.models import Post  # ← ERRADO

# DEPOIS
from apps.content.models import (
    Pauta, IAModelUsage, ContentMetrics, TrendMonitor
)
from apps.posts.models import Post  # ← CORRETO
```

### Impacto

Sem essa correção, o Celery não iniciava, bloqueando todos os fluxos assíncronos da aplicação (geração de pautas, posts, etc.).

---

## Alteração 3 — Correção do Bucket S3 (AWS_BUCKET_NAME)

**Commit:** `4af8c48`

### Problema

O upload de arquivos (logos, imagens de referência, fontes) falhava com `Failed to fetch` no browser.

**Causa raiz:** O `S3Service` (`apps/core/services/s3_service.py`) usa `settings.AWS_BUCKET_NAME` para gerar as presigned URLs, mas o default estava configurado para `iamkt-uploads` — bucket que não existe/não é acessível com as credenciais da aplicação.

O bucket real e acessível é `vibemkt-femme-arquivos`, que estava corretamente configurado em `AWS_STORAGE_BUCKET_NAME`, mas esse setting não era usado pelo `S3Service`.

**Dois settings conflitantes em `settings/base.py`:**

| Setting | Valor anterior | Usado por |
|---|---|---|
| `AWS_STORAGE_BUCKET_NAME` | `vibemkt-femme-arquivos` ✅ | `S3Manager` (utils/s3.py) — código legado/não usado |
| `AWS_BUCKET_NAME` | `iamkt-uploads` ❌ | `S3Service` (core/services) — código ativo |

### Arquivos Alterados

#### `app/sistema/settings/base.py`

```python
# ANTES (linha 205)
AWS_BUCKET_NAME = config('AWS_BUCKET_NAME', default='iamkt-uploads')

# DEPOIS
AWS_BUCKET_NAME = config('AWS_BUCKET_NAME', default='vibemkt-femme-arquivos')
```

#### `.env.example`

```env
# ANTES
AWS_STORAGE_BUCKET_NAME=iamkt-assets-dev

# DEPOIS
AWS_BUCKET_NAME=iamkt-assets-dev
```

### Configuração necessária

Adicione/atualize no `.env.development`:
```env
AWS_BUCKET_NAME=vibemkt-femme-arquivos
AWS_ACCESS_KEY_ID=<sua-chave>
AWS_SECRET_ACCESS_KEY=<seu-secret>
AWS_REGION=us-east-1
```

---

## Alteração 4 — Configuração de CORS no Bucket S3

**Realizada diretamente no Console AWS (sem commit de código)**

### Problema

Mesmo com o bucket correto, o browser bloqueava o PUT direto para a presigned URL com `Failed to fetch`. O browser envia um preflight `OPTIONS` antes do `PUT` — sem CORS configurado no bucket, o S3 rejeitava esse preflight.

### Solução

Configuração de CORS aplicada no bucket `vibemkt-femme-arquivos` via **AWS Console → S3 → Permissions → Cross-origin resource sharing (CORS)**:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": ["https://vibemkt.aisuites.com.br"],
        "ExposeHeaders": ["ETag", "x-amz-server-side-encryption", "x-amz-request-id"],
        "MaxAgeSeconds": 3600
    }
]
```

### Verificação

Preflight testado via `curl` — resposta confirmada:
```
Access-Control-Allow-Origin: https://vibemkt.aisuites.com.br
Access-Control-Allow-Methods: GET, PUT, POST, DELETE, HEAD
Access-Control-Allow-Headers: content-type, x-amz-server-side-encryption, x-amz-storage-class,
                              x-amz-meta-original-name, x-amz-meta-organization-id,
                              x-amz-meta-category, x-amz-meta-upload-timestamp
Access-Control-Max-Age: 3600
```

> **Nota:** A IAM user `vibemkt-femme` não tem permissão `s3:PutBucketCORS` nem `s3:GetBucketCORS`. Qualquer alteração futura no CORS deve ser feita por um usuário com permissões de admin no Console AWS.

---

## Alteração 5 — População da KnowledgeBase FEMME

**Realizada via Django shell (sem commit de código — dados no banco)**

### O que foi feito

Populados todos os blocos da `KnowledgeBase` para a organização FEMME (`organization_id=1`, `knowledge_base_id=1`) via Django shell.

**Resultado:** Completude = **85%**

### Dados inseridos

**Bloco 1 — Identidade Institucional:**
- `nome_empresa`, `missao`, `visao`, `valores`, `descricao_produto`

**Bloco 2 — Público-Alvo:**
- `publico_externo`

**Bloco 3 — Posicionamento:**
- `posicionamento`, `diferenciais`, `proposta_valor`

**Bloco 4 — Tom de Voz:**
- `tom_voz_externo`

**Bloco 5 — Paleta de Cores** (model `ColorPalette`):

| Nome | Hex | Tipo |
|---|---|---|
| Roxo Principal | `#512375` | primary |
| Rosa Claro | `#e9c2db` | secondary |
| Verde Claro | `#f1f6df` | accent |

**Bloco 6 — Redes Sociais** (model `SocialNetwork`):
- Instagram, Facebook, LinkedIn, YouTube

**Bloco 7 — Fontes Confiáveis:**
- `fontes_confiaveis` (ONA, B Corp)

### Observação sobre ColorPalette

O model `ColorPalette` possui unique constraint em `(knowledge_base_id, name)`. O campo `name` é obrigatório e deve ser único por knowledge base. Ao criar cores via shell ou código, sempre fornecer um `name` descritivo.

---

## Como Reiniciar a Aplicação

```bash
docker compose -f /opt/vibemkt/docker-compose.yml up -d --force-recreate vibemkt_web vibemkt_celery
```

## O que NÃO foi alterado

- Lógica de negócio dos fluxos de geração de pautas e posts
- Endpoint receptor `/pautas/webhook/n8n/`
- Estrutura dos models (nenhuma migration foi criada)
- Configurações de Redis, Celery broker/backend
