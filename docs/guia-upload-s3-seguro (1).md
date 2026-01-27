# Guia Completo: Upload Seguro de Arquivos para AWS S3

## Introdução

Este guia apresenta um sistema completo e seguro para upload de arquivos do seu sistema para a AWS S3, utilizando **Presigned URLs** (URLs pré-assinadas) para máxima segurança.

### O que vamos construir

Um sistema com dois componentes principais:

1. **Backend (API)**: Gera URLs pré-assinadas para upload direto ao S3
2. **Cliente**: Envia arquivos diretamente para o S3 usando essas URLs

### Fluxo de Funcionamento

```
1. Cliente solicita permissão para upload → Backend (sua API)
2. Backend valida a requisição e tipo de arquivo permitido
3. Backend gera Presigned URL (válida por tempo limitado)
4. Backend retorna URL pré-assinada → Cliente
5. Cliente faz upload direto para S3 usando a URL
6. S3 confirma upload bem-sucedido
7. Cliente recebe URL pública/privada para acessar o arquivo
```

### Vantagens desta Abordagem

- ✅ **Segurança máxima**: Arquivos não passam pelo seu servidor
- ✅ **Escalabilidade**: S3 gerencia o tráfego de arquivos
- ✅ **Controle total**: Você determina quem, quando e o que pode ser enviado
- ✅ **Economia**: Reduz carga no seu servidor
- ✅ **Rastreabilidade**: Logs completos de todas as operações

---

## Estimativa de Custos AWS S3

### Custos Mensais Estimados

**Cenário Básico (até 1.000 uploads/mês):**
- Armazenamento (5 GB): ~$0.12/mês
- Requisições PUT: ~$0.01/mês
- Requisições GET (3.000): ~$0.01/mês
- Transferência de dados (10 GB): ~$0.90/mês
- **TOTAL: ~$1.04/mês**

**Cenário Médio (10.000 uploads/mês):**
- Armazenamento (50 GB): ~$1.15/mês
- Requisições PUT: ~$0.05/mês
- Requisições GET (30.000): ~$0.12/mês
- Transferência de dados (100 GB): ~$9.00/mês
- **TOTAL: ~$10.32/mês**

**Cenário Alto (100.000 uploads/mês):**
- Armazenamento (500 GB): ~$11.50/mês
- Requisições PUT: ~$0.50/mês
- Requisições GET (300.000): ~$1.20/mês
- Transferência de dados (1 TB): ~$90.00/mês
- **TOTAL: ~$103.20/mês**

### Tabela de Preços AWS S3 (Região us-east-1)

| Recurso | Preço |
|---------|-------|
| Armazenamento Standard | $0.023 por GB/mês |
| Requisições PUT/POST | $0.005 por 1.000 requisições |
| Requisições GET | $0.0004 por 1.000 requisições |
| Transferência OUT (internet) | $0.09 por GB |
| Transferência IN | Grátis |

**Nota**: Região São Paulo (sa-east-1) pode ter custos ~30% maiores.

---

## ETAPA 1: Configuração da Conta AWS

### 1.1 Criar Conta AWS (se não tiver)

1. Acesse: https://aws.amazon.com
2. Clique em **"Criar uma conta da AWS"**
3. Preencha:
   - Endereço de e-mail
   - Nome da conta AWS
   - Senha (mínimo 8 caracteres)
4. Clique em **"Continuar"**
5. Escolha tipo de conta: **"Pessoal"** ou **"Profissional"**
6. Preencha informações de contato
7. Adicione informações de pagamento (cartão de crédito)
8. Verifique identidade via SMS
9. Escolha plano de suporte: **"Básico (Gratuito)"**
10. Clique em **"Concluir inscrição"**

**Resposta esperada**: E-mail de confirmação em até 24 horas

### 1.2 Acessar Console AWS

1. Acesse: https://console.aws.amazon.com
2. Clique em **"Fazer login no console"**
3. Selecione **"Usuário raiz"**
4. Digite seu e-mail e senha
5. Clique em **"Entrar"**

**Resposta esperada**: Você verá o Dashboard principal da AWS

### 1.3 Selecionar Região

1. No canto superior direito, clique no nome da região (ex: "Norte da Virgínia")
2. Escolha a região mais próxima:
   - **São Paulo (sa-east-1)**: Para usuários no Brasil
   - **Norte da Virgínia (us-east-1)**: Mais barata, mas maior latência
3. Anote a região escolhida

**Resposta esperada**: A região selecionada aparece no canto superior direito

---

## ETAPA 2: Criar Bucket S3

### 2.1 Acessar S3

1. No console AWS, clique na barra de busca superior
2. Digite **"S3"**
3. Clique em **"S3"** (ícone de balde laranja)

**Resposta esperada**: Você verá a página "Buckets" do S3

### 2.2 Criar Novo Bucket

1. Clique no botão **"Criar bucket"**
2. Preencha os campos:

**Nome do bucket:**
- Digite um nome único globalmente (ex: `seu-sistema-uploads-2025`)
- Use apenas letras minúsculas, números e hífens
- Anote este nome exatamente como digitou

**Região da AWS:**
- Selecione a mesma região da Etapa 1.3

**Configurações de propriedade do objeto:**
- Deixe marcado: **"ACLs desabilitadas (recomendado)"**

**Configurações de bloqueio do acesso público:**
- ⚠️ **IMPORTANTE**: Marque **"Bloquear todo o acesso público"**
- Esta é a configuração mais segura
- Vamos usar Presigned URLs para acesso controlado

**Versionamento de bucket:**
- Deixe **desabilitado** (por enquanto)

**Tags (opcional):**
- Adicione se quiser organizar recursos:
  - Chave: `Projeto`
  - Valor: `SistemaUpload`

**Criptografia padrão:**
- Selecione: **"Habilitar"**
- Tipo: **"Chaves gerenciadas pelo Amazon S3 (SSE-S3)"**
- Esta opção é gratuita e segura

**Bloqueio de objetos:**
- Deixe **desabilitado**

3. Clique em **"Criar bucket"**

**Resposta esperada**: 
- Mensagem verde: "Bucket criado com sucesso: seu-sistema-uploads-2025"
- O bucket aparece na lista

### 2.3 Configurar CORS (Cross-Origin Resource Sharing)

1. Na lista de buckets, clique no nome do seu bucket
2. Clique na aba **"Permissões"**
3. Role até a seção **"Compartilhamento de recursos entre origens (CORS)"**
4. Clique em **"Editar"**
5. Cole a seguinte configuração:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "PUT",
            "POST",
            "GET"
        ],
        "AllowedOrigins": [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://seu-dominio.com"
        ],
        "ExposeHeaders": [
            "ETag"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

6. **Substitua** `https://seu-dominio.com` pelo domínio do seu sistema
7. Clique em **"Salvar alterações"**

**Resposta esperada**: Mensagem "Configuração de CORS salva com sucesso"

---

## ETAPA 3: Criar Usuário IAM e Configurar Permissões

### 3.1 Acessar IAM

1. No console AWS, clique na barra de busca
2. Digite **"IAM"**
3. Clique em **"IAM"**

**Resposta esperada**: Dashboard do IAM Identity Center

### 3.2 Criar Política de Permissões Customizada

1. No menu lateral esquerdo, clique em **"Políticas"**
2. Clique em **"Criar política"**
3. Clique na aba **"JSON"**
4. Cole o seguinte código (substitua `SEU-BUCKET-NAME`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPresignedURLGeneration",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::SEU-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowListBucket",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::SEU-BUCKET-NAME"
        }
    ]
}
```

5. Substitua **todas** as ocorrências de `SEU-BUCKET-NAME` pelo nome do seu bucket
6. Clique em **"Próximo"**
7. Em **"Nome da política"**, digite: `S3PresignedURLPolicy`
8. Em **"Descrição"**, digite: `Permite geração de Presigned URLs para upload no S3`
9. Clique em **"Criar política"**

**Resposta esperada**: Mensagem "Política S3PresignedURLPolicy criada com sucesso"

### 3.3 Criar Usuário IAM

1. No menu lateral, clique em **"Usuários"**
2. Clique em **"Criar usuário"**
3. Em **"Nome do usuário"**, digite: `s3-upload-api-user`
4. Clique em **"Próximo"**
5. Selecione **"Anexar políticas diretamente"**
6. Na barra de busca, digite: `S3PresignedURLPolicy`
7. Marque a checkbox da política criada
8. Clique em **"Próximo"**
9. Revise as informações
10. Clique em **"Criar usuário"**

**Resposta esperada**: Mensagem "Usuário s3-upload-api-user criado com sucesso"

### 3.4 Criar Chaves de Acesso

1. Na lista de usuários, clique em **"s3-upload-api-user"**
2. Clique na aba **"Credenciais de segurança"**
3. Role até **"Chaves de acesso"**
4. Clique em **"Criar chave de acesso"**
5. Selecione: **"Aplicação em execução fora da AWS"**
6. Clique em **"Próximo"**
7. (Opcional) Adicione tag de descrição: `API Upload S3`
8. Clique em **"Criar chave de acesso"**

**⚠️ CRÍTICO - SALVE ESTAS INFORMAÇÕES AGORA:**

9. Você verá:
   - **Access key ID** (ex: `AKIAIOSFODNN7EXAMPLE`)
   - **Secret access key** (ex: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

10. Clique em **"Baixar arquivo .csv"** e salve em local seguro
11. **NÃO COMPARTILHE ESTAS CHAVES COM NINGUÉM**
12. Copie e cole em um gerenciador de senhas ou arquivo criptografado

**Resposta esperada**: Arquivo CSV baixado com as credenciais

---

## ETAPA 4: Implementar Backend (API) em Python

### 4.1 Tecnologia Escolhida

Vamos usar **Python com FastAPI** - framework moderno, rápido e com validação automática de dados.

**Requisitos**:
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 4.2 Criar Ambiente Virtual Python

1. Abra o terminal no diretório do seu projeto
2. Execute:

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

**Resposta esperada**: 
```
(venv) aparece no início da linha do terminal
```

### 4.3 Instalar Dependências Python

1. Com o ambiente virtual ativado, execute:

```bash
pip install fastapi uvicorn boto3 python-dotenv pydantic python-multipart slowapi
```

**Resposta esperada**: 
```
Successfully installed fastapi-0.109.0 uvicorn-0.27.0 boto3-1.34.0 ...
```

2. Criar arquivo `requirements.txt` para documentar dependências:

```bash
pip freeze > requirements.txt
```

### 4.4 Criar Arquivo de Configuração (.env)

1. Na raiz do projeto, crie arquivo `.env`
2. Adicione o seguinte conteúdo:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua-access-key-aqui
AWS_SECRET_ACCESS_KEY=sua-secret-key-aqui
AWS_BUCKET_NAME=seu-bucket-name-aqui

# Server Configuration
PORT=8000
ENVIRONMENT=production

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://seu-dominio.com
MAX_FILE_SIZE_MB=10
PRESIGNED_URL_EXPIRATION_SECONDS=300
```

3. Substitua os valores:
   - `AWS_REGION`: Região do seu bucket
   - `AWS_ACCESS_KEY_ID`: Access Key da Etapa 3.4
   - `AWS_SECRET_ACCESS_KEY`: Secret Key da Etapa 3.4
   - `AWS_BUCKET_NAME`: Nome do seu bucket
   - `ALLOWED_ORIGINS`: Domínios que podem acessar a API

4. **⚠️ IMPORTANTE**: Adicione `.env` ao `.gitignore`

```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

### 4.5 Criar Arquivo Principal da API (main.py)

Crie o arquivo `main.py`:

```python
"""
API Segura para Upload de Arquivos no AWS S3
Utiliza Presigned URLs para máxima segurança
"""

import os
import secrets
import time
import re
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================
# CARREGAR CONFIGURAÇÕES
# ============================================

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
PORT = int(os.getenv('PORT', 8000))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 10))
PRESIGNED_URL_EXPIRATION = int(os.getenv('PRESIGNED_URL_EXPIRATION_SECONDS', 300))

# ============================================
# CONFIGURAÇÃO AWS S3
# ============================================

s3_config = Config(
    region_name=AWS_REGION,
    signature_version='s3v4',
    retries={'max_attempts': 3, 'mode': 'standard'}
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=s3_config
)

# ============================================
# CONFIGURAÇÃO FASTAPI
# ============================================

app = FastAPI(
    title="S3 Upload API",
    description="API segura para upload de arquivos usando AWS S3 Presigned URLs",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=86400  # 24 horas
)

# ============================================
# VALIDAÇÕES E CONFIGURAÇÕES
# ============================================

# Tipos de arquivo permitidos (MIME type -> extensão)
ALLOWED_FILE_TYPES = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'text/plain': 'txt',
    'text/csv': 'csv'
}

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ============================================
# MODELOS PYDANTIC (VALIDAÇÃO AUTOMÁTICA)
# ============================================

class UploadRequest(BaseModel):
    """Modelo para requisição de upload"""
    fileName: str = Field(..., min_length=1, max_length=255, description="Nome do arquivo")
    fileType: str = Field(..., description="MIME type do arquivo")
    fileSize: int = Field(..., gt=0, description="Tamanho do arquivo em bytes")
    
    @validator('fileName')
    def validate_filename(cls, v):
        """Valida nome do arquivo"""
        if not v or not v.strip():
            raise ValueError('Nome do arquivo não pode ser vazio')
        # Remove caracteres perigosos
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', v):
            raise ValueError('Nome do arquivo contém caracteres inválidos')
        return v.strip()
    
    @validator('fileType')
    def validate_filetype(cls, v):
        """Valida tipo do arquivo"""
        if v not in ALLOWED_FILE_TYPES:
            raise ValueError(
                f'Tipo de arquivo não permitido. Tipos aceitos: {", ".join(ALLOWED_FILE_TYPES.keys())}'
            )
        return v
    
    @validator('fileSize')
    def validate_filesize(cls, v):
        """Valida tamanho do arquivo"""
        if v > MAX_FILE_SIZE_BYTES:
            raise ValueError(f'Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE_MB}MB')
        return v


class DownloadRequest(BaseModel):
    """Modelo para requisição de download"""
    key: str = Field(..., min_length=1, description="Chave do arquivo no S3")
    
    @validator('key')
    def validate_key(cls, v):
        """Valida chave do arquivo"""
        if not v.startswith('uploads/'):
            raise ValueError('Chave de arquivo inválida')
        # Previne path traversal
        if '..' in v or '//' in v:
            raise ValueError('Chave de arquivo contém caracteres suspeitos')
        return v


class UploadResponse(BaseModel):
    """Modelo para resposta de upload"""
    success: bool
    data: Optional[dict] = None
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Modelo para resposta de health check"""
    status: str
    timestamp: str
    service: str
    bucket: str
    region: str


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def generate_secure_filename(original_name: str, mime_type: str) -> str:
    """
    Gera nome único e seguro para arquivo
    
    Args:
        original_name: Nome original do arquivo
        mime_type: MIME type do arquivo
        
    Returns:
        Nome seguro do arquivo no formato: uploads/timestamp-random-sanitized.ext
    """
    extension = ALLOWED_FILE_TYPES.get(mime_type, 'bin')
    timestamp = int(time.time() * 1000)  # Timestamp em milissegundos
    random_string = secrets.token_hex(16)  # 32 caracteres hexadecimais
    
    # Sanitizar nome original
    sanitized_name = re.sub(r'[^a-zA-Z0-9._-]', '_', original_name)
    sanitized_name = sanitized_name[:50]  # Limitar tamanho
    
    # Remover extensão do nome original se existir
    name_without_ext = os.path.splitext(sanitized_name)[0]
    
    return f"uploads/{timestamp}-{random_string}-{name_without_ext}.{extension}"


def log_operation(operation: str, details: str):
    """
    Log de operações (em produção, use um logger apropriado)
    
    Args:
        operation: Tipo de operação (UPLOAD, DOWNLOAD, DELETE)
        details: Detalhes da operação
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{operation}] {details}")


# ============================================
# ROTAS DA API
# ============================================

@app.get("/", response_model=dict)
async def root():
    """Rota raiz - informações básicas da API"""
    return {
        "message": "S3 Upload API",
        "version": "1.0.0",
        "docs": "/docs" if ENVIRONMENT != "production" else "disabled",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """
    Health check - verifica se a API está funcionando
    
    Returns:
        Status da API e configurações básicas
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        service="S3 Upload API",
        bucket=AWS_BUCKET_NAME,
        region=AWS_REGION
    )


@app.post("/api/upload/presigned-url", response_model=UploadResponse)
@limiter.limit("100/15minutes")
async def generate_upload_url(request: Request, upload_req: UploadRequest):
    """
    Gera Presigned URL para upload de arquivo
    
    Args:
        upload_req: Dados do arquivo (nome, tipo, tamanho)
        
    Returns:
        URL pré-assinada para upload direto ao S3
        
    Raises:
        HTTPException: Se houver erro na geração da URL
    """
    try:
        # Gerar nome seguro para o arquivo
        secure_filename = generate_secure_filename(
            upload_req.fileName, 
            upload_req.fileType
        )
        
        # Parâmetros para Presigned URL
        params = {
            'Bucket': AWS_BUCKET_NAME,
            'Key': secure_filename,
            'ContentType': upload_req.fileType,
            'ServerSideEncryption': 'AES256',
            'Metadata': {
                'original-name': upload_req.fileName,
                'upload-timestamp': str(int(time.time()))
            }
        }
        
        # Gerar Presigned URL
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
            HttpMethod='PUT'
        )
        
        log_operation("UPLOAD", f"Presigned URL gerada para: {secure_filename}")
        
        return UploadResponse(
            success=True,
            data={
                "uploadUrl": presigned_url,
                "key": secure_filename,
                "expiresIn": PRESIGNED_URL_EXPIRATION
            }
        )
        
    except ClientError as e:
        log_operation("ERROR", f"Erro AWS ao gerar upload URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao comunicar com S3"
        )
    except Exception as e:
        log_operation("ERROR", f"Erro ao gerar upload URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar URL de upload"
        )


@app.post("/api/download/presigned-url", response_model=UploadResponse)
@limiter.limit("200/15minutes")
async def generate_download_url(request: Request, download_req: DownloadRequest):
    """
    Gera Presigned URL para download/visualização de arquivo
    
    Args:
        download_req: Chave do arquivo no S3
        
    Returns:
        URL pré-assinada para download/visualização
        
    Raises:
        HTTPException: Se houver erro na geração da URL
    """
    try:
        # Parâmetros para Presigned URL
        params = {
            'Bucket': AWS_BUCKET_NAME,
            'Key': download_req.key
        }
        
        # Gerar Presigned URL
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params=params,
            ExpiresIn=3600,  # 1 hora
            HttpMethod='GET'
        )
        
        log_operation("DOWNLOAD", f"Presigned URL gerada para: {download_req.key}")
        
        return UploadResponse(
            success=True,
            data={
                "downloadUrl": presigned_url,
                "expiresIn": 3600
            }
        )
        
    except ClientError as e:
        log_operation("ERROR", f"Erro AWS ao gerar download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao comunicar com S3"
        )
    except Exception as e:
        log_operation("ERROR", f"Erro ao gerar download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar URL de download"
        )


@app.delete("/api/file/{key:path}")
@limiter.limit("50/15minutes")
async def delete_file(request: Request, key: str):
    """
    Deleta arquivo do S3 (opcional - implemente autenticação antes de usar!)
    
    Args:
        key: Chave do arquivo no S3
        
    Returns:
        Confirmação de deleção
        
    Raises:
        HTTPException: Se houver erro na deleção
    """
    try:
        # Validações de segurança
        if not key.startswith('uploads/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chave de arquivo inválida"
            )
        
        if '..' in key or '//' in key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chave contém caracteres suspeitos"
            )
        
        # Deletar arquivo
        s3_client.delete_object(
            Bucket=AWS_BUCKET_NAME,
            Key=key
        )
        
        log_operation("DELETE", f"Arquivo deletado: {key}")
        
        return {
            "success": True,
            "message": "Arquivo deletado com sucesso"
        }
        
    except ClientError as e:
        log_operation("ERROR", f"Erro AWS ao deletar arquivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao comunicar com S3"
        )
    except Exception as e:
        log_operation("ERROR", f"Erro ao deletar arquivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao deletar arquivo"
        )


# ============================================
# TRATAMENTO DE ERROS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções não tratadas"""
    log_operation("ERROR", f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Erro interno do servidor"
        }
    )


# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🚀 Iniciando S3 Upload API")
    print("=" * 50)
    print(f"📦 Bucket S3: {AWS_BUCKET_NAME}")
    print(f"🌍 Região: {AWS_REGION}")
    print(f"⏱️  Expiração URLs: {PRESIGNED_URL_EXPIRATION}s")
    print(f"📊 Tamanho máximo: {MAX_FILE_SIZE_MB}MB")
    print(f"🔒 CORS habilitado para: {', '.join(ALLOWED_ORIGINS)}")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=ENVIRONMENT != "production"
    )
```

### 4.6 Testar a API Python

1. Com o ambiente virtual ativado, inicie o servidor:

```bash
python main.py
```

**Resposta esperada**:
```
==================================================
🚀 Iniciando S3 Upload API
==================================================
📦 Bucket S3: seu-bucket-name
🌍 Região: us-east-1
⏱️  Expiração URLs: 300s
📊 Tamanho máximo: 10MB
🔒 CORS habilitado para: http://localhost:3000
==================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

2. Testar endpoint de saúde (em outro terminal):

```bash
curl http://localhost:8000/api/health
```

**Resposta esperada**:
```json
{
  "status": "ok",
  "timestamp": "2025-01-13T10:30:00.000000",
  "service": "S3 Upload API",
  "bucket": "seu-bucket-name",
  "region": "us-east-1"
}
```

3. Acessar documentação automática (Swagger UI):

Abra no navegador: `http://localhost:8000/docs`

**Resposta esperada**: Interface interativa com todas as rotas da API documentadas

---

## ETAPA 5: Implementar Cliente (Frontend)

### 5.1 HTML + JavaScript (Exemplo Simples)

Crie o arquivo `upload-client.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Seguro S3</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
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

        .upload-icon {
            font-size: 60px;
            margin-bottom: 15px;
        }

        input[type="file"] {
            display: none;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin-top: 20px;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .progress-container {
            display: none;
            margin-top: 20px;
        }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
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
            border-radius: 10px;
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

        .file-info {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background: #f8f9ff;
            border-radius: 10px;
            text-align: left;
        }

        .file-info p {
            margin: 5px 0;
            color: #333;
            font-size: 14px;
        }

        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-weight: 600;
            transition: transform 0.2s;
        }

        .download-link:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📤 Upload Seguro para S3</h1>
        <p class="subtitle">Arraste e solte ou clique para selecionar um arquivo</p>

        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">☁️</div>
            <p>Clique ou arraste um arquivo aqui</p>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">
                Tipos aceitos: JPG, PNG, GIF, WebP, PDF, DOC, DOCX, XLS, XLSX<br>
                Tamanho máximo: 10MB
            </p>
            <input type="file" id="fileInput" accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx">
        </div>

        <button class="btn" id="uploadBtn" disabled>Fazer Upload</button>

        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill">0%</div>
            </div>
        </div>

        <div class="message" id="message"></div>

        <div class="file-info" id="fileInfo"></div>
    </div>

    <script>
        // Configuração
        const API_BASE_URL = 'http://localhost:8000/api';
        
        // Elementos DOM
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const message = document.getElementById('message');
        const fileInfo = document.getElementById('fileInfo');

        let selectedFile = null;

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

        uploadBtn.addEventListener('click', uploadFile);

        // Funções
        function handleFileSelect(file) {
            selectedFile = file;
            uploadBtn.disabled = false;
            
            uploadArea.innerHTML = `
                <div class="upload-icon">✅</div>
                <p><strong>${file.name}</strong></p>
                <p style="font-size: 12px; color: #666;">
                    ${formatFileSize(file.size)} - ${file.type}
                </p>
            `;
            
            hideMessage();
            fileInfo.style.display = 'none';
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        async function uploadFile() {
            if (!selectedFile) {
                showMessage('Selecione um arquivo primeiro', 'error');
                return;
            }

            uploadBtn.disabled = true;
            progressContainer.style.display = 'block';
            hideMessage();

            try {
                // Etapa 1: Obter Presigned URL
                updateProgress(10, 'Obtendo URL de upload...');
                
                const presignedResponse = await fetch(`${API_BASE_URL}/upload/presigned-url`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        fileName: selectedFile.name,
                        fileType: selectedFile.type,
                        fileSize: selectedFile.size
                    })
                });

                if (!presignedResponse.ok) {
                    const errorData = await presignedResponse.json();
                    throw new Error(errorData.errors ? errorData.errors.join(', ') : 'Erro ao obter URL');
                }

                const { data } = await presignedResponse.json();
                
                // Etapa 2: Upload para S3
                updateProgress(30, 'Enviando arquivo...');
                
                const uploadResponse = await fetch(data.uploadUrl, {
                    method: 'PUT',
                    body: selectedFile,
                    headers: {
                        'Content-Type': selectedFile.type
                    }
                });

                if (!uploadResponse.ok) {
                    throw new Error('Erro ao fazer upload do arquivo');
                }

                updateProgress(70, 'Gerando link de acesso...');

                // Etapa 3: Obter URL de download
                const downloadResponse = await fetch(`${API_BASE_URL}/download/presigned-url`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        key: data.key
                    })
                });

                if (!downloadResponse.ok) {
                    throw new Error('Erro ao obter URL de download');
                }

                const downloadData = await downloadResponse.json();
                
                updateProgress(100, 'Concluído!');
                
                showMessage('Upload realizado com sucesso! ✅', 'success');
                
                fileInfo.innerHTML = `
                    <p><strong>✅ Arquivo enviado com sucesso!</strong></p>
                    <p><strong>Nome:</strong> ${selectedFile.name}</p>
                    <p><strong>Tamanho:</strong> ${formatFileSize(selectedFile.size)}</p>
                    <p><strong>Chave S3:</strong> <code>${data.key}</code></p>
                    <a href="${downloadData.data.downloadUrl}" target="_blank" class="download-link">
                        🔗 Visualizar/Baixar Arquivo
                    </a>
                    <p style="font-size: 11px; color: #999; margin-top: 10px;">
                        Link válido por ${Math.floor(downloadData.data.expiresIn / 60)} minutos
                    </p>
                `;
                fileInfo.style.display = 'block';

                // Reset
                setTimeout(() => {
                    resetForm();
                }, 5000);

            } catch (error) {
                console.error('Erro:', error);
                showMessage(`Erro: ${error.message}`, 'error');
                updateProgress(0, '');
            } finally {
                uploadBtn.disabled = false;
            }
        }

        function updateProgress(percent, text) {
            progressFill.style.width = percent + '%';
            progressFill.textContent = text || percent + '%';
        }

        function showMessage(text, type) {
            message.textContent = text;
            message.className = `message ${type}`;
            message.style.display = 'block';
        }

        function hideMessage() {
            message.style.display = 'none';
        }

        function resetForm() {
            selectedFile = null;
            fileInput.value = '';
            uploadBtn.disabled = true;
            progressContainer.style.display = 'none';
            updateProgress(0, '');
            uploadArea.innerHTML = `
                <div class="upload-icon">☁️</div>
                <p>Clique ou arraste um arquivo aqui</p>
                <p style="font-size: 12px; color: #999; margin-top: 10px;">
                    Tipos aceitos: JPG, PNG, GIF, WebP, PDF, DOC, DOCX, XLS, XLSX<br>
                    Tamanho máximo: 10MB
                </p>
            `;
        }
    </script>
</body>
</html>
```

### 5.2 Testar o Cliente

1. Abra o arquivo HTML no navegador
2. Selecione ou arraste um arquivo
3. Clique em "Fazer Upload"

**Respostas esperadas**:
- Barra de progresso aparece
- Mensagem de sucesso
- Link para visualizar/baixar o arquivo

---

## ETAPA 6: Testes de Segurança

### 6.1 Testes a Executar

Execute cada teste abaixo e anote os resultados:

**Teste 1: Upload de tipo não permitido**
- Tente fazer upload de arquivo .exe ou .sh
- **Resultado esperado**: Erro "Tipo de arquivo não permitido"

**Teste 2: Upload de arquivo muito grande**
- Tente fazer upload de arquivo > 10MB
- **Resultado esperado**: Erro "Arquivo muito grande"

**Teste 3: URL expirada**
- Obtenha uma Presigned URL
- Aguarde 6 minutos (após expiração)
- Tente usar a URL
- **Resultado esperado**: Erro 403 Forbidden

**Teste 4: Acesso direto ao bucket**
- Tente acessar: `https://seu-bucket.s3.amazonaws.com/uploads/arquivo.jpg`
- **Resultado esperado**: Erro 403 Access Denied

**Teste 5: CORS**
- Abra o console do navegador (F12)
- Faça upload
- **Resultado esperado**: Sem erros de CORS

---

## ETAPA 7: Segurança Adicional (Recomendado)

### 7.1 Implementar Autenticação JWT em Python

Adicione verificação de token JWT antes de gerar Presigned URLs:

```bash
# Instalar dependência
pip install pyjwt python-jose[cryptography] passlib[bcrypt]
```

Crie o arquivo `auth.py`:

```python
"""
Módulo de autenticação JWT
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuração
JWT_SECRET = os.getenv('JWT_SECRET', 'sua-chave-secreta-muito-segura-aqui')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_MINUTES = 30

# Setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT
    
    Args:
        data: Dados a serem incluídos no token
        expires_delta: Tempo de expiração customizado
        
    Returns:
        Token JWT assinado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verifica e decodifica um token JWT
    
    Args:
        credentials: Credenciais HTTP Bearer
        
    Returns:
        Payload do token decodificado
        
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_password(password: str) -> str:
    """Hash de senha"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha"""
    return pwd_context.verify(plain_password, hashed_password)
```

Atualize o `main.py` para usar autenticação:

```python
# No início do arquivo, adicione:
from auth import verify_token, create_access_token

# Nas rotas protegidas, adicione o parâmetro:
@app.post("/api/upload/presigned-url", response_model=UploadResponse)
@limiter.limit("100/15minutes")
async def generate_upload_url(
    request: Request, 
    upload_req: UploadRequest,
    token_data: dict = Security(verify_token)  # ← ADICIONE ESTA LINHA
):
    # O resto do código permanece igual
    # Agora você tem acesso aos dados do usuário via token_data
    user_id = token_data.get("user_id")
    log_operation("UPLOAD", f"Usuário {user_id} solicitou upload de: {upload_req.fileName}")
    # ... resto do código

# Rota para gerar token (exemplo - adapte para seu sistema de login)
@app.post("/api/auth/login")
async def login(username: str, password: str):
    """
    Endpoint de login - adapte para seu sistema
    """
    # Aqui você validaria username/password com seu banco de dados
    # Exemplo simplificado:
    if username == "admin" and password == "senha123":
        token = create_access_token(
            data={"user_id": "123", "username": username}
        )
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas"
    )
```

Atualize o `.env`:

```env
# Adicione esta linha
JWT_SECRET=sua-chave-secreta-muito-longa-e-aleatoria-aqui-min-32-chars
```

Atualize o cliente HTML para incluir o token:

```javascript
// No início do script, adicione:
const TOKEN = 'seu-token-jwt-aqui'; // Você obteria isso do login

// Em todas as requisições, adicione o header:
const presignedResponse = await fetch(`${API_BASE_URL}/upload/presigned-url`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN}`  // ← ADICIONE ESTA LINHA
    },
    body: JSON.stringify({
        fileName: selectedFile.name,
        fileType: selectedFile.type,
        fileSize: selectedFile.size
    })
});
```

### 7.2 Configurar CloudFront (CDN)

Para melhor performance e segurança:

1. Acesse CloudFront no console AWS
2. Clique em "Create Distribution"
3. Configure:
   - **Origin domain**: Seu bucket S3
   - **Origin access**: "Origin access control settings"
   - **Viewer protocol policy**: "Redirect HTTP to HTTPS"
4. Crie a distribuição
5. Atualize política do bucket S3 para permitir apenas CloudFront

### 7.3 Habilitar Logging

No console S3:
1. Acesse seu bucket
2. Vá em "Properties" > "Server access logging"
3. Habilite logging
4. Escolha bucket de destino para logs

---

## ETAPA 8: Monitoramento e Manutenção

### 8.1 Métricas para Monitorar

No CloudWatch AWS, configure alarmes para:

- **Número de requisições**: Alert se > 1000/hora
- **Erros 4xx**: Alert se > 5% das requisições
- **Erros 5xx**: Alert se > 1% das requisições
- **Tamanho do bucket**: Alert se > 80% do limite

### 8.2 Backup e Retenção

Configure versionamento do bucket:

1. Acesse seu bucket S3
2. Vá em "Properties" > "Bucket Versioning"
3. Clique em "Enable"
4. Configure lifecycle policy:
   - Mover para S3 Glacier após 90 dias
   - Deletar versões antigas após 365 dias

---

## ETAPA 9: Checklist de Deploy para Produção

Antes de ir para produção, verifique:

- [ ] `.env` não está no repositório Git
- [ ] `venv/` e `__pycache__/` estão no `.gitignore`
- [ ] CORS configurado apenas para domínios corretos
- [ ] HTTPS configurado no frontend
- [ ] Rate limiting ativado
- [ ] JWT ou outra autenticação implementada
- [ ] Logging habilitado no S3
- [ ] Backup/versionamento configurado
- [ ] Alarmes CloudWatch configurados
- [ ] Documentação da API criada (FastAPI gera automaticamente)
- [ ] Testes de segurança executados
- [ ] Certificado SSL configurado
- [ ] Variáveis de ambiente em produção configuradas
- [ ] Plano de rollback definido
- [ ] Servidor de produção configurado (ex: Gunicorn + Nginx)
- [ ] Variável `ENVIRONMENT=production` definida

### Deploy com Gunicorn (Produção)

Para deploy em produção, use Gunicorn em vez de Uvicorn diretamente:

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar em produção
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Configurar Nginx (Recomendado)

Exemplo de configuração Nginx como proxy reverso:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name seu-dominio.com;
    
    ssl_certificate /caminho/para/certificado.crt;
    ssl_certificate_key /caminho/para/chave.key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting Comum

### Erro: "Access Denied"
**Causa**: Permissões IAM incorretas
**Solução**: Revise a política IAM na Etapa 3.2

### Erro: "CORS policy"
**Causa**: CORS não configurado ou domínio errado
**Solução**: Verifique configuração CORS na Etapa 2.3

### Erro: "Request has expired"
**Causa**: Presigned URL expirou
**Solução**: Gere nova URL. Considere aumentar tempo de expiração

### Upload lento
**Causa**: Região S3 distante do usuário
**Solução**: Use CloudFront ou mude para região mais próxima

### Custo alto inesperado
**Causa**: Muitas requisições GET ou transferência de dados
**Solução**: Implemente cache, use CloudFront

---

## Próximos Passos

Após seguir este guia:

1. **Documentar sua API** usando Swagger/OpenAPI
2. **Implementar autenticação** robusta (OAuth2, JWT)
3. **Adicionar testes automatizados**
4. **Configurar CI/CD** para deploy automático
5. **Implementar monitoramento** com ferramentas como Datadog ou New Relic
6. **Otimizar custos** com análise de uso
7. **Adicionar funcionalidades**:
   - Resize automático de imagens
   - Scan de vírus/malware
   - Thumbnails automáticos
   - Metadados customizados

---

## Suporte e Recursos

### Documentação Oficial AWS
- S3: https://docs.aws.amazon.com/s3/
- IAM: https://docs.aws.amazon.com/iam/
- SDK JavaScript: https://docs.aws.amazon.com/sdk-for-javascript/

### Comunidade
- Stack Overflow: Tag `amazon-s3`
- AWS Forums: https://forums.aws.amazon.com/
- Reddit: r/aws

### Contato Anthropic (este guia)
- Feedback sobre o guia: thumbs down/up no chat

---

## Resumo do Fluxo Completo

```
1. ✅ Conta AWS criada
2. ✅ Bucket S3 configurado com segurança máxima
3. ✅ Usuário IAM com permissões mínimas necessárias
4. ✅ API backend Python (FastAPI) com geração de Presigned URLs
5. ✅ Cliente frontend com interface amigável
6. ✅ Testes de segurança executados
7. ✅ Monitoramento configurado
8. ✅ Ready para produção!
```

**Tempo estimado total**: 2-4 horas (primeira vez)

**Stack Tecnológica**:
- Backend: Python 3.8+ com FastAPI
- AWS: S3, IAM
- Frontend: HTML5 + JavaScript Vanilla

---

**Última atualização**: Janeiro 2025
**Versão**: 2.0 (Python/FastAPI)
**Compatibilidade**: Python 3.8+, AWS SDK boto3, FastAPI 0.109+
