# Guia Completo: Upload S3 com Django + Service Layer

## Versão 4.0 - Híbrida (FastAPI + Django + Multi-tenant)

**Data:** 27/01/2026  
**Versão:** 4.0 Híbrida  
**Status:** ✅ COMPLETO

---

## 📋 Sobre Este Guia

Este é um guia híbrido que combina:
- ✅ **Tutorial educacional** do zero (criação de conta AWS)
- ✅ **Arquitetura Django** com Service Layer (SOLID principles)
- ✅ **Código pronto** para produção
- ✅ **Integração** com models Django existentes
- ✅ **Multi-tenant** com isolamento de organizações

**Complemento:** `guia-referencia-aws-cli.md` - Consulta rápida de comandos AWS CLI

---

## 📑 Índice

### Parte 1: Fundamentos
1. [Introdução e Arquitetura](#1-introdução-e-arquitetura)
2. [Estimativa de Custos](#2-estimativa-de-custos)
3. [Decisões Arquiteturais](#3-decisões-arquiteturais)

### Parte 2: Setup AWS
4. [Configurar Conta AWS](#4-configurar-conta-aws)
5. [Criar e Configurar Bucket S3](#5-criar-e-configurar-bucket-s3)
6. [Configurar IAM e Permissões](#6-configurar-iam-e-permissões)

### Parte 3: Implementação Django
7. [Service Layer (S3Service)](#7-implementar-service-layer)
8. [Views Django](#8-implementar-views-django)
9. [URLs e Rotas](#9-configurar-urls)
10. [Frontend JavaScript](#10-implementar-frontend)

### Parte 4: Features Avançadas
11. [Preview e Lazy Loading](#11-preview-e-lazy-loading)
12. [Validações Avançadas](#12-validações-avançadas)
13. [Integração com Models](#13-integração-com-models-existentes)

### Parte 5: Testes e Deploy
14. [Testes de Segurança](#14-testes-de-segurança)
15. [Deploy para Produção](#15-deploy-para-produção)
16. [Monitoring e Manutenção](#16-monitoring-e-manutenção)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Introdução e Arquitetura

### 1.1 O que vamos construir

Um sistema completo de upload de arquivos para AWS S3 integrado ao Django, usando **Presigned URLs** e **Service Layer Pattern**.

**Componentes:**
```
Django Application
├── Service Layer (S3Service)       ← Lógica de S3 centralizada
├── Views Django                    ← Endpoints HTTP
├── Models (Logo, ReferenceImage)   ← Já existentes, vamos integrar
└── Frontend JavaScript             ← Classes reutilizáveis
```

### 1.2 Fluxo Completo

```
┌─────────────┐
│   Browser   │
│  (Cliente)  │
└──────┬──────┘
       │
       │ 1. POST /logo/upload-url/ (fileName, fileType, fileSize)
       ▼
┌─────────────────────┐
│   Django View       │
│  (Autenticação)     │
└──────┬──────────────┘
       │
       │ 2. Chama service
       ▼
┌─────────────────────┐
│    S3Service        │
│  (Validação +       │
│   Presigned URL)    │
└──────┬──────────────┘
       │
       │ 3. Retorna URL temporária
       ▼
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 4. PUT direto para S3 (arquivo)
       ▼
┌─────────────┐
│   AWS S3    │
└──────┬──────┘
       │
       │ 5. Confirma upload (200 OK)
       ▼
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 6. POST /logo/create/ (s3_key, metadata)
       ▼
┌─────────────────────┐
│   Django View       │
│  (Cria registro     │
│   Logo no DB)       │
└─────────────────────┘
```

**Vantagens:**
- ✅ Arquivo não passa pelo servidor Django
- ✅ Escalável (S3 gerencia o tráfego)
- ✅ Seguro (URLs temporárias)
- ✅ Rápido (upload direto)

### 1.3 Arquitetura Multi-tenant

**Estrutura S3:**
```
seu-bucket-name/
├── org-1/                          ← Organização 1
│   ├── logos/
│   │   ├── 1706356800000-abc123-logo.png
│   │   └── 1706356900000-def456-brand.svg
│   ├── references/
│   │   ├── 1706357000000-ghi789-produto.jpg
│   │   └── 1706357100000-jkl012-mockup.png
│   └── fonts/
│       ├── 1706357200000-mno345-Roboto.ttf
│       └── 1706357300000-pqr678-OpenSans.woff2
├── org-2/                          ← Organização 2
│   ├── logos/
│   └── references/
└── org-3/                          ← Organização 3
    └── logos/
```

**Segurança:**
- ✅ Cada organização só acessa `org-{id}/`
- ✅ Django valida `organization_id` em cada request
- ✅ S3Service valida prefixo correto
- ✅ IAM policy permite apenas operações necessárias

---

## 2. Estimativa de Custos

### 2.1 Custos Mensais (Região us-east-1)

**Cenário Básico: 10 organizações, 100 uploads/org/mês**
- Armazenamento (50 GB): **$1.15/mês**
- Requisições PUT (1.000): **$0.01/mês**
- Requisições GET (10.000): **$0.04/mês**
- Transferência OUT (100 GB): **$9.00/mês**
- **TOTAL: ~$10.20/mês**

**Cenário Médio: 100 organizações, 100 uploads/org/mês**
- Armazenamento (500 GB): **$11.50/mês**
- Requisições PUT (10.000): **$0.05/mês**
- Requisições GET (100.000): **$0.40/mês**
- Transferência OUT (1 TB): **$90.00/mês**
- **TOTAL: ~$101.95/mês**

**Cenário Alto: 1000 organizações, 100 uploads/org/mês**
- Armazenamento (5 TB): **$115.00/mês**
- Requisições PUT (100.000): **$0.50/mês**
- Requisições GET (1M): **$4.00/mês**
- Transferência OUT (10 TB): **$900.00/mês**
- **TOTAL: ~$1.019,50/mês**

### 2.2 Otimizações de Custo

**1. Lifecycle Policies (Reduz até 80%):**
```bash
# Mover arquivos antigos para Glacier após 90 dias
# Glacier: $0.004/GB/mês (vs $0.023 Standard)
# Economia: 83% em armazenamento
```

**2. CloudFront (Reduz transferência):**
```bash
# Cache de arquivos estáticos
# Reduz requisições GET diretas ao S3
# Economia: ~50% em transferência
```

**3. Compressão de Imagens:**
```python
# Comprimir antes do upload
# Reduz tamanho em até 70%
# Economia: Storage + Transferência
```

---

## 3. Decisões Arquiteturais

### 3.1 Por que Service Layer?

**❌ Abordagem Ruim (sem Service Layer):**
```python
# views.py - CÓDIGO DUPLICADO
def upload_logo(request):
    # 50 linhas de código S3
    s3_client = boto3.client('s3', ...)
    presigned_url = s3_client.generate_presigned_url(...)
    # ...

def upload_reference(request):
    # MESMAS 50 linhas DUPLICADAS
    s3_client = boto3.client('s3', ...)
    presigned_url = s3_client.generate_presigned_url(...)
    # ...

def upload_font(request):
    # MESMAS 50 linhas DUPLICADAS NOVAMENTE
    s3_client = boto3.client('s3', ...)
    presigned_url = s3_client.generate_presigned_url(...)
    # ...
```

**Problemas:**
- ❌ Código duplicado (DRY violation)
- ❌ Bug precisa ser corrigido em 3 lugares
- ❌ Difícil de testar
- ❌ Difícil de manter

**✅ Abordagem Boa (com Service Layer):**
```python
# services/s3_service.py - CÓDIGO CENTRALIZADO
class S3Service:
    @staticmethod
    def generate_presigned_upload_url(...):
        # 50 linhas de código UMA VEZ SÓ

# views.py - USA O SERVICE
def upload_logo(request):
    url = S3Service.generate_presigned_upload_url(
        folder='logos', ...  # ← Único parâmetro diferente
    )

def upload_reference(request):
    url = S3Service.generate_presigned_upload_url(
        folder='references', ...  # ← Único parâmetro diferente
    )

def upload_font(request):
    url = S3Service.generate_presigned_upload_url(
        folder='fonts', ...  # ← Único parâmetro diferente
    )
```

**Vantagens:**
- ✅ **DRY:** Código uma vez só
- ✅ **Manutenível:** Bug corrigido em 1 lugar
- ✅ **Testável:** Service isolado
- ✅ **Reutilizável:** Qualquer view pode usar
- ✅ **SOLID:** Single Responsibility Principle

### 3.2 Por que Presigned URLs?

**❌ Abordagem Ruim (upload via Django):**
```python
def upload_file(request):
    file = request.FILES['file']  # ← Arquivo passa pelo Django
    # Django recebe 100MB de arquivo
    # Consome memória do servidor
    # Lento para usuário
    s3_client.upload_fileobj(file, 'bucket', 'key')
```

**Problemas:**
- ❌ Arquivo passa pelo servidor Django (lento)
- ❌ Consome memória/CPU do servidor
- ❌ Não escala (muitos uploads simultâneos travam)
- ❌ Timeout em arquivos grandes

**✅ Abordagem Boa (Presigned URL):**
```python
def get_upload_url(request):
    # Django apenas gera URL (rápido, 50ms)
    presigned_url = S3Service.generate_presigned_upload_url(...)
    return JsonResponse({'url': presigned_url})

# Usuário faz upload DIRETO para S3
# Django não vê o arquivo
# S3 gerencia o upload
```

**Vantagens:**
- ✅ **Rápido:** Upload direto para S3
- ✅ **Escalável:** S3 gerencia milhões de uploads
- ✅ **Eficiente:** Django não processa arquivo
- ✅ **Seguro:** URL expira em 5 minutos

### 3.3 Estrutura de Pastas S3

**Opção escolhida:**
```
org-{id}/{folder}/{timestamp}-{random}-{filename}.{ext}
```

**Exemplos:**
```
org-1/logos/1706356800000-abc123def456-logo-principal.png
org-1/references/1706357000000-ghi789jkl012-mockup-produto.jpg
org-2/fonts/1706357200000-mno345pqr678-Roboto-Bold.ttf
```

**Por quê essa estrutura?**

✅ **Isolamento por organização:**
```bash
# Backup de uma organização
aws s3 sync s3://bucket/org-1/ ./backup-org-1/

# Deletar tudo de uma organização
aws s3 rm s3://bucket/org-1/ --recursive

# IAM policy simples
"Resource": "arn:aws:s3:::bucket/org-1/*"
```

✅ **Organização por tipo:**
```bash
# Listar apenas logos
aws s3 ls s3://bucket/org-1/logos/

# Listar apenas referências
aws s3 ls s3://bucket/org-1/references/
```

✅ **Nome único garantido:**
```
timestamp (milissegundos) + random (32 chars) = colisão impossível
```

---

## 4. Configurar Conta AWS

### 4.1 Criar Conta AWS (se não tiver)

**Via Console Web:**

1. Acesse: https://aws.amazon.com
2. Clique em **"Criar uma conta da AWS"**
3. Preencha:
   - E-mail
   - Nome da conta
   - Senha (mín. 8 caracteres)
4. Tipo de conta: **Pessoal** ou **Profissional**
5. Informações de contato
6. Informações de pagamento (cartão de crédito)
7. Verificação de identidade (SMS)
8. Plano de suporte: **Básico (Gratuito)**

**Resposta esperada:** E-mail de confirmação em 24h

### 4.2 Acessar Console AWS

1. https://console.aws.amazon.com
2. **"Fazer login no console"**
3. **"Usuário raiz"**
4. E-mail e senha
5. **"Entrar"**

**Resposta esperada:** Dashboard da AWS

### 4.3 Selecionar Região

1. Canto superior direito → Nome da região
2. Escolha:
   - **us-east-1** (Norte da Virgínia) - Mais barata
   - **sa-east-1** (São Paulo) - Menor latência, +30% custo
3. Anote a região

**Para este guia, usaremos: us-east-1**

---

## 5. Criar e Configurar Bucket S3

### 5.1 Via Console AWS (Recomendado para primeira vez)

**Passo 1: Acessar S3**
1. Barra de busca → digite "S3"
2. Clique em **S3**

**Passo 2: Criar Bucket**
1. **"Criar bucket"**
2. **Nome:** `iamkt-uploads` (ou seu nome único)
3. **Região:** us-east-1
4. **Propriedade do objeto:** ACLs desabilitadas
5. **Acesso público:** ✅ Bloquear todo acesso público
6. **Versionamento:** ✅ Habilitar
7. **Criptografia:** ✅ SSE-S3
8. **"Criar bucket"**

**Resposta esperada:** Mensagem verde de sucesso

**Passo 3: Configurar CORS**
1. Clique no bucket criado
2. Aba **"Permissões"**
3. Seção **"CORS"** → **"Editar"**
4. Cole:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["PUT", "POST", "GET"],
        "AllowedOrigins": [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "https://seu-dominio.com"
        ],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

5. **"Salvar alterações"**

**IMPORTANTE:** Substitua `https://seu-dominio.com` pelo seu domínio de produção.

### 5.2 Via AWS CLI (Rápido para reproduzir)

**Pré-requisito:** AWS CLI instalado e configurado (ver Guia Referência)

```bash
# 1. Criar bucket
aws s3 mb s3://iamkt-uploads --region us-east-1

# 2. Habilitar versionamento
aws s3api put-bucket-versioning \
    --bucket iamkt-uploads \
    --versioning-configuration Status=Enabled

# 3. Habilitar criptografia
aws s3api put-bucket-encryption \
    --bucket iamkt-uploads \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'

# 4. Configurar CORS
cat > cors.json << 'EOF'
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["PUT", "POST", "GET"],
        "AllowedOrigins": [
            "http://localhost:8000",
            "https://seu-dominio.com"
        ],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
EOF

aws s3api put-bucket-cors \
    --bucket iamkt-uploads \
    --cors-configuration file://cors.json

# 5. Verificar
aws s3api get-bucket-cors --bucket iamkt-uploads
```

### 5.3 Lifecycle Policies (Opcional mas Recomendado)

**Benefício:** Reduz custos em até 80%

```bash
cat > lifecycle.json << 'EOF'
{
    "Rules": [
        {
            "Id": "MoveToGlacierAfter90Days",
            "Status": "Enabled",
            "Filter": {"Prefix": ""},
            "Transitions": [{
                "Days": 90,
                "StorageClass": "GLACIER"
            }]
        },
        {
            "Id": "DeleteOldVersionsAfter30Days",
            "Status": "Enabled",
            "Filter": {"Prefix": ""},
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 30
            }
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket iamkt-uploads \
    --lifecycle-configuration file://lifecycle.json
```

**O que faz:**
- Arquivos com +90 dias → Glacier (80% mais barato)
- Versões antigas → Deletadas após 30 dias

---

## 6. Configurar IAM e Permissões

### 6.1 Criar Política IAM

**Via Console:**

1. IAM → **"Políticas"** → **"Criar política"**
2. Aba **"JSON"**
3. Cole (substitua `iamkt-uploads`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3Operations",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::iamkt-uploads/*"
        },
        {
            "Sid": "AllowListBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::iamkt-uploads"
        }
    ]
}
```

4. **"Próximo"**
5. **Nome:** `IamktS3UploadPolicy`
6. **"Criar política"**

**Via CLI:**

```bash
cat > iam-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::iamkt-uploads/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::iamkt-uploads"
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name IamktS3UploadPolicy \
    --policy-document file://iam-policy.json
```

### 6.2 Criar Usuário IAM

**Via Console:**

1. IAM → **"Usuários"** → **"Criar usuário"**
2. **Nome:** `iamkt-upload-api-user`
3. **"Próximo"**
4. **"Anexar políticas diretamente"**
5. Buscar: `IamktS3UploadPolicy`
6. Marcar a checkbox
7. **"Criar usuário"**

**Via CLI:**

```bash
# Criar usuário
aws iam create-user --user-name iamkt-upload-api-user

# Obter ID da conta
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Anexar política
aws iam attach-user-policy \
    --user-name iamkt-upload-api-user \
    --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/IamktS3UploadPolicy
```

### 6.3 Criar Chaves de Acesso

**Via Console:**

1. IAM → Usuários → `iamkt-upload-api-user`
2. Aba **"Credenciais de segurança"**
3. **"Criar chave de acesso"**
4. **"Aplicação em execução fora da AWS"**
5. **"Criar chave de acesso"**
6. **⚠️ SALVE AGORA:**
   - Access Key ID
   - Secret Access Key
7. **"Baixar arquivo .csv"**

**Via CLI:**

```bash
aws iam create-access-key --user-name iamkt-upload-api-user
```

**Resposta esperada:**
```json
{
    "AccessKey": {
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Status": "Active"
    }
}
```

**⚠️ CRÍTICO:** Salve essas credenciais IMEDIATAMENTE. Você não poderá vê-las novamente.

```bash
# Salvar em arquivo seguro (NÃO commitar no Git!)
cat > .aws-credentials.txt << EOF
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EOF

chmod 600 .aws-credentials.txt
```

---

## 7. Implementar Service Layer

### 7.1 Estrutura de Diretórios

```
seu_projeto_django/
├── apps/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── s3_service.py        ← CRIAR ESTE
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_validators.py   ← CRIAR ESTE
│   └── knowledge/
│       ├── models.py                 ← JÁ EXISTE
│       ├── views.py                  ← MODIFICAR
│       └── urls.py                   ← MODIFICAR
└── config/
    └── settings.py                   ← MODIFICAR
```

### 7.2 Configurar Django Settings

**Arquivo:** `config/settings.py`

```python
# AWS S3 Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'iamkt-uploads')

# Validar credenciais AWS em desenvolvimento
if DEBUG:
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise ImproperlyConfigured(
            "AWS credentials missing. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY in environment variables."
        )
```

**Arquivo:** `.env`

```env
# AWS S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_BUCKET_NAME=iamkt-uploads
```

**Arquivo:** `.gitignore`

```bash
# Adicionar ao .gitignore
.env
.aws-credentials.txt
```

### 7.3 Instalar Dependências

```bash
pip install boto3==1.34.0
pip freeze > requirements.txt
```

### 7.4 Criar File Validators

**Arquivo:** `apps/core/utils/file_validators.py`

```python
"""
Validadores de arquivo reutilizáveis
"""
from typing import Tuple, Optional


class FileValidator:
    """Validações de arquivo"""
    
    # Tipos de arquivo permitidos por categoria
    ALLOWED_TYPES = {
        'logos': {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/svg+xml': 'svg',
            'image/webp': 'webp',
        },
        'references': {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
        },
        'fonts': {
            'font/ttf': 'ttf',
            'font/otf': 'otf',
            'font/woff': 'woff',
            'font/woff2': 'woff2',
        },
        'documents': {
            'application/pdf': 'pdf',
        },
    }
    
    # Tamanhos máximos por categoria (em MB)
    MAX_FILE_SIZES = {
        'logos': 5,
        'references': 10,
        'fonts': 2,
        'documents': 20,
    }
    
    @classmethod
    def validate_file_type(
        cls,
        file_type: str,
        category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida tipo de arquivo para categoria
        
        Returns:
            (is_valid, error_message)
        """
        allowed_types = cls.ALLOWED_TYPES.get(category, {})
        
        if not allowed_types:
            return False, f"Categoria inválida: {category}"
        
        if file_type not in allowed_types:
            allowed_list = ', '.join(allowed_types.keys())
            return False, (
                f"Tipo '{file_type}' não permitido para {category}. "
                f"Aceitos: {allowed_list}"
            )
        
        return True, None
    
    @classmethod
    def validate_file_size(
        cls,
        file_size: int,
        category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida tamanho do arquivo
        
        Args:
            file_size: Tamanho em bytes
            category: Categoria do arquivo
            
        Returns:
            (is_valid, error_message)
        """
        max_size_mb = cls.MAX_FILE_SIZES.get(category, 10)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, (
                f"Arquivo muito grande. "
                f"Máximo para {category}: {max_size_mb}MB"
            )
        
        if file_size <= 0:
            return False, "Arquivo vazio"
        
        return True, None
    
    @classmethod
    def get_extension(cls, file_type: str, category: str) -> Optional[str]:
        """Retorna extensão para o tipo de arquivo"""
        allowed_types = cls.ALLOWED_TYPES.get(category, {})
        return allowed_types.get(file_type)
    
    @classmethod
    def validate_file(
        cls,
        file_type: str,
        file_size: int,
        category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validação completa de arquivo
        
        Returns:
            (is_valid, error_message)
        """
        # Validar tipo
        is_valid, error = cls.validate_file_type(file_type, category)
        if not is_valid:
            return False, error
        
        # Validar tamanho
        is_valid, error = cls.validate_file_size(file_size, category)
        if not is_valid:
            return False, error
        
        return True, None
```

### 7.5 Criar S3Service

**Arquivo:** `apps/core/services/s3_service.py`

```python
"""
Service Layer para operações S3
Centraliza toda lógica de upload/download/delete
"""
import boto3
import secrets
import time
import re
from datetime import datetime
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from typing import Dict, Optional, Tuple
from apps.core.utils.file_validators import FileValidator


class S3Service:
    """
    Service centralizado para operações AWS S3
    
    Usage:
        # Gerar URL para upload
        data = S3Service.generate_presigned_upload_url(
            file_name='logo.png',
            file_type='image/png',
            file_size=512000,
            category='logos',
            organization_id=1
        )
        
        # Gerar URL para download
        url = S3Service.generate_presigned_download_url(
            s3_key='org-1/logos/123-abc-logo.png'
        )
        
        # Deletar arquivo
        success = S3Service.delete_file(
            s3_key='org-1/logos/123-abc-logo.png'
        )
    """
    
    # Configurações
    PRESIGNED_URL_EXPIRATION = 300  # 5 minutos
    DOWNLOAD_URL_EXPIRATION = 3600  # 1 hora
    
    _s3_client = None  # Cache do cliente S3
    
    @classmethod
    def _get_s3_client(cls):
        """Retorna cliente S3 configurado (cached)"""
        if cls._s3_client is None:
            config = Config(
                region_name=settings.AWS_REGION,
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
            
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
        
        return cls._s3_client
    
    # Templates padrão por categoria
    DEFAULT_TEMPLATES = {
        'logos': 'org-{org_id}/{category}/{timestamp}-{random}-{name}.{ext}',
        'references': 'org-{org_id}/{category}/{timestamp}-{random}-{name}.{ext}',
        'fonts': 'org-{org_id}/{category}/{name}.{ext}',  # Sem timestamp para fontes
        'documents': 'org-{org_id}/{category}/{date}/{timestamp}-{random}.{ext}',
        'posts': 'org-{org_id}/posts/{date}/{random}.{ext}',
    }
    
    @classmethod
    def generate_secure_filename(
        cls,
        original_name: str,
        file_type: str,
        category: str,
        organization_id: int,
        template: Optional[str] = None,
        custom_data: Optional[Dict] = None
    ) -> str:
        """
        Gera nome único e seguro para arquivo usando template flexível
        
        Args:
            original_name: Nome original do arquivo
            file_type: MIME type
            category: Categoria (logos, references, fonts, documents, posts)
            organization_id: ID da organização
            template: Template customizado (opcional)
            custom_data: Dados customizados para o template (opcional)
            
        Variáveis Disponíveis:
            {org_id}    - ID da organização
            {category}  - Categoria do arquivo
            {timestamp} - Timestamp em milissegundos
            {random}    - String aleatória (32 chars)
            {ext}       - Extensão do arquivo
            {name}      - Nome sanitizado do arquivo
            {date}      - Data YYYYMMDD
            {datetime}  - Data e hora YYYYMMDDHHmmss
            + Qualquer chave em custom_data
            
        Examples:
            # Logo padrão
            generate_secure_filename('logo.png', 'image/png', 'logos', 1)
            # → org-1/logos/1706356800000-abc123def456-logo.png
            
            # Fonte com nome específico
            generate_secure_filename(
                'Roboto.ttf', 'font/ttf', 'fonts', 1,
                template='org-{org_id}/fontes/{font_name}_{variant}.{ext}',
                custom_data={'font_name': 'Roboto', 'variant': 'Bold'}
            )
            # → org-1/fontes/Roboto_Bold.ttf
            
            # Post com data
            generate_secure_filename(
                'post.png', 'image/png', 'posts', 1,
                custom_data={'date': '20260127'}
            )
            # → org-1/posts/20260127/abc123def456.png
        
        Returns:
            Caminho completo do arquivo no S3
        """
        from datetime import datetime as dt
        
        # Obter extensão
        extension = FileValidator.get_extension(file_type, category)
        if not extension:
            extension = 'bin'
        
        # Sanitizar nome original
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', original_name)
        name_without_ext = sanitized.rsplit('.', 1)[0][:50]
        
        # Preparar variáveis disponíveis
        now = dt.now()
        variables = {
            'org_id': organization_id,
            'category': category,
            'timestamp': int(time.time() * 1000),
            'random': secrets.token_hex(16),
            'ext': extension,
            'name': name_without_ext,
            'date': now.strftime('%Y%m%d'),
            'datetime': now.strftime('%Y%m%d%H%M%S'),
        }
        
        # Adicionar variáveis customizadas
        if custom_data:
            variables.update(custom_data)
        
        # Usar template customizado ou padrão da categoria
        if template is None:
            template = cls.DEFAULT_TEMPLATES.get(
                category,
                'org-{org_id}/{category}/{timestamp}-{random}-{name}.{ext}'
            )
        
        # Substituir variáveis no template
        try:
            filename = template.format(**variables)
        except KeyError as e:
            raise ValueError(
                f"Variável '{e.args[0]}' não encontrada. "
                f"Disponíveis: {', '.join(variables.keys())}"
            )
        
        # Validar caminho gerado (segurança)
        if '..' in filename or '//' in filename:
            raise ValueError("Path gerado contém caracteres suspeitos")
        
        return filename
    
    @classmethod
    def generate_presigned_upload_url(
        cls,
        file_name: str,
        file_type: str,
        file_size: int,
        category: str,
        organization_id: int,
        template: Optional[str] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Gera Presigned URL para upload de arquivo
        
        Args:
            file_name: Nome do arquivo
            file_type: MIME type
            file_size: Tamanho em bytes
            category: Categoria (logos, references, fonts, documents, posts)
            organization_id: ID da organização
            template: Template customizado para nomenclatura (opcional)
            custom_data: Dados customizados para template (opcional)
            
        Returns:
            {
                'upload_url': str,  # URL para fazer PUT
                's3_key': str,      # Chave do arquivo no S3
                'expires_in': int   # Segundos até expirar
            }
            
        Raises:
            ValueError: Se validação falhar
            Exception: Se erro ao gerar URL
            
        Examples:
            # Upload simples (usa template padrão)
            data = generate_presigned_upload_url(
                'logo.png', 'image/png', 500000, 'logos', 1
            )
            
            # Upload com nomenclatura customizada
            data = generate_presigned_upload_url(
                'Roboto.ttf', 'font/ttf', 200000, 'fonts', 1,
                template='org-{org_id}/fontes/{font_family}_{variant}.{ext}',
                custom_data={'font_family': 'Roboto', 'variant': 'Bold'}
            )
        """
        # Validar arquivo
        is_valid, error_msg = FileValidator.validate_file(
            file_type, file_size, category
        )
        if not is_valid:
            raise ValueError(error_msg)
        
        # Gerar nome seguro com template
        s3_key = cls.generate_secure_filename(
            original_name=file_name,
            file_type=file_type,
            category=category,
            organization_id=organization_id,
            template=template,
            custom_data=custom_data
        )
        
        # Obter cliente S3
        s3_client = cls._get_s3_client()
        
        try:
            # Gerar Presigned URL
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': settings.AWS_BUCKET_NAME,
                    'Key': s3_key,
                    'ContentType': file_type,
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'INTELLIGENT_TIERING',
                    'Metadata': {
                        'original-name': file_name,
                        'organization-id': str(organization_id),
                        'category': category,
                        'upload-timestamp': str(int(time.time()))
                    }
                },
                ExpiresIn=cls.PRESIGNED_URL_EXPIRATION,
                HttpMethod='PUT'
            )
            
            return {
                'upload_url': presigned_url,
                's3_key': s3_key,
                'expires_in': cls.PRESIGNED_URL_EXPIRATION
            }
            
        except ClientError as e:
            raise Exception(f"Erro AWS ao gerar URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao gerar URL de upload: {str(e)}")
    
    @classmethod
    def generate_presigned_download_url(
        cls,
        s3_key: str,
        expires_in: Optional[int] = None
    ) -> str:
        """
        Gera Presigned URL para download/visualização
        
        Args:
            s3_key: Chave do arquivo no S3
            expires_in: Tempo de expiração em segundos (padrão: 1 hora)
            
        Returns:
            URL temporária para download
            
        Raises:
            Exception: Se erro ao gerar URL
        """
        if expires_in is None:
            expires_in = cls.DOWNLOAD_URL_EXPIRATION
        
        s3_client = cls._get_s3_client()
        
        try:
            return s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': settings.AWS_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=expires_in,
                HttpMethod='GET'
            )
        except ClientError as e:
            raise Exception(f"Erro AWS ao gerar URL de download: {str(e)}")
    
    @classmethod
    def delete_file(cls, s3_key: str) -> bool:
        """
        Deleta arquivo do S3
        
        Args:
            s3_key: Chave do arquivo no S3
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        s3_client = cls._get_s3_client()
        
        try:
            s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key
            )
            return True
        except ClientError:
            return False
    
    @classmethod
    def get_public_url(cls, s3_key: str) -> str:
        """
        Retorna URL pública do arquivo (para armazenar no banco)
        
        Args:
            s3_key: Chave do arquivo no S3
            
        Returns:
            URL pública (não temporária)
        """
        return (
            f"https://{settings.AWS_BUCKET_NAME}.s3."
            f"{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        )
    
    @classmethod
    def validate_organization_access(
        cls,
        s3_key: str,
        organization_id: int
    ) -> bool:
        """
        Valida que organização tem acesso ao arquivo
        
        Args:
            s3_key: Chave do arquivo
            organization_id: ID da organização
            
        Returns:
            True se acesso permitido
            
        Raises:
            ValueError: Se acesso negado
        """
        expected_prefix = f"org-{organization_id}/"
        
        if not s3_key.startswith(expected_prefix):
            raise ValueError(
                f"Acesso negado: arquivo não pertence à organização {organization_id}. "
                f"Esperado prefixo '{expected_prefix}', recebido '{s3_key}'"
            )
        
        return True
```

---

## 8. Implementar Views Django

### 8.1 Views para Logo

**Arquivo:** `apps/knowledge/views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from apps.core.services.s3_service import S3Service
from apps.knowledge.models import Logo
import json


@login_required
@require_http_methods(["POST"])
def generate_logo_upload_url(request):
    """
    Gera Presigned URL para upload de logo
    
    POST /knowledge/logo/upload-url/
    Body:
        {
            "fileName": "logo.png",
            "fileType": "image/png",
            "fileSize": 512000,
            "template": "org-{org_id}/logos/v{version}/{name}.{ext}",  // Opcional
            "customData": {"version": "2"}  // Opcional
        }
    
    Response:
        {
            "success": true,
            "data": {
                "upload_url": "https://...",
                "s3_key": "org-1/logos/...",
                "expires_in": 300
            }
        }
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        
        # Obter organização do request
        # Assumindo que você tem middleware que adiciona organization
        organization_id = request.organization.id
        
        # Obter template e custom_data (opcionais)
        template = data.get('template')
        custom_data = data.get('customData', {})
        
        # Gerar Presigned URL via service
        presigned_data = S3Service.generate_presigned_upload_url(
            file_name=data['fileName'],
            file_type=data['fileType'],
            file_size=int(data['fileSize']),
            category='logos',
            organization_id=organization_id,
            template=template,
            custom_data=custom_data
        )
        
        return JsonResponse({
            'success': True,
            'data': presigned_data
        })
        
    except ValueError as e:
        # Erro de validação
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
        
    except KeyError as e:
        return JsonResponse({
            'success': False,
            'error': f'Campo obrigatório ausente: {e}'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro interno ao gerar URL'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def create_logo(request):
    """
    Cria registro de Logo após upload bem-sucedido no S3
    
    POST /knowledge/logo/create/
    Body:
        {
            "name": "Logo Principal",
            "logoType": "principal",
            "s3Key": "org-1/logos/123-abc-logo.png",
            "fileFormat": "png",
            "isPrimary": true
        }
    
    Response:
        {
            "success": true,
            "data": {
                "id": 123,
                "name": "Logo Principal",
                "preview_url": "https://..."
            }
        }
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        
        # Validar acesso ao s3_key
        organization_id = request.organization.id
        S3Service.validate_organization_access(
            data['s3Key'],
            organization_id
        )
        
        # Obter knowledge base
        kb = request.organization.knowledge_base
        
        # Criar Logo
        logo = Logo.objects.create(
            knowledge_base=kb,
            name=data['name'],
            logo_type=data['logoType'],
            s3_key=data['s3Key'],
            s3_url=S3Service.get_public_url(data['s3Key']),
            file_format=data['fileFormat'],
            is_primary=data.get('isPrimary', False),
            uploaded_by=request.user
        )
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(logo.s3_key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': logo.id,
                'name': logo.name,
                'logoType': logo.logo_type,
                'previewUrl': preview_url
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
        
    except KeyError as e:
        return JsonResponse({
            'success': False,
            'error': f'Campo obrigatório ausente: {e}'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao criar logo'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_logo_preview_url(request, logo_id):
    """
    Gera URL temporária para preview de logo
    
    GET /knowledge/logo/<id>/preview/
    
    Response:
        {
            "success": true,
            "data": {
                "preview_url": "https://..."
            }
        }
    """
    try:
        # Buscar logo
        logo = Logo.objects.get(
            id=logo_id,
            knowledge_base__organization=request.organization
        )
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(logo.s3_key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'previewUrl': preview_url
            }
        })
        
    except Logo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Logo não encontrado'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de preview'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_logo(request, logo_id):
    """
    Deleta logo (banco + S3)
    
    DELETE /knowledge/logo/<id>/
    
    Response:
        {
            "success": true,
            "message": "Logo deletado com sucesso"
        }
    """
    try:
        # Buscar logo
        logo = Logo.objects.get(
            id=logo_id,
            knowledge_base__organization=request.organization
        )
        
        # Deletar do S3
        S3Service.delete_file(logo.s3_key)
        
        # Deletar do banco
        logo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Logo deletado com sucesso'
        })
        
    except Logo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Logo não encontrado'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar logo'
        }, status=500)
```

### 8.2 Views para ReferenceImage

**Arquivo:** `apps/knowledge/views.py` (continuar)

```python
from apps.knowledge.models import ReferenceImage


@login_required
@require_http_methods(["POST"])
def generate_reference_upload_url(request):
    """
    Gera Presigned URL para upload de referência
    
    Similar a generate_logo_upload_url, mas category='references'
    """
    try:
        data = json.loads(request.body)
        organization_id = request.organization.id
        
        presigned_data = S3Service.generate_presigned_upload_url(
            file_name=data['fileName'],
            file_type=data['fileType'],
            file_size=int(data['fileSize']),
            category='references',  # ← Diferença aqui
            organization_id=organization_id
        )
        
        return JsonResponse({
            'success': True,
            'data': presigned_data
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except KeyError as e:
        return JsonResponse({'success': False, 'error': f'Campo ausente: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Erro interno'}, status=500)


@login_required
@require_http_methods(["POST"])
def create_reference_image(request):
    """
    Cria registro de ReferenceImage após upload
    """
    try:
        data = json.loads(request.body)
        organization_id = request.organization.id
        
        # Validar acesso
        S3Service.validate_organization_access(data['s3Key'], organization_id)
        
        kb = request.organization.knowledge_base
        
        # Criar ReferenceImage
        ref = ReferenceImage.objects.create(
            knowledge_base=kb,
            title=data['title'],
            description=data.get('description', ''),
            s3_key=data['s3Key'],
            s3_url=S3Service.get_public_url(data['s3Key']),
            file_size=data['fileSize'],
            width=data.get('width', 0),
            height=data.get('height', 0),
            perceptual_hash=data.get('perceptualHash', ''),
            uploaded_by=request.user
        )
        
        preview_url = S3Service.generate_presigned_download_url(ref.s3_key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': ref.id,
                'title': ref.title,
                'previewUrl': preview_url
            }
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except KeyError as e:
        return JsonResponse({'success': False, 'error': f'Campo ausente: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Erro ao criar referência'}, status=500)
```

---

## 9. Configurar URLs

**Arquivo:** `apps/knowledge/urls.py`

```python
from django.urls import path
from apps.knowledge import views

app_name = 'knowledge'

urlpatterns = [
    # Logo URLs
    path(
        'logo/upload-url/',
        views.generate_logo_upload_url,
        name='logo_upload_url'
    ),
    path(
        'logo/create/',
        views.create_logo,
        name='logo_create'
    ),
    path(
        'logo/<int:logo_id>/preview/',
        views.get_logo_preview_url,
        name='logo_preview'
    ),
    path(
        'logo/<int:logo_id>/',
        views.delete_logo,
        name='logo_delete'
    ),
    
    # ReferenceImage URLs
    path(
        'reference/upload-url/',
        views.generate_reference_upload_url,
        name='reference_upload_url'
    ),
    path(
        'reference/create/',
        views.create_reference_image,
        name='reference_create'
    ),
]
```

**Arquivo:** `config/urls.py` (principal)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('knowledge/', include('apps.knowledge.urls')),
    # ... outras URLs
]
```

---

## 10. Implementar Frontend

### 10.1 JavaScript Reutilizável

**Arquivo:** `static/js/s3-uploader.js`

```javascript
/**
 * S3Uploader - Classe reutilizável para upload via Presigned URLs
 * 
 * Uso:
 *   const uploader = new S3Uploader('/knowledge/logo/upload-url/', '/knowledge/logo/create/');
 *   const result = await uploader.upload(file, { name: 'Logo Principal', logoType: 'principal' });
 */

class S3Uploader {
    constructor(uploadUrlEndpoint, createRecordEndpoint) {
        this.uploadUrlEndpoint = uploadUrlEndpoint;
        this.createRecordEndpoint = createRecordEndpoint;
        this.onProgress = null;  // Callback para progresso
    }
    
    /**
     * Faz upload completo do arquivo
     * @param {File} file - Arquivo do input
     * @param {Object} metadata - Metadados para criar registro
     * @returns {Promise<Object>} Dados do registro criado
     */
    async upload(file, metadata = {}) {
        try {
            // 1. Obter Presigned URL
            this.updateProgress(10, 'Obtendo permissão...');
            const presignedData = await this.getPresignedUrl(file);
            
            // 2. Upload para S3
            this.updateProgress(30, 'Enviando arquivo...');
            await this.uploadToS3(presignedData.upload_url, file);
            
            // 3. Criar registro no banco
            this.updateProgress(80, 'Finalizando...');
            const record = await this.createRecord({
                s3Key: presignedData.s3_key,
                fileFormat: file.type.split('/')[1],
                fileSize: file.size,
                ...metadata
            });
            
            this.updateProgress(100, 'Concluído!');
            return record;
            
        } catch (error) {
            throw new Error(`Upload falhou: ${error.message}`);
        }
    }
    
    /**
     * Obtém Presigned URL do backend
     */
    async getPresignedUrl(file) {
        const response = await fetch(this.uploadUrlEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao obter URL');
        }
        
        const result = await response.json();
        return result.data;
    }
    
    /**
     * Faz upload direto para S3
     */
    async uploadToS3(url, file) {
        const response = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': file.type
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro S3: ${response.status}`);
        }
    }
    
    /**
     * Cria registro no banco de dados
     */
    async createRecord(data) {
        const response = await fetch(this.createRecordEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao criar registro');
        }
        
        const result = await response.json();
        return result.data;
    }
    
    /**
     * Atualiza progresso
     */
    updateProgress(percent, message) {
        if (this.onProgress) {
            this.onProgress(percent, message);
        }
    }
    
    /**
     * Obtém cookie CSRF
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}


/**
 * Helper para formatar tamanho de arquivo
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
```

### 10.2 HTML de Exemplo (Logo Upload)

**Arquivo:** `templates/knowledge/logo_upload.html`

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<style>
    .upload-container {
        max-width: 600px;
        margin: 40px auto;
        padding: 30px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .upload-area {
        border: 3px dashed #667eea;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        background: #f8f9ff;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: #f0f1ff;
    }
    
    .upload-area.dragover {
        border-color: #764ba2;
        background: #e8e9ff;
        transform: scale(1.02);
    }
    
    .progress-bar {
        width: 100%;
        height: 30px;
        background: #e0e0e0;
        border-radius: 15px;
        overflow: hidden;
        margin-top: 20px;
        display: none;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        transition: width 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 12px;
    }
    
    .message {
        margin-top: 20px;
        padding: 15px;
        border-radius: 8px;
        display: none;
    }
    
    .message.success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .message.error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
{% endblock %}

{% block content %}
<div class="upload-container">
    <h2>Upload de Logo</h2>
    <p>Selecione ou arraste um arquivo de logo</p>
    
    <!-- Upload Area -->
    <div class="upload-area" id="uploadArea">
        <div style="font-size: 48px; margin-bottom: 10px;">☁️</div>
        <p><strong>Clique ou arraste um arquivo aqui</strong></p>
        <p style="font-size: 12px; color: #666; margin-top: 10px;">
            Formatos aceitos: PNG, JPG, SVG, WebP<br>
            Tamanho máximo: 5MB
        </p>
        <input type="file" id="fileInput" accept="image/png,image/jpeg,image/svg+xml,image/webp" style="display: none;">
    </div>
    
    <!-- Formulário de Metadata -->
    <div id="metadataForm" style="margin-top: 20px; display: none;">
        <div style="margin-bottom: 15px;">
            <label>Nome do Logo:</label>
            <input type="text" id="logoName" class="form-control" placeholder="Ex: Logo Principal" required>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label>Tipo de Logo:</label>
            <select id="logoType" class="form-control">
                <option value="principal">Principal</option>
                <option value="horizontal">Horizontal</option>
                <option value="vertical">Vertical</option>
                <option value="simbolo">Símbolo</option>
            </select>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label>
                <input type="checkbox" id="isPrimary">
                Definir como logo principal
            </label>
        </div>
        
        <button id="uploadBtn" class="btn btn-primary" disabled>
            Fazer Upload
        </button>
    </div>
    
    <!-- Progress Bar -->
    <div class="progress-bar" id="progressBar">
        <div class="progress-fill" id="progressFill">0%</div>
    </div>
    
    <!-- Message -->
    <div class="message" id="message"></div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/s3-uploader.js' %}"></script>
<script>
    // Elementos
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const metadataForm = document.getElementById('metadataForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const message = document.getElementById('message');
    
    let selectedFile = null;
    
    // Criar uploader
    const logoUploader = new S3Uploader(
        '/knowledge/logo/upload-url/',
        '/knowledge/logo/create/'
    );
    
    // Callback de progresso
    logoUploader.onProgress = (percent, text) => {
        progressBar.style.display = 'block';
        progressFill.style.width = percent + '%';
        progressFill.textContent = text || percent + '%';
    };
    
    // Event Listeners
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    uploadBtn.addEventListener('click', handleUpload);
    
    // Funções
    function handleFileSelect(file) {
        // Validar tipo
        const allowedTypes = ['image/png', 'image/jpeg', 'image/svg+xml', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showMessage('Tipo de arquivo não permitido', 'error');
            return;
        }
        
        // Validar tamanho (5MB)
        if (file.size > 5 * 1024 * 1024) {
            showMessage('Arquivo muito grande. Máximo: 5MB', 'error');
            return;
        }
        
        selectedFile = file;
        uploadBtn.disabled = false;
        metadataForm.style.display = 'block';
        
        uploadArea.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
            <p><strong>${file.name}</strong></p>
            <p style="font-size: 12px; color: #666;">
                ${formatFileSize(file.size)} - ${file.type}
            </p>
        `;
        
        hideMessage();
    }
    
    async function handleUpload() {
        if (!selectedFile) return;
        
        // Obter metadata
        const metadata = {
            name: document.getElementById('logoName').value,
            logoType: document.getElementById('logoType').value,
            isPrimary: document.getElementById('isPrimary').checked
        };
        
        if (!metadata.name) {
            showMessage('Digite o nome do logo', 'error');
            return;
        }
        
        uploadBtn.disabled = true;
        hideMessage();
        
        try {
            const result = await logoUploader.upload(selectedFile, metadata);
            
            showMessage('Logo enviado com sucesso! ✅', 'success');
            
            // Reset após 2 segundos
            setTimeout(() => {
                location.reload();
            }, 2000);
            
        } catch (error) {
            showMessage(`Erro: ${error.message}`, 'error');
            uploadBtn.disabled = false;
        }
    }
    
    function showMessage(text, type) {
        message.textContent = text;
        message.className = `message ${type}`;
        message.style.display = 'block';
    }
    
    function hideMessage() {
        message.style.display = 'none';
    }
</script>
{% endblock %}
```

---

**CONTINUA NO PRÓXIMO ARQUIVO...**

Este guia é muito extenso. Vou criar o segundo arquivo complementar com as seções restantes.
