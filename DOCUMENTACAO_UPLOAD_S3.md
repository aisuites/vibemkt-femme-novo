# 📚 DOCUMENTAÇÃO: Upload S3 com Presigned URLs

**Data:** 27/01/2026  
**Versão:** 1.0  
**Status:** ✅ IMPLEMENTADO

---

## 🎯 VISÃO GERAL

Sistema completo e reutilizável para upload de arquivos usando AWS S3 com Presigned URLs.

**Características:**
- ✅ Upload direto para S3 (não passa pelo servidor Django)
- ✅ Nomenclatura personalizável por tipo de arquivo
- ✅ Validação flexível de tamanho por tipo
- ✅ Bucket por organização (multi-tenant)
- ✅ Preview com lazy loading
- ✅ Thumbnails e compressão automática
- ✅ URLs temporárias seguras
- ✅ Reutilizável para múltiplos tipos de arquivo

---

## 📁 ARQUITETURA

### **Backend:**
```
apps/
├── core/
│   └── services/
│       ├── s3_service.py          # Service principal
│       └── image_processor.py     # Thumbnails + compressão
└── knowledge/
    ├── views_upload.py            # Views de upload
    └── urls.py                    # URLs configuradas
```

### **Frontend:**
```
static/
└── js/
    └── s3-uploader.js             # Classes reutilizáveis
```

---

## 🚀 COMO USAR

### **1. Upload de Logo**

#### **HTML:**
```html
<input type="file" id="logoInput" accept="image/png,image/svg+xml,image/jpeg,image/webp">
<button onclick="uploadLogo()">Upload Logo</button>
<div id="progress"></div>
<img id="preview" data-record-id="" data-record-type="logo" src="/static/images/placeholder.png">
```

#### **JavaScript:**
```javascript
// Criar uploader
const logoUploader = new S3Uploader(
    '/knowledge/logo/upload-url/',
    '/knowledge/logo/create/',
    {
        onProgress: (percent, message) => {
            document.getElementById('progress').textContent = `${percent}% - ${message}`;
        },
        onSuccess: (data) => {
            console.log('Logo criado:', data);
            // Atualizar preview
            const img = document.getElementById('preview');
            img.dataset.recordId = data.id;
            img.src = data.preview_url;
        },
        onError: (error) => {
            alert('Erro: ' + error.message);
        }
    }
);

// Fazer upload
async function uploadLogo() {
    const file = document.getElementById('logoInput').files[0];
    if (!file) return;
    
    try {
        await logoUploader.upload(file, {
            name: 'Logo Principal',
            logoType: 'principal',
            isPrimary: true
        });
    } catch (error) {
        console.error('Erro no upload:', error);
    }
}
```

---

### **2. Upload de Imagem de Referência**

#### **JavaScript:**
```javascript
const referenceUploader = new S3Uploader(
    '/knowledge/reference/upload-url/',
    '/knowledge/reference/create/',
    {
        validateFile: FileValidators.combine(
            FileValidators.maxSize(10),
            FileValidators.allowedTypes(['image/png', 'image/jpeg', 'image/webp'])
        ),
        onProgress: (percent, message) => {
            console.log(`${percent}% - ${message}`);
        }
    }
);

async function uploadReference() {
    const file = document.getElementById('referenceInput').files[0];
    
    // Obter dimensões da imagem
    const validation = await FileValidators.imageDimensions()(file);
    
    await referenceUploader.upload(file, {
        title: 'Imagem de Referência',
        description: 'Descrição da imagem',
        width: validation.width,
        height: validation.height,
        fileSize: file.size,
        perceptualHash: '' // Opcional
    });
}
```

---

### **3. Preview com Lazy Loading**

#### **HTML:**
```html
<!-- Logos -->
<div class="logos-grid">
    <img data-record-id="1" data-record-type="logo" 
         src="/static/images/placeholder.png" 
         class="lazy-load-image">
    <img data-record-id="2" data-record-type="logo" 
         src="/static/images/placeholder.png" 
         class="lazy-load-image">
</div>

<!-- Imagens de Referência -->
<div class="references-grid">
    <img data-record-id="1" data-record-type="reference" 
         src="/static/images/placeholder.png" 
         class="lazy-load-image">
</div>
```

#### **JavaScript:**
```javascript
// Inicializar loader
const logoPreviewLoader = new ImagePreviewLoader('/knowledge/logo/preview-url/');
const referencePreviewLoader = new ImagePreviewLoader('/knowledge/reference/preview-url/');

// Observar todas as imagens
document.querySelectorAll('img[data-record-type="logo"]').forEach(img => {
    logoPreviewLoader.observe(img);
});

document.querySelectorAll('img[data-record-type="reference"]').forEach(img => {
    referencePreviewLoader.observe(img);
});

// Cleanup ao sair da página
window.addEventListener('beforeunload', () => {
    logoPreviewLoader.disconnect();
    referencePreviewLoader.disconnect();
});
```

---

## 🔧 CONFIGURAÇÃO

### **1. Variáveis de Ambiente (.env)**

```env
# AWS S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_BUCKET_NAME_TEMPLATE=iamkt-org-{org_id}
```

### **2. Criar Buckets S3**

Para cada organização, criar bucket:
```bash
# Exemplo: Organização ID 1
aws s3 mb s3://iamkt-org-1 --region us-east-1

# Configurar CORS
aws s3api put-bucket-cors --bucket iamkt-org-1 --cors-configuration file://cors.json
```

**cors.json:**
```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["PUT", "POST", "GET"],
            "AllowedOrigins": [
                "http://localhost:8000",
                "https://iamkt-femmeintegra.aisuites.com.br"
            ],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

---

## 📋 TIPOS DE ARQUIVO SUPORTADOS

### **Configurações Atuais:**

| Tipo | Pasta | Tamanho Max | Formatos | Padrão de Nome |
|------|-------|-------------|----------|----------------|
| `logo` | `logos/` | 10MB | PNG, SVG, JPG, WebP | `org_{org_id}_logo_{timestamp}_{random}.{ext}` |
| `reference` | `references/` | 10MB | PNG, JPG, WebP | `org_{org_id}_ref_{timestamp}_{random}.{ext}` |
| `font` | `fonts/` | 5MB | TTF, OTF | `org_{org_id}_fonte_{name}.{ext}` |
| `video` | `videos/` | 25MB | MP4, WebM, MOV | `org_{org_id}_video_{timestamp}_{random}.{ext}` |
| `pdf` | `documents/` | 15MB | PDF | `org_{org_id}_doc_{timestamp}_{random}.{ext}` |
| `post_image` | `posts/` | 10MB | PNG, JPG, WebP | `org_{org_id}_post_{date}_{random}.{ext}` |

### **Adicionar Novo Tipo:**

Editar `apps/core/services/s3_service.py`:

```python
FILE_CONFIGS = {
    # ... tipos existentes ...
    
    'novo_tipo': {
        'folder': 'nova_pasta',
        'max_size_mb': 20,
        'allowed_types': {
            'application/zip': 'zip',
            'application/x-rar': 'rar',
        },
        'filename_pattern': 'org_{org_id}_arquivo_{timestamp}.{ext}',
    },
}
```

---

## 🎨 NOMENCLATURA PERSONALIZADA

### **Variáveis Disponíveis:**

- `{org_id}` - ID da organização
- `{timestamp}` - Timestamp em milissegundos
- `{random}` - String aleatória (16 chars)
- `{ext}` - Extensão do arquivo
- `{name}` - Nome sanitizado do arquivo
- `{date}` - Data YYYYMMDD
- **Qualquer variável customizada**

### **Exemplos:**

```python
# Logo com timestamp
'org_{org_id}_logo_{timestamp}_{random}.{ext}'
# Resultado: org_1_logo_1706356800000_abc123.png

# Fonte com nome customizado
'org_{org_id}_fonte_{name}.{ext}'
# Uso: custom_data={'name': 'Roboto'}
# Resultado: org_1_fonte_Roboto.ttf

# Post com data
'org_{org_id}_post_{date}_{random}.{ext}'
# Uso: custom_data={'date': '20260127'}
# Resultado: org_1_post_20260127_abc123.png
```

---

## 🔒 SEGURANÇA

### **URLs Temporárias:**
- **Upload:** 5 minutos
- **Preview:** 1 hora
- **Download:** 1 hora

### **Validações:**
- ✅ Tipo de arquivo (MIME type)
- ✅ Tamanho máximo por tipo
- ✅ Sanitização de nomes
- ✅ Prevenção de path traversal
- ✅ Autenticação obrigatória
- ✅ Isolamento por organização

### **Permissões IAM:**
```json
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
            "Resource": "arn:aws:s3:::iamkt-org-*/*"
        }
    ]
}
```

---

## 🧪 TESTES

### **Testar Upload:**
```bash
# Abrir console do navegador
const file = document.getElementById('fileInput').files[0];
const uploader = new S3Uploader('/knowledge/logo/upload-url/', '/knowledge/logo/create/');
await uploader.upload(file, { name: 'Teste', logoType: 'principal' });
```

### **Testar Preview:**
```bash
# Verificar se imagem carrega
const loader = new ImagePreviewLoader('/knowledge/logo/preview-url/');
loader.observe(document.querySelector('img[data-record-id="1"]'));
```

---

## 🐛 TROUBLESHOOTING

### **Erro: "CORS policy"**
**Causa:** CORS não configurado no bucket  
**Solução:** Configurar CORS conforme seção "Configuração"

### **Erro: "Access Denied"**
**Causa:** Permissões IAM incorretas  
**Solução:** Verificar política IAM do usuário AWS

### **Erro: "Request has expired"**
**Causa:** URL expirou (5 minutos)  
**Solução:** Gerar nova URL

### **Preview não carrega**
**Causa:** `data-record-id` ou `data-record-type` ausente  
**Solução:** Adicionar atributos no `<img>`

---

## 📊 FLUXO COMPLETO

```
1. User seleciona arquivo
   ↓
2. JS valida tipo/tamanho
   ↓
3. JS solicita Presigned URL → Django View
   ↓
4. Django valida user/org → S3Service gera URL
   ↓
5. JS faz upload direto para S3 (PUT)
   ↓
6. S3 armazena arquivo
   ↓
7. JS notifica Django → Cria registro no banco
   ↓
8. Django retorna preview URL
   ↓
9. JS exibe preview na interface
```

---

## 🔄 PRÓXIMAS IMPLEMENTAÇÕES

- [ ] Upload de fontes TTF/OTF
- [ ] Upload de vídeos
- [ ] Upload de PDFs
- [ ] Geração automática de thumbnails no backend
- [ ] Compressão de imagens no backend
- [ ] Rate limiting por usuário
- [ ] Webhook S3 para processamento assíncrono

---

## 📞 SUPORTE

**Desenvolvedor:** Cascade AI  
**Data Implementação:** 27/01/2026  
**Versão:** 1.0

**Arquivos Principais:**
- `apps/core/services/s3_service.py`
- `apps/core/services/image_processor.py`
- `apps/knowledge/views_upload.py`
- `static/js/s3-uploader.js`
