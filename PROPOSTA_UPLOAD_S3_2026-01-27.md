# 🎯 PROPOSTA: Arquitetura Reutilizável para Upload S3

**Data:** 27/01/2026 11:05  
**Objetivo:** Definir arquitetura para upload de arquivos usando Presigned URLs de forma reutilizável

---

## 📊 ANÁLISE DO GUIA E CONTEXTO ATUAL

### **Etapas já executadas (1-3):**
✅ Conta AWS criada  
✅ Bucket S3 configurado  
✅ Usuário IAM com permissões criado  
✅ Credenciais AWS disponíveis

### **O que precisamos implementar (Etapas 4-5):**
- Backend: API para gerar Presigned URLs
- Frontend: Interface para upload e preview
- Integração com models existentes (Logo, ReferenceImage)

---

## 🏗️ ARQUITETURA ATUAL DO SISTEMA

### **Models Existentes:**

```python
# Logo Model (apps/knowledge/models.py:394-434)
class Logo(models.Model):
    knowledge_base = FK(KnowledgeBase)
    name = CharField(max_length=200)
    logo_type = CharField(choices=['principal', 'horizontal', ...])
    s3_key = CharField(max_length=500)        # ✅ Já existe
    s3_url = URLField(max_length=1000)        # ✅ Já existe
    file_format = CharField(max_length=10)
    is_primary = BooleanField(default=False)
    uploaded_by = FK(User)
    created_at = DateTimeField(auto_now_add=True)

# ReferenceImage Model (apps/knowledge/models.py:~474+)
class ReferenceImage(models.Model):
    knowledge_base = FK(KnowledgeBase)
    title = CharField(max_length=200)
    description = TextField(blank=True)
    s3_key = CharField(max_length=500)        # ✅ Já existe
    s3_url = URLField(max_length=1000)        # ✅ Já existe
    file_size = IntegerField()
    width = IntegerField()
    height = IntegerField()
    perceptual_hash = CharField(max_length=64)
    uploaded_by = FK(User)
    created_at = DateTimeField(auto_now_add=True)
```

**✅ ÓTIMO:** Models já têm campos `s3_key` e `s3_url` prontos!

---

## 🎯 PROPOSTA DE ARQUITETURA REUTILIZÁVEL

### **OPÇÃO A: Service Layer Centralizado (RECOMENDADO)**

**Estrutura:**
```
apps/
├── core/
│   ├── services/
│   │   ├── __init__.py
│   │   └── s3_service.py          # ✅ Service centralizado
│   └── utils/
│       └── file_validators.py      # ✅ Validações reutilizáveis
├── knowledge/
│   ├── views.py
│   │   └── upload_logo()           # Usa S3Service
│   │   └── upload_reference()      # Usa S3Service
│   └── services.py                 # Lógica de negócio específica
└── api/
    └── urls.py
        └── /api/s3/presigned-url/  # ✅ Endpoint único
```

**Vantagens:**
- ✅ **Reutilizável:** Um service para toda aplicação
- ✅ **Manutenível:** Mudanças em um único lugar
- ✅ **Testável:** Fácil de testar isoladamente
- ✅ **DRY:** Sem duplicação de código
- ✅ **Escalável:** Fácil adicionar novos tipos de upload

**Como funciona:**
```python
# 1. Service centralizado
class S3Service:
    @staticmethod
    def generate_presigned_upload_url(
        file_name: str,
        file_type: str,
        file_size: int,
        folder: str = 'uploads',  # logos, references, fonts, etc
        organization_id: int = None
    ) -> dict:
        """Gera Presigned URL para upload"""
        # Validações
        # Gera nome seguro
        # Cria Presigned URL
        # Retorna URL + metadata

    @staticmethod
    def generate_presigned_download_url(s3_key: str) -> str:
        """Gera Presigned URL para download/preview"""
        # Valida s3_key
        # Gera URL temporária
        # Retorna URL

# 2. Views específicas usam o service
def upload_logo(request):
    # Validações de negócio (user, organization, etc)
    presigned_data = S3Service.generate_presigned_upload_url(
        file_name=request.POST['fileName'],
        file_type=request.POST['fileType'],
        file_size=request.POST['fileSize'],
        folder='logos',
        organization_id=request.organization.id
    )
    return JsonResponse(presigned_data)
```

---

### **OPÇÃO B: API Separada (FastAPI)**

**Estrutura:**
```
/opt/iamkt/
├── app/                    # Django app principal
└── s3_api/                 # ✅ FastAPI separada
    ├── main.py             # API de upload
    ├── .env                # Credenciais AWS
    └── requirements.txt
```

**Vantagens:**
- ✅ Isolamento completo
- ✅ Tecnologia especializada (FastAPI)
- ✅ Pode escalar independentemente

**Desvantagens:**
- ❌ Mais complexo (2 servidores)
- ❌ Autenticação duplicada
- ❌ Deploy mais complexo
- ❌ CORS entre servidores

---

### **OPÇÃO C: Django View + boto3 Direto**

**Estrutura:**
```
apps/knowledge/
├── views.py
│   └── generate_presigned_url()    # View Django
└── utils.py
    └── s3_helpers.py               # Funções auxiliares
```

**Vantagens:**
- ✅ Simples e direto
- ✅ Usa autenticação Django existente

**Desvantagens:**
- ❌ Difícil reutilizar
- ❌ Tendência a duplicar código
- ❌ Menos organizado

---

## 🏆 RECOMENDAÇÃO: OPÇÃO A (Service Layer)

**Por quê?**
1. **Reutilizável:** Logos, Imagens, Fontes TTF/OTF, PDFs, etc
2. **Manutenível:** Mudança de bucket? Apenas 1 arquivo
3. **Django-native:** Usa stack existente
4. **Autenticação:** Usa sistema Django existente
5. **Deploy:** Sem complexidade adicional

---

## 📐 ARQUITETURA DETALHADA (OPÇÃO A)

### **1. S3Service (apps/core/services/s3_service.py)**

```python
import boto3
import secrets
import time
import re
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from typing import Tuple, Optional

class S3Service:
    """Service centralizado para operações S3"""
    
    # Configuração
    ALLOWED_FILE_TYPES = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/svg+xml': 'svg',
        'image/webp': 'webp',
        'font/ttf': 'ttf',
        'font/otf': 'otf',
        'application/pdf': 'pdf',
    }
    
    MAX_FILE_SIZE_MB = 10
    PRESIGNED_URL_EXPIRATION = 300  # 5 minutos
    
    @classmethod
    def _get_s3_client(cls):
        """Retorna cliente S3 configurado"""
        config = Config(
            region_name=settings.AWS_REGION,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=config
        )
    
    @classmethod
    def generate_secure_filename(
        cls,
        original_name: str,
        mime_type: str,
        folder: str,
        organization_id: int
    ) -> str:
        """Gera nome único e seguro"""
        extension = cls.ALLOWED_FILE_TYPES.get(mime_type, 'bin')
        timestamp = int(time.time() * 1000)
        random_string = secrets.token_hex(16)
        
        # Sanitizar nome
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', original_name)
        name_without_ext = sanitized.rsplit('.', 1)[0][:50]
        
        return f"{folder}/org_{organization_id}/{timestamp}-{random_string}-{name_without_ext}.{extension}"
    
    @classmethod
    def validate_file(
        cls,
        file_type: str,
        file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """Valida tipo e tamanho do arquivo"""
        if file_type not in cls.ALLOWED_FILE_TYPES:
            return False, f"Tipo não permitido. Aceitos: {', '.join(cls.ALLOWED_FILE_TYPES.keys())}"
        
        max_bytes = cls.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"Arquivo muito grande. Máximo: {cls.MAX_FILE_SIZE_MB}MB"
        
        return True, None
    
    @classmethod
    def generate_presigned_upload_url(
        cls,
        file_name: str,
        file_type: str,
        file_size: int,
        folder: str,
        organization_id: int
    ) -> dict:
        """
        Gera Presigned URL para upload
        
        Returns:
            {
                'upload_url': str,
                's3_key': str,
                'expires_in': int
            }
        """
        # Validar arquivo
        is_valid, error_msg = cls.validate_file(file_type, file_size)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Gerar nome seguro
        s3_key = cls.generate_secure_filename(
            file_name, file_type, folder, organization_id
        )
        
        # Gerar Presigned URL
        s3_client = cls._get_s3_client()
        
        try:
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': settings.AWS_BUCKET_NAME,
                    'Key': s3_key,
                    'ContentType': file_type,
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'original-name': file_name,
                        'organization-id': str(organization_id)
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
            raise Exception(f"Erro ao gerar URL: {str(e)}")
    
    @classmethod
    def generate_presigned_download_url(
        cls,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        """Gera Presigned URL para download/preview"""
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
            raise Exception(f"Erro ao gerar URL de download: {str(e)}")
    
    @classmethod
    def delete_file(cls, s3_key: str) -> bool:
        """Deleta arquivo do S3"""
        s3_client = cls._get_s3_client()
        
        try:
            s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key
            )
            return True
        except ClientError:
            return False
```

---

### **2. Views Django (apps/knowledge/views.py)**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from apps.core.services.s3_service import S3Service
from apps.knowledge.models import Logo, ReferenceImage

@login_required
@require_http_methods(["POST"])
def generate_logo_upload_url(request):
    """Gera Presigned URL para upload de logo"""
    try:
        data = S3Service.generate_presigned_upload_url(
            file_name=request.POST['fileName'],
            file_type=request.POST['fileType'],
            file_size=int(request.POST['fileSize']),
            folder='logos',
            organization_id=request.organization.id
        )
        return JsonResponse({'success': True, 'data': data})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Erro interno'}, status=500)

@login_required
@require_http_methods(["POST"])
def create_logo(request):
    """Cria registro de Logo após upload bem-sucedido"""
    try:
        kb = request.organization.knowledge_base
        
        logo = Logo.objects.create(
            knowledge_base=kb,
            name=request.POST['name'],
            logo_type=request.POST['logoType'],
            s3_key=request.POST['s3Key'],
            s3_url=f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{request.POST['s3Key']}",
            file_format=request.POST['fileFormat'],
            is_primary=request.POST.get('isPrimary', False),
            uploaded_by=request.user
        )
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(logo.s3_key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': logo.id,
                'name': logo.name,
                'preview_url': preview_url
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Similar para ReferenceImage
```

---

### **3. Frontend JavaScript (static/js/s3-upload.js)**

```javascript
/**
 * S3 Upload Helper - Reutilizável
 */

class S3Uploader {
    constructor(uploadUrlEndpoint, createRecordEndpoint) {
        this.uploadUrlEndpoint = uploadUrlEndpoint;
        this.createRecordEndpoint = createRecordEndpoint;
    }
    
    async upload(file, metadata = {}) {
        try {
            // 1. Obter Presigned URL
            const presignedData = await this.getPresignedUrl(file);
            
            // 2. Upload para S3
            await this.uploadToS3(presignedData.upload_url, file);
            
            // 3. Criar registro no banco
            const record = await this.createRecord({
                s3Key: presignedData.s3_key,
                fileFormat: file.type.split('/')[1],
                ...metadata
            });
            
            return record;
            
        } catch (error) {
            throw new Error(`Upload falhou: ${error.message}`);
        }
    }
    
    async getPresignedUrl(file) {
        const response = await fetch(this.uploadUrlEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams({
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
    
    async uploadToS3(url, file) {
        const response = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': file.type
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao enviar arquivo para S3');
        }
    }
    
    async createRecord(data) {
        const response = await fetch(this.createRecordEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        });
        
        if (!response.ok) {
            throw new Error('Erro ao criar registro');
        }
        
        const result = await response.json();
        return result.data;
    }
}

// Uso:
const logoUploader = new S3Uploader(
    '/knowledge/logo/upload-url/',
    '/knowledge/logo/create/'
);

const referenceUploader = new S3Uploader(
    '/knowledge/reference/upload-url/',
    '/knowledge/reference/create/'
);
```

---

## 📋 CONFIGURAÇÃO NECESSÁRIA

### **1. Django Settings (settings.py)**

```python
# AWS S3 Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
```

### **2. Environment Variables (.env)**

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_BUCKET_NAME=seu-bucket-name
```

### **3. Requirements (requirements.txt)**

```txt
boto3==1.34.0
```

---

## 🎨 PREVIEW DE IMAGENS

### **Lazy Loading com Presigned URLs**

```javascript
// static/js/image-preview.js
class ImagePreviewLoader {
    constructor(previewUrlEndpoint) {
        this.previewUrlEndpoint = previewUrlEndpoint;
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            { rootMargin: '50px' }
        );
    }
    
    observe(imageElement) {
        this.observer.observe(imageElement);
    }
    
    async handleIntersection(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                const img = entry.target;
                const s3Key = img.dataset.s3Key;
                
                try {
                    const url = await this.getPreviewUrl(s3Key);
                    img.src = url;
                    this.observer.unobserve(img);
                } catch (error) {
                    console.error('Erro ao carregar preview:', error);
                }
            }
        }
    }
    
    async getPreviewUrl(s3Key) {
        const response = await fetch(`${this.previewUrlEndpoint}?s3_key=${s3Key}`);
        const data = await response.json();
        return data.preview_url;
    }
}

// Uso no template:
// <img data-s3-key="logos/org_1/123-abc-logo.png" 
//      src="/static/images/placeholder.png" 
//      class="lazy-load-image">
```

---

## ✅ VANTAGENS DA ARQUITETURA PROPOSTA

1. **✅ Reutilizável:** Logos, Imagens, Fontes, PDFs
2. **✅ Manutenível:** Mudanças centralizadas
3. **✅ Seguro:** Presigned URLs temporárias
4. **✅ Escalável:** Fácil adicionar novos tipos
5. **✅ Testável:** Service isolado
6. **✅ Performance:** Upload direto ao S3
7. **✅ Preview:** Lazy loading com URLs temporárias
8. **✅ Multi-tenant:** Organização por pasta

---

## 🚀 PRÓXIMOS PASSOS SUGERIDOS

1. **Debater e aprovar arquitetura**
2. Criar `apps/core/services/s3_service.py`
3. Adicionar credenciais AWS ao `.env`
4. Criar views para logos e imagens
5. Criar JavaScript reutilizável
6. Implementar preview com lazy loading
7. Testar upload e preview
8. Documentar uso para futuros uploads

---

## ❓ PERGUNTAS PARA DEBATER

1. **Aprovação da Opção A (Service Layer)?**
2. **Estrutura de pastas S3:** `logos/org_{id}/` ou `org_{id}/logos/`?
3. **Tamanho máximo:** 10MB suficiente ou aumentar?
4. **Formatos aceitos:** Adicionar GIF, BMP, TIFF?
5. **Preview:** Gerar thumbnails ou usar imagem original?
6. **Validação:** Validar dimensões mínimas/máximas?
7. **Compressão:** Comprimir imagens automaticamente?

---

**Aguardando sua análise e feedback para prosseguir com a implementação!** 🎯
