# Guia Completo: Upload S3 com Django + Service Layer

## Versão 4.0 - Parte 2 (Continuação)

**Data:** 27/01/2026  
**Versão:** 4.0 Híbrida - Parte 2  
**Status:** ✅ COMPLETO

---

## 📑 Índice da Parte 2

11. [Preview e Lazy Loading](#11-preview-e-lazy-loading)
12. [Validações Avançadas](#12-validações-avançadas)
13. [Integração com Models Existentes](#13-integração-com-models-existentes)
14. [Testes de Segurança](#14-testes-de-segurança)
15. [Deploy para Produção](#15-deploy-para-produção)
16. [Monitoring e Manutenção](#16-monitoring-e-manutenção)
17. [Troubleshooting Django](#17-troubleshooting-django)
18. [Apêndices e Recursos](#18-apêndices-e-recursos)

---

## 11. Preview e Lazy Loading

### 11.1 Por que Lazy Loading?

**Problema sem Lazy Loading:**
```python
# Template carrega TODAS as imagens de uma vez
{% for logo in logos %}
    <img src="{{ logo.get_preview_url }}">  # ← 100 requisições S3 simultâneas
{% endfor %}
```

**Problemas:**
- ❌ 100 requisições simultâneas ao S3
- ❌ Usuário espera TODAS as imagens carregarem
- ❌ Custo alto (100 GET requests)
- ❌ Lento (muitas imagens grandes)

**Solução com Lazy Loading:**
```javascript
// Carrega apenas imagens visíveis no viewport
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            loadImage(entry.target);  // ← Carrega sob demanda
        }
    });
});
```

**Vantagens:**
- ✅ Carrega apenas imagens visíveis
- ✅ Economia de custos (menos GET requests)
- ✅ Página carrega rápido
- ✅ Experiência fluida

### 11.2 Implementar Image Preview Loader

**Arquivo:** `static/js/image-preview-loader.js`

```javascript
/**
 * ImagePreviewLoader - Lazy loading de imagens S3 com Presigned URLs
 * 
 * Uso:
 *   const loader = new ImagePreviewLoader('/knowledge/preview-url/');
 *   loader.observeAll('.lazy-s3-image');
 */

class ImagePreviewLoader {
    constructor(previewUrlEndpoint) {
        this.previewUrlEndpoint = previewUrlEndpoint;
        this.cache = new Map();  // Cache de URLs
        
        // IntersectionObserver para detectar imagens no viewport
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            {
                root: null,
                rootMargin: '50px',  // Pré-carrega 50px antes
                threshold: 0.01
            }
        );
    }
    
    /**
     * Observa todas as imagens com a classe especificada
     */
    observeAll(selector) {
        const images = document.querySelectorAll(selector);
        images.forEach(img => this.observe(img));
    }
    
    /**
     * Observa uma imagem específica
     */
    observe(imageElement) {
        this.observer.observe(imageElement);
    }
    
    /**
     * Callback quando imagem entra/sai do viewport
     */
    async handleIntersection(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                const img = entry.target;
                const s3Key = img.dataset.s3Key;
                
                // Já carregada? Pular
                if (img.dataset.loaded === 'true') continue;
                
                try {
                    // Mostrar loading
                    img.classList.add('loading');
                    
                    // Obter URL do preview
                    const previewUrl = await this.getPreviewUrl(s3Key);
                    
                    // Carregar imagem
                    await this.loadImage(img, previewUrl);
                    
                    // Marcar como carregada
                    img.dataset.loaded = 'true';
                    img.classList.remove('loading');
                    img.classList.add('loaded');
                    
                    // Parar de observar
                    this.observer.unobserve(img);
                    
                } catch (error) {
                    console.error('Erro ao carregar preview:', error);
                    img.classList.remove('loading');
                    img.classList.add('error');
                    
                    // Mostrar imagem de erro
                    img.src = '/static/images/image-error.png';
                }
            }
        }
    }
    
    /**
     * Obtém Presigned URL do backend (com cache)
     */
    async getPreviewUrl(s3Key) {
        // Verificar cache
        if (this.cache.has(s3Key)) {
            const cached = this.cache.get(s3Key);
            
            // URL ainda válida? (expira em 55 minutos)
            if (Date.now() - cached.timestamp < 55 * 60 * 1000) {
                return cached.url;
            }
        }
        
        // Buscar do backend
        const response = await fetch(
            `${this.previewUrlEndpoint}?s3_key=${encodeURIComponent(s3Key)}`,
            {
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        const previewUrl = data.data.previewUrl;
        
        // Salvar no cache
        this.cache.set(s3Key, {
            url: previewUrl,
            timestamp: Date.now()
        });
        
        return previewUrl;
    }
    
    /**
     * Carrega imagem (Promise que resolve quando carregada)
     */
    loadImage(imgElement, url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                imgElement.src = url;
                resolve();
            };
            
            img.onerror = () => {
                reject(new Error('Falha ao carregar imagem'));
            };
            
            img.src = url;
        });
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
    
    /**
     * Limpa cache (chamar periodicamente)
     */
    clearCache() {
        this.cache.clear();
    }
}
```

### 11.3 View para Preview

**Arquivo:** `apps/knowledge/views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from apps.core.services.s3_service import S3Service


@login_required
@require_http_methods(["GET"])
def get_preview_url(request):
    """
    Gera Presigned URL para preview de qualquer arquivo
    
    GET /knowledge/preview-url/?s3_key=org-1/logos/123-abc-logo.png
    
    Response:
        {
            "success": true,
            "data": {
                "previewUrl": "https://...",
                "expiresIn": 3600
            }
        }
    """
    try:
        s3_key = request.GET.get('s3_key')
        
        if not s3_key:
            return JsonResponse({
                'success': False,
                'error': 's3_key é obrigatório'
            }, status=400)
        
        # Validar que usuário tem acesso (organização)
        organization_id = request.organization.id
        S3Service.validate_organization_access(s3_key, organization_id)
        
        # Gerar Presigned URL
        preview_url = S3Service.generate_presigned_download_url(s3_key)
        
        return JsonResponse({
            'success': True,
            'data': {
                'previewUrl': preview_url,
                'expiresIn': 3600
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de preview'
        }, status=500)
```

### 11.4 Template com Lazy Loading

**Arquivo:** `templates/knowledge/logo_list.html`

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<style>
    .logo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        padding: 20px;
    }
    
    .logo-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .logo-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .logo-image {
        width: 100%;
        height: 150px;
        object-fit: contain;
        background: #f5f5f5;
        border-radius: 8px;
        transition: opacity 0.3s;
    }
    
    .logo-image.loading {
        opacity: 0.5;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
    }
    
    .logo-image.loaded {
        opacity: 1;
    }
    
    .logo-image.error {
        opacity: 0.3;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .logo-info {
        margin-top: 10px;
    }
    
    .logo-name {
        font-weight: 600;
        color: #333;
        margin-bottom: 5px;
    }
    
    .logo-type {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
    }
</style>
{% endblock %}

{% block content %}
<div class="container">
    <h1>Logos</h1>
    
    <div class="logo-grid">
        {% for logo in logos %}
        <div class="logo-card">
            <!-- Imagem com lazy loading -->
            <img 
                class="logo-image lazy-s3-image"
                data-s3-key="{{ logo.s3_key }}"
                src="/static/images/placeholder.png"
                alt="{{ logo.name }}"
            >
            
            <div class="logo-info">
                <div class="logo-name">{{ logo.name }}</div>
                <div class="logo-type">{{ logo.get_logo_type_display }}</div>
            </div>
        </div>
        {% empty %}
        <p>Nenhum logo cadastrado ainda.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/image-preview-loader.js' %}"></script>
<script>
    // Inicializar lazy loading
    const previewLoader = new ImagePreviewLoader('/knowledge/preview-url/');
    previewLoader.observeAll('.lazy-s3-image');
    
    // Limpar cache a cada 1 hora
    setInterval(() => {
        previewLoader.clearCache();
    }, 60 * 60 * 1000);
</script>
{% endblock %}
```

### 11.5 Adicionar URL de Preview

**Arquivo:** `apps/knowledge/urls.py`

```python
urlpatterns = [
    # ... outras URLs
    
    # Preview URL (genérica)
    path(
        'preview-url/',
        views.get_preview_url,
        name='preview_url'
    ),
]
```

---

## 12. Validações Avançadas

### 12.1 Validação de Dimensões de Imagem

**Arquivo:** `apps/core/utils/image_validators.py`

```python
"""
Validadores avançados para imagens
"""
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional


class ImageValidator:
    """Validações avançadas de imagens"""
    
    # Dimensões mínimas por categoria
    MIN_DIMENSIONS = {
        'logos': (100, 100),
        'references': (200, 200),
    }
    
    # Dimensões máximas por categoria
    MAX_DIMENSIONS = {
        'logos': (5000, 5000),
        'references': (10000, 10000),
    }
    
    # Aspect ratios permitidos (largura/altura)
    ALLOWED_RATIOS = {
        'logos': [(1, 1), (16, 9), (4, 3), (3, 2)],  # Quadrado, widescreen, etc
        'references': None,  # Qualquer ratio
    }
    
    @classmethod
    def validate_dimensions(
        cls,
        image_data: bytes,
        category: str
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Valida dimensões da imagem
        
        Args:
            image_data: Bytes da imagem
            category: Categoria (logos, references)
            
        Returns:
            (is_valid, error_message, dimensions_info)
            dimensions_info = {'width': int, 'height': int, 'ratio': float}
        """
        try:
            # Abrir imagem
            img = Image.open(BytesIO(image_data))
            width, height = img.size
            
            # Info de dimensões
            dimensions_info = {
                'width': width,
                'height': height,
                'ratio': width / height if height > 0 else 0
            }
            
            # Validar dimensões mínimas
            min_dims = cls.MIN_DIMENSIONS.get(category)
            if min_dims:
                min_width, min_height = min_dims
                if width < min_width or height < min_height:
                    return False, (
                        f"Dimensões muito pequenas. "
                        f"Mínimo: {min_width}x{min_height}px"
                    ), dimensions_info
            
            # Validar dimensões máximas
            max_dims = cls.MAX_DIMENSIONS.get(category)
            if max_dims:
                max_width, max_height = max_dims
                if width > max_width or height > max_height:
                    return False, (
                        f"Dimensões muito grandes. "
                        f"Máximo: {max_width}x{max_height}px"
                    ), dimensions_info
            
            # Validar aspect ratio
            allowed_ratios = cls.ALLOWED_RATIOS.get(category)
            if allowed_ratios:
                ratio = width / height
                
                # Verificar se ratio está próximo de algum permitido (±10%)
                ratio_valid = False
                for allowed_width, allowed_height in allowed_ratios:
                    allowed_ratio = allowed_width / allowed_height
                    if abs(ratio - allowed_ratio) / allowed_ratio <= 0.1:
                        ratio_valid = True
                        break
                
                if not ratio_valid:
                    ratio_strings = [f"{w}:{h}" for w, h in allowed_ratios]
                    return False, (
                        f"Proporção da imagem não permitida. "
                        f"Permitidas: {', '.join(ratio_strings)}"
                    ), dimensions_info
            
            return True, None, dimensions_info
            
        except Exception as e:
            return False, f"Erro ao validar imagem: {str(e)}", None
    
    @classmethod
    def validate_image_quality(
        cls,
        image_data: bytes,
        min_dpi: int = 72
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida qualidade da imagem (DPI)
        
        Args:
            image_data: Bytes da imagem
            min_dpi: DPI mínimo
            
        Returns:
            (is_valid, error_message)
        """
        try:
            img = Image.open(BytesIO(image_data))
            
            # Obter DPI (se disponível)
            dpi = img.info.get('dpi')
            
            if dpi:
                dpi_x, dpi_y = dpi
                avg_dpi = (dpi_x + dpi_y) / 2
                
                if avg_dpi < min_dpi:
                    return False, (
                        f"Qualidade da imagem muito baixa. "
                        f"DPI mínimo: {min_dpi}, detectado: {int(avg_dpi)}"
                    )
            
            return True, None
            
        except Exception as e:
            # Se não conseguir ler DPI, considerar válido
            return True, None
```

### 12.2 Validação com Preview Antes do Upload

**Arquivo:** `static/js/image-validator.js`

```javascript
/**
 * ImageValidator - Valida imagem no frontend antes do upload
 */

class ImageValidator {
    constructor(category) {
        this.category = category;
        
        // Configurações por categoria
        this.config = {
            logos: {
                minDimensions: { width: 100, height: 100 },
                maxDimensions: { width: 5000, height: 5000 },
                maxFileSize: 5 * 1024 * 1024,  // 5MB
                allowedTypes: ['image/png', 'image/jpeg', 'image/svg+xml', 'image/webp']
            },
            references: {
                minDimensions: { width: 200, height: 200 },
                maxDimensions: { width: 10000, height: 10000 },
                maxFileSize: 10 * 1024 * 1024,  // 10MB
                allowedTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
            }
        };
    }
    
    /**
     * Valida arquivo completo
     */
    async validate(file) {
        const errors = [];
        
        // 1. Validar tipo
        const typeError = this.validateFileType(file);
        if (typeError) errors.push(typeError);
        
        // 2. Validar tamanho
        const sizeError = this.validateFileSize(file);
        if (sizeError) errors.push(sizeError);
        
        // 3. Validar dimensões (se imagem)
        if (file.type.startsWith('image/') && file.type !== 'image/svg+xml') {
            const dimensionsError = await this.validateDimensions(file);
            if (dimensionsError) errors.push(dimensionsError);
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    /**
     * Valida tipo de arquivo
     */
    validateFileType(file) {
        const config = this.config[this.category];
        
        if (!config.allowedTypes.includes(file.type)) {
            return `Tipo não permitido. Aceitos: ${config.allowedTypes.join(', ')}`;
        }
        
        return null;
    }
    
    /**
     * Valida tamanho do arquivo
     */
    validateFileSize(file) {
        const config = this.config[this.category];
        
        if (file.size > config.maxFileSize) {
            const maxMB = Math.round(config.maxFileSize / (1024 * 1024));
            return `Arquivo muito grande. Máximo: ${maxMB}MB`;
        }
        
        return null;
    }
    
    /**
     * Valida dimensões da imagem
     */
    async validateDimensions(file) {
        const config = this.config[this.category];
        
        return new Promise((resolve) => {
            const img = new Image();
            const url = URL.createObjectURL(file);
            
            img.onload = () => {
                URL.revokeObjectURL(url);
                
                const { width, height } = img;
                
                // Verificar mínimo
                if (width < config.minDimensions.width || height < config.minDimensions.height) {
                    resolve(
                        `Dimensões muito pequenas. Mínimo: ${config.minDimensions.width}x${config.minDimensions.height}px`
                    );
                    return;
                }
                
                // Verificar máximo
                if (width > config.maxDimensions.width || height > config.maxDimensions.height) {
                    resolve(
                        `Dimensões muito grandes. Máximo: ${config.maxDimensions.width}x${config.maxDimensions.height}px`
                    );
                    return;
                }
                
                resolve(null);
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(url);
                resolve('Erro ao carregar imagem para validação');
            };
            
            img.src = url;
        });
    }
    
    /**
     * Gera preview da imagem
     */
    async generatePreview(file, maxWidth = 300, maxHeight = 300) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const img = new Image();
                
                img.onload = () => {
                    // Calcular dimensões do preview mantendo aspect ratio
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }
                    
                    if (height > maxHeight) {
                        width = (width * maxHeight) / height;
                        height = maxHeight;
                    }
                    
                    // Criar canvas para resize
                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    resolve({
                        dataUrl: canvas.toDataURL(file.type),
                        width: img.width,
                        height: img.height
                    });
                };
                
                img.src = e.target.result;
            };
            
            reader.readAsDataURL(file);
        });
    }
}
```

### 12.3 Atualizar Upload com Validação

**Arquivo:** `templates/knowledge/logo_upload.html` (atualizar script)

```javascript
// Adicionar validador
const validator = new ImageValidator('logos');

// Atualizar handleFileSelect
async function handleFileSelect(file) {
    // Validar arquivo
    const validation = await validator.validate(file);
    
    if (!validation.valid) {
        showMessage(validation.errors.join('. '), 'error');
        return;
    }
    
    // Gerar preview
    const preview = await validator.generatePreview(file);
    
    selectedFile = file;
    uploadBtn.disabled = false;
    metadataForm.style.display = 'block';
    
    uploadArea.innerHTML = `
        <img src="${preview.dataUrl}" style="max-width: 200px; max-height: 200px; margin-bottom: 10px;">
        <p><strong>${file.name}</strong></p>
        <p style="font-size: 12px; color: #666;">
            ${preview.width}x${preview.height}px - ${formatFileSize(file.size)}
        </p>
    `;
    
    hideMessage();
}
```

---

## 13. Integração com Models Existentes

### 13.1 Nomenclatura Flexível de Arquivos

**NOVIDADE v4.0:** Sistema de templates para nomenclatura customizada!

#### **Por que templates flexíveis?**

```python
# ❌ ANTES: Nome fixo
'org-1/fonts/1706356800000-abc123def456-Roboto.ttf'
# Difícil de encontrar, timestamp no nome da fonte

# ✅ AGORA: Nome customizado
'org-1/fontes/Roboto_Bold.ttf'
# Fácil de encontrar, nome semântico
```

#### **Variáveis Disponíveis:**

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `{org_id}` | ID da organização | `1` |
| `{category}` | Categoria do arquivo | `logos` |
| `{timestamp}` | Timestamp em ms | `1706356800000` |
| `{random}` | String aleatória (32 chars) | `abc123def456...` |
| `{ext}` | Extensão do arquivo | `png` |
| `{name}` | Nome sanitizado | `logo-principal` |
| `{date}` | Data YYYYMMDD | `20260127` |
| `{datetime}` | Data+hora YYYYMMDDHHmmss | `20260127153045` |
| **Custom** | Qualquer chave em `custom_data` | `{font_family}`, `{product_id}`, etc |

#### **Templates Padrão por Categoria:**

```python
# No S3Service
DEFAULT_TEMPLATES = {
    'logos': 'org-{org_id}/{category}/{timestamp}-{random}-{name}.{ext}',
    # Resultado: org-1/logos/1706356800000-abc123-logo.png
    
    'references': 'org-{org_id}/{category}/{timestamp}-{random}-{name}.{ext}',
    # Resultado: org-1/references/1706356800000-abc123-ref.jpg
    
    'fonts': 'org-{org_id}/{category}/{name}.{ext}',
    # Resultado: org-1/fonts/Roboto-Bold.ttf (sem timestamp!)
    
    'documents': 'org-{org_id}/{category}/{date}/{timestamp}-{random}.{ext}',
    # Resultado: org-1/documents/20260127/1706356800000-abc123.pdf
    
    'posts': 'org-{org_id}/posts/{date}/{random}.{ext}',
    # Resultado: org-1/posts/20260127/abc123def456.png
}
```

#### **Exemplos Práticos:**

**1. Fonte com nome específico:**
```python
# View para upload de fonte
@login_required
def upload_font(request):
    data = json.loads(request.body)
    
    presigned = S3Service.generate_presigned_upload_url(
        file_name='Roboto-Bold.ttf',
        file_type='font/ttf',
        file_size=200000,
        category='fonts',
        organization_id=request.organization.id,
        template='org-{org_id}/fontes/{font_family}_{variant}.{ext}',
        custom_data={
            'font_family': 'Roboto',
            'variant': 'Bold'
        }
    )
    
    # Resultado: org-1/fontes/Roboto_Bold.ttf
    return JsonResponse({'success': True, 'data': presigned})
```

**2. Post de mídia social com data:**
```python
from datetime import datetime

@login_required
def upload_post(request):
    presigned = S3Service.generate_presigned_upload_url(
        file_name='post.png',
        file_type='image/png',
        file_size=1000000,
        category='posts',
        organization_id=request.organization.id,
        custom_data={
            'date': datetime.now().strftime('%Y%m%d'),
            'campaign': 'natal2026'
        }
    )
    
    # Resultado (usando template padrão): org-1/posts/20260127/abc123def456.png
    return JsonResponse({'success': True, 'data': presigned})
```

**3. Referência de produto:**
```python
@login_required
def upload_product_reference(request):
    presigned = S3Service.generate_presigned_upload_url(
        file_name='produto.jpg',
        file_type='image/jpeg',
        file_size=800000,
        category='references',
        organization_id=request.organization.id,
        template='org-{org_id}/produtos/{product_id}/{view_angle}/{random}.{ext}',
        custom_data={
            'product_id': 'PROD-789',
            'view_angle': 'frontal'
        }
    )
    
    # Resultado: org-1/produtos/PROD-789/frontal/abc123def456.jpg
    return JsonResponse({'success': True, 'data': presigned})
```

**4. Documento jurídico com estrutura complexa:**
```python
@login_required
def upload_contract(request):
    presigned = S3Service.generate_presigned_upload_url(
        file_name='contrato.pdf',
        file_type='application/pdf',
        file_size=2000000,
        category='documents',
        organization_id=request.organization.id,
        template='org-{org_id}/juridico/{year}/{month}/contrato-{client_id}-{timestamp}.{ext}',
        custom_data={
            'year': '2026',
            'month': '01',
            'client_id': '12345'
        }
    )
    
    # Resultado: org-1/juridico/2026/01/contrato-12345-1706356800000.pdf
    return JsonResponse({'success': True, 'data': presigned})
```

**5. Avatar de usuário:**
```python
@login_required
def upload_avatar(request):
    presigned = S3Service.generate_presigned_upload_url(
        file_name='avatar.jpg',
        file_type='image/jpeg',
        file_size=500000,
        category='avatars',
        organization_id=request.organization.id,
        template='org-{org_id}/usuarios/{user_id}/avatar_{timestamp}.{ext}',
        custom_data={
            'user_id': request.user.id
        }
    )
    
    # Resultado: org-1/usuarios/123/avatar_1706356800000.jpg
    return JsonResponse({'success': True, 'data': presigned})
```

#### **Configurar Templates no Settings:**

```python
# config/settings/base.py

# Templates de nomenclatura S3 (opcional - sobrescreve padrões)
S3_FILENAME_TEMPLATES = {
    'logos': 'org-{org_id}/logos/{name}_v{version}.{ext}',
    'fonts': 'org-{org_id}/fontes/{font_family}_{variant}.{ext}',
    'posts': 'org-{org_id}/midia-social/{platform}/{date}/{random}.{ext}',
    'documents': 'org-{org_id}/docs/{department}/{year}/{month}/{type}_{timestamp}.{ext}',
    'avatars': 'org-{org_id}/usuarios/{user_id}/avatar_{timestamp}.{ext}',
}

# Usar nas views
from django.conf import settings

template = settings.S3_FILENAME_TEMPLATES.get('fonts')
presigned = S3Service.generate_presigned_upload_url(
    ...,
    template=template,
    custom_data={'font_family': 'Roboto', 'variant': 'Bold'}
)
```

#### **Vantagens:**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Fontes** | `170635-abc-Roboto.ttf` | `Roboto_Bold.ttf` ✅ |
| **Posts** | `170635-abc-post.png` | `posts/20260127/abc.png` ✅ |
| **Produtos** | `170635-abc-ref.jpg` | `produtos/PROD-789/frontal/abc.jpg` ✅ |
| **Busca S3** | Por timestamp 🟡 | Por estrutura lógica ✅ |
| **Organização** | Razoável 🟡 | Excelente ✅ |
| **Manutenção** | Difícil 🟡 | Fácil ✅ |

---

## 13.2 Verificar Models Atuais

**Models já existentes no projeto:**

```python
# apps/knowledge/models.py

class Logo(models.Model):
    """
    Model já existente - PERFEITO!
    Já tem campos s3_key e s3_url
    """
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    logo_type = models.CharField(
        max_length=50,
        choices=[
            ('principal', 'Principal'),
            ('horizontal', 'Horizontal'),
            ('vertical', 'Vertical'),
            ('simbolo', 'Símbolo'),
        ]
    )
    s3_key = models.CharField(max_length=500)  # ✅ Já existe!
    s3_url = models.URLField(max_length=1000)  # ✅ Já existe!
    file_format = models.CharField(max_length=10)
    is_primary = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_preview_url(self):
        """Gera URL temporária para preview"""
        from apps.core.services.s3_service import S3Service
        return S3Service.generate_presigned_download_url(self.s3_key)


class ReferenceImage(models.Model):
    """
    Model já existente - PERFEITO!
    Já tem campos s3_key e s3_url
    """
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    s3_key = models.CharField(max_length=500)  # ✅ Já existe!
    s3_url = models.URLField(max_length=1000)  # ✅ Já existe!
    file_size = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    perceptual_hash = models.CharField(max_length=64, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_preview_url(self):
        """Gera URL temporária para preview"""
        from apps.core.services.s3_service import S3Service
        return S3Service.generate_presigned_download_url(self.s3_key)
```

**✅ PERFEITO:** Models já estão prontos! Não precisa criar migrations.

### 13.2 Adicionar Métodos Úteis aos Models

**Arquivo:** `apps/knowledge/models.py` (adicionar aos models)

```python
from django.db import models
from apps.core.services.s3_service import S3Service


class Logo(models.Model):
    # ... campos existentes ...
    
    def get_preview_url(self, expires_in=3600):
        """
        Gera URL temporária para preview
        
        Args:
            expires_in: Segundos até expirar (padrão: 1 hora)
            
        Returns:
            URL temporária
        """
        return S3Service.generate_presigned_download_url(
            self.s3_key,
            expires_in=expires_in
        )
    
    def delete_from_s3(self):
        """Deleta arquivo do S3"""
        return S3Service.delete_file(self.s3_key)
    
    def delete(self, *args, **kwargs):
        """Override delete para deletar também do S3"""
        self.delete_from_s3()
        super().delete(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Retorna extensão do arquivo"""
        return self.s3_key.split('.')[-1] if '.' in self.s3_key else ''
    
    @property
    def organization_id(self):
        """Extrai organization_id do s3_key"""
        # s3_key formato: org-1/logos/file.png
        if self.s3_key.startswith('org-'):
            parts = self.s3_key.split('/')
            org_part = parts[0]  # 'org-1'
            return int(org_part.split('-')[1])  # 1
        return None
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Logo'
        verbose_name_plural = 'Logos'
    
    def __str__(self):
        return f"{self.name} ({self.get_logo_type_display()})"


class ReferenceImage(models.Model):
    # ... campos existentes ...
    
    def get_preview_url(self, expires_in=3600):
        """Gera URL temporária para preview"""
        return S3Service.generate_presigned_download_url(
            self.s3_key,
            expires_in=expires_in
        )
    
    def delete_from_s3(self):
        """Deleta arquivo do S3"""
        return S3Service.delete_file(self.s3_key)
    
    def delete(self, *args, **kwargs):
        """Override delete para deletar também do S3"""
        self.delete_from_s3()
        super().delete(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Retorna extensão do arquivo"""
        return self.s3_key.split('.')[-1] if '.' in self.s3_key else ''
    
    @property
    def aspect_ratio(self):
        """Calcula aspect ratio"""
        if self.height > 0:
            return round(self.width / self.height, 2)
        return 0
    
    @property
    def organization_id(self):
        """Extrai organization_id do s3_key"""
        if self.s3_key.startswith('org-'):
            parts = self.s3_key.split('/')
            org_part = parts[0]
            return int(org_part.split('-')[1])
        return None
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Imagem de Referência'
        verbose_name_plural = 'Imagens de Referência'
    
    def __str__(self):
        return self.title
```

### 13.3 Django Admin com Preview

**Arquivo:** `apps/knowledge/admin.py`

```python
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from apps.knowledge.models import Logo, ReferenceImage


@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = [
        'preview_thumbnail',
        'name',
        'logo_type',
        'file_format',
        'is_primary',
        'uploaded_by',
        'created_at'
    ]
    list_filter = ['logo_type', 'is_primary', 'created_at']
    search_fields = ['name', 's3_key']
    readonly_fields = ['preview_image', 's3_key', 's3_url', 'created_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'logo_type', 'is_primary')
        }),
        ('Arquivo', {
            'fields': ('preview_image', 's3_key', 's3_url', 'file_format')
        }),
        ('Metadata', {
            'fields': ('knowledge_base', 'uploaded_by', 'created_at')
        }),
    )
    
    def preview_thumbnail(self, obj):
        """Thumbnail pequeno na lista"""
        try:
            url = obj.get_preview_url()
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;">',
                url
            )
        except:
            return '(sem preview)'
    preview_thumbnail.short_description = 'Preview'
    
    def preview_image(self, obj):
        """Preview grande no form"""
        try:
            url = obj.get_preview_url()
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px;">',
                url
            )
        except:
            return '(sem preview)'
    preview_image.short_description = 'Preview do Logo'


@admin.register(ReferenceImage)
class ReferenceImageAdmin(admin.ModelAdmin):
    list_display = [
        'preview_thumbnail',
        'title',
        'dimensions',
        'file_size_display',
        'uploaded_by',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['title', 'description', 's3_key']
    readonly_fields = [
        'preview_image',
        's3_key',
        's3_url',
        'file_size',
        'width',
        'height',
        'perceptual_hash',
        'created_at'
    ]
    
    fieldsets = (
        ('Informações', {
            'fields': ('title', 'description')
        }),
        ('Arquivo', {
            'fields': (
                'preview_image',
                's3_key',
                's3_url',
                'file_size',
                'width',
                'height'
            )
        }),
        ('Metadata', {
            'fields': ('knowledge_base', 'perceptual_hash', 'uploaded_by', 'created_at')
        }),
    )
    
    def preview_thumbnail(self, obj):
        """Thumbnail na lista"""
        try:
            url = obj.get_preview_url()
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;">',
                url
            )
        except:
            return '(sem preview)'
    preview_thumbnail.short_description = 'Preview'
    
    def preview_image(self, obj):
        """Preview grande no form"""
        try:
            url = obj.get_preview_url()
            return format_html(
                '<img src="{}" style="max-width: 600px; max-height: 600px;">',
                url
            )
        except:
            return '(sem preview)'
    preview_image.short_description = 'Preview da Imagem'
    
    def dimensions(self, obj):
        """Exibe dimensões"""
        return f"{obj.width}x{obj.height}px"
    dimensions.short_description = 'Dimensões'
    
    def file_size_display(self, obj):
        """Formata tamanho do arquivo"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'Tamanho'
```

---

## 14. Testes de Segurança

### 14.1 Testes Unitários do S3Service

**Arquivo:** `apps/core/tests/test_s3_service.py`

```python
import pytest
from django.test import TestCase
from django.conf import settings
from apps.core.services.s3_service import S3Service
from apps.core.utils.file_validators import FileValidator


class TestS3Service(TestCase):
    """Testes para S3Service"""
    
    def test_generate_secure_filename(self):
        """Testa geração de nome seguro"""
        filename = S3Service.generate_secure_filename(
            original_name='logo principal.png',
            file_type='image/png',
            category='logos',
            organization_id=1
        )
        
        # Verificar formato
        self.assertTrue(filename.startswith('org-1/logos/'))
        self.assertTrue(filename.endswith('.png'))
        
        # Verificar que espaços foram removidos
        self.assertNotIn(' ', filename)
        
        # Verificar que tem timestamp e random
        parts = filename.split('/')[-1].split('-')
        self.assertTrue(len(parts) >= 3)
    
    def test_validate_organization_access_valid(self):
        """Testa validação de acesso válido"""
        s3_key = 'org-1/logos/file.png'
        organization_id = 1
        
        # Não deve lançar exceção
        result = S3Service.validate_organization_access(s3_key, organization_id)
        self.assertTrue(result)
    
    def test_validate_organization_access_invalid(self):
        """Testa validação de acesso inválido"""
        s3_key = 'org-2/logos/file.png'
        organization_id = 1
        
        # Deve lançar ValueError
        with self.assertRaises(ValueError) as context:
            S3Service.validate_organization_access(s3_key, organization_id)
        
        self.assertIn('Acesso negado', str(context.exception))
    
    def test_validate_organization_access_path_traversal(self):
        """Testa proteção contra path traversal"""
        malicious_keys = [
            '../org-2/logos/file.png',
            'org-1/../org-2/logos/file.png',
            'org-1/logos/../../org-2/logos/file.png'
        ]
        
        for key in malicious_keys:
            with self.assertRaises(ValueError):
                S3Service.validate_organization_access(key, 1)


class TestFileValidator(TestCase):
    """Testes para FileValidator"""
    
    def test_validate_file_type_valid(self):
        """Testa validação de tipo válido"""
        is_valid, error = FileValidator.validate_file_type('image/png', 'logos')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_file_type_invalid(self):
        """Testa validação de tipo inválido"""
        is_valid, error = FileValidator.validate_file_type('video/mp4', 'logos')
        self.assertFalse(is_valid)
        self.assertIn('não permitido', error)
    
    def test_validate_file_size_valid(self):
        """Testa validação de tamanho válido"""
        size = 1 * 1024 * 1024  # 1MB
        is_valid, error = FileValidator.validate_file_size(size, 'logos')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_file_size_too_large(self):
        """Testa validação de arquivo muito grande"""
        size = 10 * 1024 * 1024  # 10MB (máximo para logos é 5MB)
        is_valid, error = FileValidator.validate_file_size(size, 'logos')
        self.assertFalse(is_valid)
        self.assertIn('muito grande', error)
    
    def test_validate_file_size_empty(self):
        """Testa validação de arquivo vazio"""
        is_valid, error = FileValidator.validate_file_size(0, 'logos')
        self.assertFalse(is_valid)
        self.assertIn('vazio', error)
```

### 14.2 Testes de Integração

**Arquivo:** `apps/knowledge/tests/test_upload_views.py`

```python
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.knowledge.models import Logo, KnowledgeBase
from apps.core.models import Organization


User = get_user_model()


class TestUploadViews(TestCase):
    """Testes de integração para views de upload"""
    
    def setUp(self):
        """Configurar teste"""
        # Criar usuário e organização
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(name='Test Org')
        self.kb = KnowledgeBase.objects.create(
            organization=self.organization,
            name='Test KB'
        )
        
        # Configurar client
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Simular middleware que adiciona organization ao request
        # (ajuste conforme seu middleware real)
    
    def test_generate_logo_upload_url_success(self):
        """Testa geração de upload URL com sucesso"""
        data = {
            'fileName': 'logo.png',
            'fileType': 'image/png',
            'fileSize': 500000  # 500KB
        }
        
        response = self.client.post(
            '/knowledge/logo/upload-url/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        self.assertIn('upload_url', result['data'])
        self.assertIn('s3_key', result['data'])
        self.assertIn('expires_in', result['data'])
        
        # Verificar formato do s3_key
        s3_key = result['data']['s3_key']
        self.assertTrue(s3_key.startswith(f'org-{self.organization.id}/logos/'))
    
    def test_generate_logo_upload_url_invalid_type(self):
        """Testa rejeição de tipo inválido"""
        data = {
            'fileName': 'video.mp4',
            'fileType': 'video/mp4',
            'fileSize': 500000
        }
        
        response = self.client.post(
            '/knowledge/logo/upload-url/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertFalse(result['success'])
        self.assertIn('não permitido', result['error'])
    
    def test_generate_logo_upload_url_file_too_large(self):
        """Testa rejeição de arquivo muito grande"""
        data = {
            'fileName': 'logo.png',
            'fileType': 'image/png',
            'fileSize': 10 * 1024 * 1024  # 10MB (máx é 5MB)
        }
        
        response = self.client.post(
            '/knowledge/logo/upload-url/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertFalse(result['success'])
        self.assertIn('muito grande', result['error'])
    
    def test_create_logo_success(self):
        """Testa criação de logo com sucesso"""
        data = {
            'name': 'Logo Principal',
            'logoType': 'principal',
            's3Key': f'org-{self.organization.id}/logos/123-abc-logo.png',
            'fileFormat': 'png',
            'isPrimary': True
        }
        
        response = self.client.post(
            '/knowledge/logo/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        self.assertIn('id', result['data'])
        
        # Verificar que logo foi criado no banco
        logo = Logo.objects.get(id=result['data']['id'])
        self.assertEqual(logo.name, 'Logo Principal')
        self.assertEqual(logo.logo_type, 'principal')
        self.assertTrue(logo.is_primary)
    
    def test_create_logo_wrong_organization(self):
        """Testa que não pode criar logo de outra organização"""
        data = {
            'name': 'Logo Malicioso',
            'logoType': 'principal',
            's3Key': 'org-999/logos/123-abc-logo.png',  # Org diferente
            'fileFormat': 'png',
            'isPrimary': False
        }
        
        response = self.client.post(
            '/knowledge/logo/create/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        
        result = response.json()
        self.assertFalse(result['success'])
        self.assertIn('Acesso negado', result['error'])
```

### 14.3 Teste de Segurança Multi-tenant

**Arquivo:** `apps/core/tests/test_multi_tenant_security.py`

```python
import pytest
from django.test import TestCase
from apps.core.services.s3_service import S3Service


class TestMultiTenantSecurity(TestCase):
    """Testes de segurança multi-tenant"""
    
    def test_organization_cannot_access_other_org_files(self):
        """Organização não pode acessar arquivos de outra organização"""
        # Org 1 tenta acessar arquivo da Org 2
        s3_key_org2 = 'org-2/logos/secret-logo.png'
        organization_id_org1 = 1
        
        with self.assertRaises(ValueError) as context:
            S3Service.validate_organization_access(s3_key_org2, organization_id_org1)
        
        self.assertIn('Acesso negado', str(context.exception))
        self.assertIn('org-1/', str(context.exception))
    
    def test_path_traversal_attack_blocked(self):
        """Path traversal deve ser bloqueado"""
        malicious_keys = [
            '../org-2/logos/file.png',
            'org-1/../org-2/logos/file.png',
            'org-1/logos/../../org-2/logos/file.png',
            'org-1/logos/../../../etc/passwd',
        ]
        
        for malicious_key in malicious_keys:
            with self.assertRaises(ValueError) as context:
                S3Service.validate_organization_access(malicious_key, 1)
            
            error_msg = str(context.exception)
            self.assertIn('Acesso negado', error_msg)
    
    def test_filename_generation_prevents_collision(self):
        """Nomes de arquivo devem ser únicos"""
        names = set()
        
        # Gerar 1000 nomes
        for i in range(1000):
            name = S3Service.generate_secure_filename(
                original_name='logo.png',
                file_type='image/png',
                category='logos',
                organization_id=1
            )
            names.add(name)
        
        # Todos devem ser únicos
        self.assertEqual(len(names), 1000)
    
    def test_filename_sanitization(self):
        """Caracteres perigosos devem ser removidos"""
        dangerous_names = [
            '../../../etc/passwd',
            'logo<script>alert(1)</script>.png',
            'logo"; DROP TABLE users; --.png',
            'logo\x00.png',
            'logo/../../other.png',
        ]
        
        for dangerous_name in dangerous_names:
            safe_name = S3Service.generate_secure_filename(
                original_name=dangerous_name,
                file_type='image/png',
                category='logos',
                organization_id=1
            )
            
            # Não deve conter caracteres perigosos
            self.assertNotIn('<', safe_name)
            self.assertNotIn('>', safe_name)
            self.assertNotIn('"', safe_name)
            self.assertNotIn("'", safe_name)
            self.assertNotIn('\x00', safe_name)
            self.assertNotIn('..', safe_name)
            
            # Deve estar no formato correto
            self.assertTrue(safe_name.startswith('org-1/logos/'))
```

### 14.4 Executar Testes

```bash
# Todos os testes
python manage.py test

# Testes específicos
python manage.py test apps.core.tests.test_s3_service
python manage.py test apps.knowledge.tests.test_upload_views
python manage.py test apps.core.tests.test_multi_tenant_security

# Com coverage
pip install coverage
coverage run --source='apps' manage.py test
coverage report
coverage html  # Gera relatório HTML
```

---

## 15. Deploy para Produção

### 15.1 Checklist Pré-Deploy

**Segurança:**
- [ ] `.env` não está no Git
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado
- [ ] `SECRET_KEY` forte e único
- [ ] HTTPS habilitado
- [ ] CORS configurado apenas para domínios corretos
- [ ] Rate limiting ativado
- [ ] Credenciais AWS em variáveis de ambiente (não hardcoded)

**AWS:**
- [ ] Bucket S3 criado
- [ ] CORS configurado
- [ ] Versionamento habilitado
- [ ] Criptografia habilitada
- [ ] Lifecycle policies configuradas
- [ ] IAM user com permissões mínimas
- [ ] CloudWatch logs habilitados

**Código:**
- [ ] Todos os testes passando
- [ ] Migrations aplicadas
- [ ] Static files coletados
- [ ] Requirements.txt atualizado

**Documentação:**
- [ ] README atualizado
- [ ] API documentada
- [ ] Variáveis de ambiente documentadas

### 15.2 Configurar Variáveis de Ambiente (Produção)

**Heroku:**
```bash
heroku config:set AWS_REGION=us-east-1
heroku config:set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
heroku config:set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG
heroku config:set AWS_BUCKET_NAME=iamkt-uploads
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=.herokuapp.com
```

**AWS Elastic Beanstalk:**
```bash
eb setenv AWS_REGION=us-east-1 \
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
    AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG \
    AWS_BUCKET_NAME=iamkt-uploads \
    DEBUG=False
```

**Docker:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    environment:
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_BUCKET_NAME=iamkt-uploads
      - DEBUG=False
```

### 15.3 Settings.py para Produção

**Arquivo:** `config/settings/production.py`

```python
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'seu-dominio.com',
    'www.seu-dominio.com',
]

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# AWS S3
AWS_REGION = os.environ['AWS_REGION']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']

# CORS
CORS_ALLOWED_ORIGINS = [
    'https://seu-dominio.com',
    'https://www.seu-dominio.com',
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'apps.core.services.s3_service': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Static Files (se usando CloudFront/CDN)
# AWS_S3_CUSTOM_DOMAIN = 'd1234567890abc.cloudfront.net'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

### 15.4 Nginx Configuration

**Arquivo:** `/etc/nginx/sites-available/seu-app`

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Client Max Body Size (para uploads grandes)
    client_max_body_size 20M;
    
    # Static Files
    location /static/ {
        alias /opt/iamkt/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media Files (se houver)
    location /media/ {
        alias /opt/iamkt/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
    
    # Django Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 15.5 Supervisor (Gunicorn)

**Arquivo:** `/etc/supervisor/conf.d/iamkt.conf`

```ini
[program:iamkt]
command=/opt/iamkt/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 60 --access-logfile - --error-logfile -
directory=/opt/iamkt
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/iamkt/gunicorn.log
stderr_logfile=/var/log/iamkt/gunicorn_error.log
environment=DJANGO_SETTINGS_MODULE="config.settings.production"
```

### 15.6 Script de Deploy

**Arquivo:** `deploy.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variáveis
APP_DIR="/opt/iamkt"
VENV_DIR="$APP_DIR/venv"

# 1. Pull do código
echo -e "${YELLOW}1. Atualizando código...${NC}"
cd $APP_DIR
git pull origin main

# 2. Ativar virtual environment
echo -e "${YELLOW}2. Ativando virtual environment...${NC}"
source $VENV_DIR/bin/activate

# 3. Instalar dependências
echo -e "${YELLOW}3. Instalando dependências...${NC}"
pip install -r requirements.txt --quiet

# 4. Coletar static files
echo -e "${YELLOW}4. Coletando static files...${NC}"
python manage.py collectstatic --noinput --clear

# 5. Aplicar migrations
echo -e "${YELLOW}5. Aplicando migrations...${NC}"
python manage.py migrate --noinput

# 6. Verificar configuração Django
echo -e "${YELLOW}6. Verificando configuração...${NC}"
python manage.py check --deploy

# 7. Executar testes
echo -e "${YELLOW}7. Executando testes...${NC}"
python manage.py test --parallel

# 8. Restartar Gunicorn
echo -e "${YELLOW}8. Restartando Gunicorn...${NC}"
sudo supervisorctl restart iamkt

# 9. Reload Nginx
echo -e "${YELLOW}9. Recarregando Nginx...${NC}"
sudo nginx -t && sudo systemctl reload nginx

echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"

# 10. Verificar status
echo -e "${YELLOW}10. Status dos serviços:${NC}"
sudo supervisorctl status iamkt
sudo systemctl status nginx --no-pager | head -n 3

# 11. Testar endpoint
echo -e "${YELLOW}11. Testando endpoint...${NC}"
curl -f https://seu-dominio.com/api/health || echo "❌ Falha no health check"

echo -e "${GREEN}🎉 Deploy finalizado!${NC}"
```

**Uso:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 16. Monitoring e Manutenção

### 16.1 CloudWatch Metrics

**Configurar alarmes no AWS CloudWatch:**

```bash
# Alarme: Muitos erros 4xx (bad requests)
aws cloudwatch put-metric-alarm \
    --alarm-name iamkt-s3-high-4xx-errors \
    --alarm-description "Alto número de erros 4xx no bucket S3" \
    --metric-name 4xxErrors \
    --namespace AWS/S3 \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 100 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=BucketName,Value=iamkt-uploads \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Alarme: Muitos erros 5xx (server errors)
aws cloudwatch put-metric-alarm \
    --alarm-name iamkt-s3-high-5xx-errors \
    --alarm-description "Alto número de erros 5xx no bucket S3" \
    --metric-name 5xxErrors \
    --namespace AWS/S3 \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=BucketName,Value=iamkt-uploads \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Alarme: Uso de armazenamento alto
aws cloudwatch put-metric-alarm \
    --alarm-name iamkt-s3-high-storage \
    --alarm-description "Uso de armazenamento S3 acima de 80%" \
    --metric-name BucketSizeBytes \
    --namespace AWS/S3 \
    --statistic Average \
    --period 86400 \
    --evaluation-periods 1 \
    --threshold 85899345920 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=BucketName,Value=iamkt-uploads Name=StorageType,Value=StandardStorage \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:billing-alerts
```

### 16.2 Django Logging

**Arquivo:** `apps/core/services/s3_service.py` (adicionar logging)

```python
import logging

logger = logging.getLogger(__name__)


class S3Service:
    # ... código existente ...
    
    @classmethod
    def generate_presigned_upload_url(cls, ...):
        """Gera Presigned URL para upload"""
        try:
            # ... validações ...
            
            # Log de sucesso
            logger.info(
                f"Presigned URL gerada - "
                f"Org: {organization_id}, "
                f"Categoria: {category}, "
                f"Arquivo: {file_name}, "
                f"Tamanho: {file_size} bytes"
            )
            
            return {...}
            
        except ValueError as e:
            logger.warning(
                f"Validação falhou - "
                f"Org: {organization_id}, "
                f"Arquivo: {file_name}, "
                f"Erro: {str(e)}"
            )
            raise
            
        except ClientError as e:
            logger.error(
                f"Erro AWS - "
                f"Org: {organization_id}, "
                f"Arquivo: {file_name}, "
                f"Erro: {str(e)}",
                exc_info=True
            )
            raise
```

### 16.3 Health Check Endpoint

**Arquivo:** `apps/core/views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from apps.core.services.s3_service import S3Service
import boto3


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check completo
    
    GET /api/health/
    
    Response:
        {
            "status": "ok",
            "checks": {
                "database": "ok",
                "s3": "ok"
            },
            "version": "1.0.0"
        }
    """
    checks = {}
    overall_status = "ok"
    
    # 1. Check Database
    try:
        from django.db import connection
        connection.ensure_connection()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        overall_status = 'degraded'
    
    # 2. Check S3
    try:
        s3_client = S3Service._get_s3_client()
        s3_client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
        checks['s3'] = 'ok'
    except Exception as e:
        checks['s3'] = f'error: {str(e)}'
        overall_status = 'degraded'
    
    status_code = 200 if overall_status == 'ok' else 503
    
    return JsonResponse({
        'status': overall_status,
        'checks': checks,
        'version': '1.0.0'
    }, status=status_code)
```

### 16.4 Comandos de Manutenção

**Arquivo:** `apps/knowledge/management/commands/cleanup_orphaned_s3_files.py`

```python
"""
Comando para limpar arquivos órfãos do S3
(arquivos que existem no S3 mas não no banco de dados)
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from apps.knowledge.models import Logo, ReferenceImage


class Command(BaseCommand):
    help = 'Remove arquivos órfãos do S3'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria deletado, sem deletar'
        )
        
        parser.add_argument(
            '--organization-id',
            type=int,
            help='Limpar apenas uma organização específica'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        org_id = options.get('organization_id')
        
        self.stdout.write(self.style.WARNING(
            f"🧹 Limpando arquivos órfãos do S3 "
            f"{'(DRY RUN)' if dry_run else ''}"
        ))
        
        # Conectar S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Obter todas as chaves do banco
        db_keys = set()
        db_keys.update(Logo.objects.values_list('s3_key', flat=True))
        db_keys.update(ReferenceImage.objects.values_list('s3_key', flat=True))
        
        self.stdout.write(f"📊 Arquivos no banco: {len(db_keys)}")
        
        # Listar arquivos no S3
        prefix = f"org-{org_id}/" if org_id else ""
        paginator = s3_client.get_paginator('list_objects_v2')
        
        total_s3_files = 0
        orphaned_files = []
        
        for page in paginator.paginate(Bucket=settings.AWS_BUCKET_NAME, Prefix=prefix):
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                s3_key = obj['Key']
                total_s3_files += 1
                
                if s3_key not in db_keys:
                    orphaned_files.append(s3_key)
        
        self.stdout.write(f"📊 Arquivos no S3: {total_s3_files}")
        self.stdout.write(f"🗑️  Arquivos órfãos: {len(orphaned_files)}")
        
        if not orphaned_files:
            self.stdout.write(self.style.SUCCESS("✅ Nenhum arquivo órfão encontrado"))
            return
        
        # Deletar órfãos
        if dry_run:
            self.stdout.write(self.style.WARNING("\n📋 Arquivos que seriam deletados:"))
            for key in orphaned_files[:10]:  # Mostrar apenas 10
                self.stdout.write(f"  - {key}")
            if len(orphaned_files) > 10:
                self.stdout.write(f"  ... e mais {len(orphaned_files) - 10}")
        else:
            self.stdout.write(self.style.WARNING("\n🗑️  Deletando arquivos..."))
            deleted = 0
            
            for key in orphaned_files:
                try:
                    s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=key)
                    deleted += 1
                    
                    if deleted % 100 == 0:
                        self.stdout.write(f"  Deletados: {deleted}/{len(orphaned_files)}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Erro ao deletar {key}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ {deleted} arquivos deletados"))
```

**Uso:**
```bash
# Dry run (apenas visualizar)
python manage.py cleanup_orphaned_s3_files --dry-run

# Executar limpeza
python manage.py cleanup_orphaned_s3_files

# Limpar apenas org específica
python manage.py cleanup_orphaned_s3_files --organization-id 1
```

---

## 17. Troubleshooting Django

### 17.1 Problemas Comuns e Soluções

#### **Problema: "Access Denied" ao gerar Presigned URL**

**Sintomas:**
```
ClientError: An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
```

**Causas possíveis:**
1. Credenciais AWS incorretas
2. IAM policy não permite operação
3. Bucket não existe

**Diagnóstico:**
```python
# No Django shell
python manage.py shell

from apps.core.services.s3_service import S3Service
from django.conf import settings

# 1. Verificar credenciais
print(f"Access Key: {settings.AWS_ACCESS_KEY_ID}")
print(f"Bucket: {settings.AWS_BUCKET_NAME}")

# 2. Testar conexão
client = S3Service._get_s3_client()
response = client.list_buckets()
print(f"Buckets: {[b['Name'] for b in response['Buckets']]}")

# 3. Testar permissões
try:
    response = client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
    print("✅ Bucket acessível")
except Exception as e:
    print(f"❌ Erro: {e}")
```

**Solução:**
```bash
# Verificar IAM policy
aws iam list-attached-user-policies --user-name iamkt-upload-api-user

# Testar acesso direto
aws s3 ls s3://iamkt-uploads --profile iamkt
```

---

#### **Problema: CORS Error no Frontend**

**Sintomas:**
```
Access to fetch at 'https://bucket.s3.amazonaws.com/...' from origin 'http://localhost:8000' 
has been blocked by CORS policy
```

**Diagnóstico:**
```bash
# Verificar CORS atual
aws s3api get-bucket-cors --bucket iamkt-uploads

# Testar CORS via curl
curl -X OPTIONS https://iamkt-uploads.s3.amazonaws.com/test.png \
  -H "Origin: http://localhost:8000" \
  -H "Access-Control-Request-Method: PUT" \
  -v
```

**Solução:**
```bash
# Reconfigurar CORS
cat > cors.json << 'EOF'
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
EOF

aws s3api put-bucket-cors \
    --bucket iamkt-uploads \
    --cors-configuration file://cors.json
```

---

#### **Problema: "SignatureDoesNotMatch"**

**Sintomas:**
```
The request signature we calculated does not match the signature you provided
```

**Causas:**
1. Secret Key incorreta
2. Hora do servidor dessincronizada
3. Região incorreta

**Solução:**
```bash
# 1. Verificar credenciais no .env
cat .env | grep AWS_

# 2. Verificar hora do servidor
date
# Se estiver errada, sincronizar:
sudo ntpdate -s time.nist.gov

# 3. Testar credenciais
aws sts get-caller-identity
```

---

#### **Problema: Upload muito lento**

**Sintomas:**
- Upload de 1MB leva mais de 30 segundos

**Causas:**
1. Região S3 muito distante
2. Rede lenta
3. Arquivo não está sendo enviado diretamente ao S3

**Diagnóstico:**
```javascript
// No console do browser
console.time('upload');
fetch(presignedUrl, {
    method: 'PUT',
    body: file
}).then(() => console.timeEnd('upload'));
```

**Solução:**
```bash
# 1. Verificar latência para região
ping s3.us-east-1.amazonaws.com

# 2. Considerar S3 Transfer Acceleration
aws s3api put-bucket-accelerate-configuration \
    --bucket iamkt-uploads \
    --accelerate-configuration Status=Enabled

# Usar endpoint acelerado
# https://iamkt-uploads.s3-accelerate.amazonaws.com
```

---

#### **Problema: ImproperlyConfigured em produção**

**Sintomas:**
```
django.core.exceptions.ImproperlyConfigured: AWS credentials missing
```

**Solução:**
```bash
# Verificar variáveis de ambiente
printenv | grep AWS_

# Se usando Heroku
heroku config

# Se usando Docker
docker exec -it container_name printenv | grep AWS_

# Adicionar variáveis faltantes
heroku config:set AWS_ACCESS_KEY_ID=...
```

---

### 17.2 Debug Mode para S3Service

**Arquivo:** `apps/core/services/s3_service.py` (adicionar método de debug)

```python
class S3Service:
    # ... código existente ...
    
    @classmethod
    def debug_info(cls):
        """
        Retorna informações de debug sobre configuração S3
        
        Usage:
            from apps.core.services.s3_service import S3Service
            print(S3Service.debug_info())
        """
        from django.conf import settings
        import boto3
        
        info = {
            'region': settings.AWS_REGION,
            'bucket': settings.AWS_BUCKET_NAME,
            'access_key_set': bool(settings.AWS_ACCESS_KEY_ID),
            'secret_key_set': bool(settings.AWS_SECRET_ACCESS_KEY),
        }
        
        # Testar conexão
        try:
            client = cls._get_s3_client()
            response = client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
            info['bucket_accessible'] = True
            info['bucket_region'] = response['ResponseMetadata']['HTTPHeaders'].get('x-amz-bucket-region')
        except Exception as e:
            info['bucket_accessible'] = False
            info['error'] = str(e)
        
        # Testar CORS
        try:
            client = cls._get_s3_client()
            cors = client.get_bucket_cors(Bucket=settings.AWS_BUCKET_NAME)
            info['cors_configured'] = True
            info['cors_origins'] = [
                rule['AllowedOrigins'] 
                for rule in cors['CORSRules']
            ]
        except:
            info['cors_configured'] = False
        
        return info
```

**Uso:**
```python
# Django shell
python manage.py shell

from apps.core.services.s3_service import S3Service
import json
print(json.dumps(S3Service.debug_info(), indent=2))
```

---

## 18. Apêndices e Recursos

### 18.1 Resumo de URLs da API

```
# Upload
POST   /knowledge/logo/upload-url/              # Gerar URL para upload de logo
POST   /knowledge/logo/create/                  # Criar registro após upload
POST   /knowledge/reference/upload-url/         # Gerar URL para upload de referência
POST   /knowledge/reference/create/             # Criar registro após upload

# Preview
GET    /knowledge/preview-url/?s3_key=...       # Obter URL de preview
GET    /knowledge/logo/<id>/preview/            # Preview de logo específico

# Delete
DELETE /knowledge/logo/<id>/                    # Deletar logo
DELETE /knowledge/reference/<id>/               # Deletar referência

# Health
GET    /api/health/                             # Health check
```

### 18.2 Estrutura Final de Arquivos

```
seu_projeto_django/
├── apps/
│   ├── core/
│   │   ├── services/
│   │   │   └── s3_service.py              ✅ Service Layer
│   │   ├── utils/
│   │   │   ├── file_validators.py         ✅ Validadores
│   │   │   └── image_validators.py        ✅ Validadores de imagem
│   │   ├── tests/
│   │   │   ├── test_s3_service.py         ✅ Testes
│   │   │   └── test_multi_tenant_security.py
│   │   └── views.py                        ✅ Health check
│   │
│   └── knowledge/
│       ├── models.py                       ✅ Logo, ReferenceImage
│       ├── views.py                        ✅ Upload/Preview views
│       ├── urls.py                         ✅ URLs
│       ├── admin.py                        ✅ Admin com preview
│       ├── management/
│       │   └── commands/
│       │       └── cleanup_orphaned_s3_files.py  ✅ Comando manutenção
│       └── tests/
│           └── test_upload_views.py        ✅ Testes de integração
│
├── static/
│   └── js/
│       ├── s3-uploader.js                  ✅ Upload class
│       ├── image-preview-loader.js         ✅ Lazy loading
│       └── image-validator.js              ✅ Validação frontend
│
├── templates/
│   └── knowledge/
│       ├── logo_upload.html                ✅ Interface upload
│       └── logo_list.html                  ✅ Lista com lazy loading
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py                   ✅ Settings produção
│   └── urls.py
│
├── deploy.sh                               ✅ Script deploy
├── requirements.txt                        ✅ Dependências
└── .env.example                            ✅ Template variáveis
```

### 18.3 Comandos Úteis Django

```bash
# Development
python manage.py runserver
python manage.py shell
python manage.py test
python manage.py makemigrations
python manage.py migrate

# Production
python manage.py check --deploy
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Manutenção
python manage.py cleanup_orphaned_s3_files --dry-run
python manage.py cleanup_orphaned_s3_files

# Debug
python manage.py shell
>>> from apps.core.services.s3_service import S3Service
>>> S3Service.debug_info()
```

### 18.4 Links e Recursos

**Documentação Oficial:**
- Django: https://docs.djangoproject.com/
- Boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- AWS S3: https://docs.aws.amazon.com/s3/
- Presigned URLs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html

**Comunidade:**
- Django Forum: https://forum.djangoproject.com/
- Stack Overflow: Tag `django`, `boto3`, `amazon-s3`
- Reddit: r/django, r/aws

**Ferramentas:**
- AWS CLI: https://aws.amazon.com/cli/
- S3 Browser: https://s3browser.com/
- Postman: Para testar API

---

## 🎉 Conclusão

Você agora tem um sistema completo de upload S3 integrado ao Django com:

✅ **Service Layer** reutilizável e testável  
✅ **Segurança** multi-tenant com isolamento por organização  
✅ **Preview** com lazy loading otimizado  
✅ **Validações** robustas (tipo, tamanho, dimensões)  
✅ **Testes** completos (unitários + integração)  
✅ **Deploy** automatizado para produção  
✅ **Monitoring** com CloudWatch e logging  
✅ **Manutenção** com comandos de limpeza  

**Próximos passos sugeridos:**
1. Implementar compressão automática de imagens
2. Adicionar geração de thumbnails
3. Implementar scan de vírus/malware
4. Adicionar suporte a vídeos
5. Implementar CloudFront para CDN

---

**Fim da Parte 2**  
**Guia Completo v4.0 - Django + S3 + Service Layer**
