# 📋 PLANEJAMENTO - PERFIL DA EMPRESA (MODO VISUALIZAÇÃO)

**Data:** 31/01/2026  
**Objetivo:** Implementar página de visualização do Perfil da Empresa após compilação N8N

---

## 🎯 VISÃO GERAL

### **Fluxo Completo**

```
1. Usuário clica "Aplicar Sugestões" (Modo Edição)
   ↓
2. Salvar dados no banco ✅ (já implementado)
   ↓
3. Marcar suggestions_reviewed = True
   ↓
4. Enviar para N8N (SEMSUGEST ou COMSUGEST)
   ↓
5. Redirecionar para /knowledge/perfil-visualizacao/
   ↓
6. Exibir estado "Compilando" (botão "Verificar Status")
   ↓
7. N8N retorna dados → Webhook salva em n8n_compilation
   ↓
8. Próximo reload → Exibir página completa
```

---

## 📡 PARTE 1: ENVIO AO N8N

### **1.1 Dois Fluxos de Envio**

#### **FLUXO SEMSUGEST** (Todas sugestões rejeitadas)
- **Condição:** Nenhuma sugestão foi aceita
- **Endpoint:** Variável de ambiente `N8N_WEBHOOK_COMPILE_SEMSUGEST`
- **Payload:** Mesmo modelo usado no salvamento da Base de Conhecimento

#### **FLUXO COMSUGEST** (Pelo menos 1 sugestão aceita)
- **Condição:** Pelo menos 1 sugestão foi aceita
- **Endpoint:** Variável de ambiente `N8N_WEBHOOK_COMPILE_COMSUGEST`
- **Payload:** Mesmo modelo usado no salvamento da Base de Conhecimento

---

### **1.2 Variáveis de Ambiente**

**Adicionar ao `.env.development`:**
```bash
# N8N - Compilação
N8N_WEBHOOK_COMPILE_SEMSUGEST=https://n8n.srv812718.hstgr.cloud/webhook/compilasemsugest-wind
N8N_WEBHOOK_COMPILE_COMSUGEST=https://n8n.srv812718.hstgr.cloud/webhook/compilacomsugest-wind
```

**Adicionar ao `.env.example`:**
```bash
# N8N - Compilação
N8N_WEBHOOK_COMPILE_SEMSUGEST=
N8N_WEBHOOK_COMPILE_COMSUGEST=
```

---

### **1.3 Modificações no Modelo**

**Arquivo:** `app/apps/knowledge/models.py`

**Adicionar campos:**
```python
# Compilação N8N
compilation_status = models.CharField(
    max_length=20,
    choices=[
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Completa'),
        ('error', 'Erro'),
    ],
    default='pending'
)
compilation_requested_at = models.DateTimeField(null=True, blank=True)
compilation_completed_at = models.DateTimeField(null=True, blank=True)
n8n_compilation = models.JSONField(default=dict, blank=True)
```

**Migração:** `0016_add_compilation_fields`

---

### **1.4 Reutilizar Código de Envio N8N**

**Arquivo:** `app/apps/knowledge/services/n8n_service.py`

**Adicionar método:**
```python
@staticmethod
def send_for_compilation(kb: KnowledgeBase, has_accepted_suggestions: bool) -> dict:
    """
    Envia dados da KB para compilação N8N.
    
    Args:
        kb: Instância do KnowledgeBase
        has_accepted_suggestions: True se pelo menos 1 sugestão foi aceita
    
    Returns:
        dict com status e mensagem
    """
    try:
        # Escolher endpoint baseado em sugestões aceitas
        if has_accepted_suggestions:
            webhook_url = settings.N8N_WEBHOOK_COMPILE_COMSUGEST
            flow_type = "comsugest"
        else:
            webhook_url = settings.N8N_WEBHOOK_COMPILE_SEMSUGEST
            flow_type = "semsugest"
        
        # Reutilizar payload existente (mesmo da Base de Conhecimento)
        payload = N8NService._build_knowledge_base_payload(kb)
        
        # Adicionar metadados
        payload['flow_type'] = flow_type
        payload['revision_id'] = kb.n8n_revision_id or str(uuid.uuid4())
        
        # Enviar para N8N
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-INTERNAL-TOKEN': settings.N8N_INTERNAL_TOKEN,
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        # Atualizar status
        kb.compilation_status = 'processing'
        kb.compilation_requested_at = timezone.now()
        kb.save(update_fields=['compilation_status', 'compilation_requested_at'])
        
        return {
            'success': True,
            'message': f'Dados enviados para compilação ({flow_type})',
            'flow_type': flow_type
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar para compilação N8N: {str(e)}")
        kb.compilation_status = 'error'
        kb.save(update_fields=['compilation_status'])
        
        return {
            'success': False,
            'message': f'Erro ao enviar para N8N: {str(e)}'
        }
```

---

### **1.5 Modificar View de Aplicar Sugestões**

**Arquivo:** `app/apps/knowledge/views_perfil.py`

**Modificar `perfil_apply_suggestions`:**
```python
@login_required
def perfil_apply_suggestions(request):
    """Aplica sugestões selecionadas e envia para compilação N8N"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        org = request.user.organization
        kb = KnowledgeBase.objects.filter(organization=org).first()
        
        if not kb:
            return JsonResponse({'success': False, 'message': 'Base não encontrada'}, status=404)
        
        data = json.loads(request.body)
        accepted_suggestions = data.get('accepted_suggestions', [])
        edited_fields = data.get('edited_fields', {})
        
        # 1. SALVAR DADOS NO BANCO (já implementado)
        # ... código existente de salvamento ...
        
        # 2. MARCAR SUGGESTIONS_REVIEWED = TRUE
        kb.suggestions_reviewed = True
        kb.suggestions_reviewed_at = timezone.now()
        kb.suggestions_reviewed_by = request.user
        kb.save(update_fields=['suggestions_reviewed', 'suggestions_reviewed_at', 'suggestions_reviewed_by'])
        
        # 3. ENVIAR PARA N8N
        has_accepted = len(accepted_suggestions) > 0
        n8n_result = N8NService.send_for_compilation(kb, has_accepted)
        
        if not n8n_result['success']:
            logger.warning(f"Falha ao enviar para N8N: {n8n_result['message']}")
        
        # 4. RETORNAR SUCESSO (frontend redireciona)
        return JsonResponse({
            'success': True,
            'message': 'Sugestões aplicadas com sucesso!',
            'redirect_url': '/knowledge/perfil-visualizacao/',
            'n8n_status': n8n_result['success'],
            'flow_type': n8n_result.get('flow_type', 'unknown')
        })
        
    except Exception as e:
        logger.error(f"Erro ao aplicar sugestões: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
```

---

### **1.6 Modificar JavaScript do Perfil (Modo Edição)**

**Arquivo:** `app/static/js/perfil.js`

**Modificar função `applySelectedSuggestions`:**
```javascript
async function applySelectedSuggestions() {
    // ... validações existentes ...
    
    try {
        const response = await fetch('/knowledge/perfil/apply-suggestions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                accepted_suggestions: acceptedSuggestions,
                edited_fields: window.editedFields || {}
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.toaster.success(data.message);
            
            // Redirecionar para página de visualização
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        } else {
            window.toaster.error(data.message);
        }
        
    } catch (error) {
        console.error('Erro ao aplicar sugestões:', error);
        window.toaster.error('Erro ao processar solicitação');
    }
}
```

---

## 📥 PARTE 2: RECEBIMENTO DO RETORNO N8N

### **2.1 Estrutura do JSON de Retorno**

```json
[{
    "evaluation": "SATISFACTORY",
    "scores": {
        "area_a": 85,
        "area_b": 75,
        "area_c": 70
    },
    "area_status": {
        "base": "SATISFACTORY",
        "digital_presence": "SATISFACTORY",
        "visual_identity": "SATISFACTORY"
    },
    "areas": {
        "base": {
            "identity_essence": "Texto...",
            "audience": "Texto...",
            "strategy_channels": "Texto...",
            "key_messages": ["msg1", "msg2"],
            "meta": {
                "confidence": "high",
                "notes": "Texto..."
            }
        },
        "digital_presence": {
            "website_url": "https://...",
            "social_networks": [
                {"network": "instagram", "url": "@handle"}
            ],
            "competitors": ["url1", "url2"],
            "meta": {...}
        },
        "visual_identity": {
            "palette_hex": ["#FF0A23", "#FFF700"],
            "typography": {
                "title": "Roboto",
                "body": "Roboto",
                "subtitle": "Roboto",
                "caption": "Roboto"
            },
            "logos": ["url1"],
            "reference_images": ["url1", "url2"],
            "meta": {...}
        }
    },
    "gaps": [],
    "link_checks": [
        {
            "url": "https://...",
            "status_hint": "ok",
            "verification": "format_only",
            "title": "Título",
            "summary": "Texto...",
            "notes": ""
        }
    ],
    "marketing_plan_4w": [
        {
            "week": 1,
            "focus": "Captação de Leads",
            "actions": ["ação1", "ação2"],
            "channels": ["Instagram", "Website"],
            "content_ideas": ["ideia1"],
            "kpis": ["kpi1"],
            "owner": "Equipe de Marketing",
            "cadence": "Semanal"
        }
    ],
    "assessment_summary": {
        "base": "Texto avaliação base",
        "digital_presence": "Texto avaliação presença digital",
        "visual_identity": "Texto avaliação identidade visual"
    },
    "improvements_summary": {
        "base": "Texto melhorias base",
        "digital_presence": "Texto melhorias presença digital",
        "visual_identity": "Texto melhorias identidade visual"
    },
    "marketing_input_summary": "Texto longo resumo..."
}]
```

---

### **2.2 Webhook para Receber Compilação**

**Arquivo:** `app/apps/knowledge/views_n8n.py`

**Adicionar endpoint:**
```python
@csrf_exempt
@require_http_methods(["POST"])
def n8n_compilation_webhook(request):
    """
    Webhook para receber compilação do N8N.
    Reutiliza camadas de segurança existentes.
    """
    
    # 1. VALIDAR TOKEN INTERNO
    internal_token = request.headers.get('X-INTERNAL-TOKEN')
    if internal_token != settings.N8N_INTERNAL_TOKEN:
        logger.warning(f"Token inválido no webhook de compilação")
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # 2. VALIDAR IP WHITELIST
    client_ip = request.headers.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR')
    allowed_ips = settings.N8N_ALLOWED_IPS.split(',')
    if client_ip not in allowed_ips:
        logger.warning(f"IP não autorizado: {client_ip}")
        return JsonResponse({'error': 'Forbidden'}, status=403)
    
    # 3. RATE LIMITING
    cache_key = f'n8n_compilation_webhook_{client_ip}'
    request_count = cache.get(cache_key, 0)
    if request_count >= 10:
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    cache.set(cache_key, request_count + 1, 60)
    
    try:
        # 4. PROCESSAR DADOS
        data = json.loads(request.body)
        
        # Extrair revision_id
        revision_id = data.get('revision_id')
        if not revision_id:
            return JsonResponse({'error': 'revision_id obrigatório'}, status=400)
        
        # Buscar KB
        kb = KnowledgeBase.objects.filter(n8n_revision_id=revision_id).first()
        if not kb:
            logger.error(f"KB não encontrado para revision_id: {revision_id}")
            return JsonResponse({'error': 'KB não encontrado'}, status=404)
        
        # 5. SALVAR COMPILAÇÃO
        compilation_data = data.get('compilation', [])
        if compilation_data:
            kb.n8n_compilation = compilation_data[0] if isinstance(compilation_data, list) else compilation_data
            kb.compilation_status = 'completed'
            kb.compilation_completed_at = timezone.now()
            kb.save(update_fields=['n8n_compilation', 'compilation_status', 'compilation_completed_at'])
            
            logger.info(f"✅ Compilação recebida para KB {kb.id} (org: {kb.organization.name})")
            
            return JsonResponse({
                'success': True,
                'message': 'Compilação recebida com sucesso',
                'kb_id': kb.id
            })
        else:
            return JsonResponse({'error': 'Dados de compilação vazios'}, status=400)
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook de compilação: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
```

---

### **2.3 Adicionar URL**

**Arquivo:** `app/apps/knowledge/urls.py`

```python
urlpatterns = [
    # ... rotas existentes ...
    
    # Webhook N8N - Compilação
    path('webhook/compilation/', views_n8n.n8n_compilation_webhook, name='n8n_compilation_webhook'),
]
```

---

## 🎨 PARTE 3: PÁGINA DE VISUALIZAÇÃO

### **3.1 View Backend**

**Arquivo:** `app/apps/knowledge/views.py`

**Criar nova view:**
```python
@login_required
def perfil_visualizacao_view(request):
    """
    Página de visualização do Perfil da Empresa (após compilação).
    """
    org = request.user.organization
    kb = KnowledgeBase.objects.filter(organization=org).first()
    
    if not kb:
        return redirect('knowledge:view')
    
    # Verificar se onboarding foi concluído
    if not kb.onboarding_completed:
        return redirect('knowledge:view')
    
    # Verificar se sugestões foram revisadas
    if not kb.suggestions_reviewed:
        return redirect('knowledge:perfil_view')
    
    # Estado da compilação
    compilation_status = kb.compilation_status
    compilation_data = kb.n8n_compilation or {}
    
    # Buscar dados complementares
    colors = kb.colors.all().order_by('order')
    typography = kb.typography_settings.all().order_by('order')
    logos = kb.logos.all().order_by('-is_primary', 'logo_type')
    references = kb.reference_images.all().order_by('-created_at')
    
    context = {
        'kb': kb,
        'compilation_status': compilation_status,
        'compilation_data': compilation_data,
        'colors': colors,
        'typography': typography,
        'logos': logos,
        'references': references,
        'kb_onboarding_completed': kb.onboarding_completed,
        'kb_suggestions_reviewed': kb.suggestions_reviewed,
    }
    
    return render(request, 'knowledge/perfil_visualizacao.html', context)
```

---

### **3.2 URL**

**Arquivo:** `app/apps/knowledge/urls.py`

```python
urlpatterns = [
    # ... rotas existentes ...
    
    # Perfil da Empresa - Visualização
    path('perfil-visualizacao/', views.perfil_visualizacao_view, name='perfil_visualizacao_view'),
]
```

---

### **3.3 Template HTML**

**Arquivo:** `app/templates/knowledge/perfil_visualizacao.html`

**Estrutura:**
```django
{% extends "base.html" %}
{% load static %}

{% block title %}Perfil da Empresa - Visualização{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/perfil-visualizacao.css' %}?v=20260131">
{% endblock %}

{% block content %}
<div class="perfil-visualizacao-container">
    
    {% if compilation_status == 'processing' %}
        <!-- ESTADO: COMPILANDO -->
        {% include 'knowledge/partials/perfil_compilando.html' %}
    
    {% elif compilation_status == 'completed' %}
        <!-- ESTADO: COMPILADO -->
        
        <!-- BLOCO 1: Header com Logo -->
        {% include 'knowledge/partials/perfil_viz_header.html' %}
        
        <!-- BLOCO 2: Resumo da Base de Conhecimento -->
        <section class="perfil-viz-section">
            <h2 class="section-title">Resumo da Base de Conhecimento</h2>
            <p class="section-subtitle">Gerado pelo agente de IA. Revise o conteúdo consolidado.</p>
            
            <!-- Linha 1: Base Consolidada + Presença Digital -->
            {% include 'knowledge/partials/perfil_viz_linha1.html' %}
            
            <!-- Linha 2: Identidade Visual -->
            {% include 'knowledge/partials/perfil_viz_linha2.html' %}
            
            <!-- Linha 3: Avaliação + Melhorias -->
            {% include 'knowledge/partials/perfil_viz_linha3.html' %}
            
            <!-- Linha 4: Plano de Marketing -->
            {% include 'knowledge/partials/perfil_viz_linha4.html' %}
            
            <!-- Linha 5: Lacunas Encontradas -->
            {% include 'knowledge/partials/perfil_viz_linha5.html' %}
            
            <!-- Linha 6: Links Verificados -->
            {% include 'knowledge/partials/perfil_viz_linha6.html' %}
        </section>
        
        <!-- Botão Editar Base -->
        <div class="perfil-viz-actions">
            <a href="{% url 'knowledge:view' %}" class="btn btn-secondary">
                Editar Base de Conhecimento
            </a>
        </div>
    
    {% elif compilation_status == 'error' %}
        <!-- ESTADO: ERRO -->
        {% include 'knowledge/partials/perfil_erro.html' %}
    
    {% endif %}
    
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/perfil-visualizacao.js' %}?v=20260131"></script>
{% endblock %}
```

---

### **3.4 Partials (Templates Reutilizáveis)**

#### **3.4.1 Estado Compilando**

**Arquivo:** `app/templates/knowledge/partials/perfil_compilando.html`

```django
<div class="perfil-empty-state">
    <div class="perfil-empty-icon">⏳</div>
    <h2>BASE EM COMPILAÇÃO</h2>
    <p>Sua Base está sendo compilada pelo nosso agente de IA...</p>
    <p class="text-muted">Isso pode levar alguns minutos. Aguarde e clique no botão abaixo para verificar o status.</p>
    <button onclick="window.location.reload()" class="btn btn-primary">
        Verificar Status
    </button>
</div>
```

---

#### **3.4.2 Header com Logo**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_header.html`

```django
<div class="perfil-header">
    <div class="perfil-header-logo">
        {% if kb.logo_primary %}
            <img src="{{ kb.logo_primary.s3_url }}" alt="Logo da empresa" class="company-logo">
        {% else %}
            <div class="company-logo-placeholder">
                <span>{{ kb.organization.name|slice:":1" }}</span>
            </div>
        {% endif %}
    </div>
    
    <div class="perfil-header-content">
        <h1>Perfil da Empresa</h1>
        <p class="subtitle">Base de conhecimento consolidada!</p>
        
        <p class="description">
            Reunimos e organizamos todas as suas informações. Agora você pode 
            navegar pelos blocos com tranquilidade. Se quiser ajustar algo, clique 
            em "Editar conteúdo" ao final da página — quando quiser, sem pressa.
        </p>
        
        <p class="description">
            Pronto para avançar? O AIMKT já está liberado para gerar conteúdo a 
            partir desta base.
        </p>
    </div>
</div>
```

---

#### **3.4.3 Linha 1: Base + Presença Digital**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha1.html`

```django
<div class="perfil-viz-grid-2">
    <!-- Coluna 1: Base Consolidada -->
    <div class="perfil-viz-card">
        <div class="card-header">
            <span class="card-tag">IDENTIDADE INSTITUCIONAL</span>
            <h3>Sua base (consolidada pelo agente)</h3>
        </div>
        
        <div class="card-body">
            <div class="content-section">
                <h4>Identidade / Essência</h4>
                <p>{{ compilation_data.areas.base.identity_essence }}</p>
            </div>
            
            <div class="content-section">
                <h4>Público-alvo</h4>
                <p>{{ compilation_data.areas.base.audience }}</p>
            </div>
            
            <div class="content-section">
                <h4>Estratégia & Canais</h4>
                <p>{{ compilation_data.areas.base.strategy_channels }}</p>
            </div>
            
            <div class="content-section">
                <h4>Mensagens-chave</h4>
                <ul class="key-messages-list">
                    {% for message in compilation_data.areas.base.key_messages %}
                        <li>{{ message }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
    
    <!-- Coluna 2: Presença Digital -->
    <div class="perfil-viz-card">
        <div class="card-header">
            <span class="card-tag">SITE • REDES • CONCORRENTES</span>
            <h3>Presença Digital</h3>
        </div>
        
        <div class="card-body">
            <div class="content-section">
                <h4>Redes sociais</h4>
                <ul class="social-list">
                    {% for social in compilation_data.areas.digital_presence.social_networks %}
                        <li>
                            <strong>{{ social.network|upper }}</strong>
                        </li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="content-section">
                <h4>Site</h4>
                <p>
                    <a href="{{ compilation_data.areas.digital_presence.website_url }}" target="_blank">
                        {{ compilation_data.areas.digital_presence.website_url }}
                    </a>
                </p>
            </div>
            
            <div class="content-section">
                <h4>Concorrentes</h4>
                <ul class="competitors-list">
                    {% for competitor in compilation_data.areas.digital_presence.competitors %}
                        <li>
                            <a href="{{ competitor }}" target="_blank">{{ competitor }}</a>
                        </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</div>
```

---

#### **3.4.4 Linha 2: Identidade Visual**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha2.html`

```django
<div class="perfil-viz-card perfil-viz-visual-identity">
    <div class="card-header">
        <span class="card-tag">PALETA • LOGOTIPO • REFERÊNCIAS</span>
        <h3>Identidade Visual</h3>
    </div>
    
    <div class="card-body">
        <div class="perfil-viz-grid-2">
            <!-- Coluna 1: Paleta + Tipografias -->
            <div>
                <!-- Paleta de Cores -->
                <div class="content-section">
                    <h4>Paleta de cores</h4>
                    <div class="color-palette-horizontal">
                        {% for hex in compilation_data.areas.visual_identity.palette_hex %}
                            <div class="color-item-viz">
                                <div class="color-circle" style="background-color: {{ hex }};"></div>
                                <span class="color-hex">{{ hex }}</span>
                            </div>
                        {% endfor %}
                    </div>
                </div>
                
                <!-- Tipografias -->
                <div class="content-section">
                    <h4>Tipografias (fontes)</h4>
                    <div class="typography-list">
                        {% for typo in typography %}
                            <div class="typography-item-viz">
                                <span class="typography-icon">▸</span>
                                <span class="typography-text">
                                    Fonte #{{ forloop.counter }} - {{ typo.font_name }} - {{ typo.get_usage_display }}
                                </span>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Coluna 2: Logotipos + Referências -->
            <div>
                <!-- Logotipos -->
                <div class="content-section">
                    <h4>Logotipos</h4>
                    <div class="logos-grid-viz">
                        {% for logo in logos %}
                            <div class="logo-item-viz">
                                <img src="{{ logo.s3_url }}" alt="{{ logo.name }}" loading="lazy">
                            </div>
                        {% endfor %}
                    </div>
                </div>
                
                <!-- Imagens de Referência -->
                <div class="content-section">
                    <h4>Imagens de referência</h4>
                    <div class="references-grid-viz">
                        {% for ref in references %}
                            <div class="reference-item-viz">
                                <img data-lazy-load="{{ ref.s3_key }}" alt="{{ ref.name }}" loading="lazy">
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

#### **3.4.5 Linha 3: Avaliação + Melhorias**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha3.html`

```django
<div class="perfil-viz-grid-2">
    <!-- Coluna 1: Avaliação -->
    <div class="perfil-viz-card">
        <div class="card-header">
            <h3>Avaliação</h3>
        </div>
        
        <div class="card-body">
            <div class="content-section">
                <h4>base:</h4>
                <p>{{ compilation_data.assessment_summary.base }}</p>
            </div>
            
            <div class="content-section">
                <h4>digital_presence:</h4>
                <p>{{ compilation_data.assessment_summary.digital_presence }}</p>
            </div>
            
            <div class="content-section">
                <h4>visual_identity:</h4>
                <p>{{ compilation_data.assessment_summary.visual_identity }}</p>
            </div>
        </div>
    </div>
    
    <!-- Coluna 2: Melhorias Sugeridas -->
    <div class="perfil-viz-card">
        <div class="card-header">
            <h3>Melhorias sugeridas</h3>
        </div>
        
        <div class="card-body">
            <div class="content-section">
                <h4>base:</h4>
                <p>{{ compilation_data.improvements_summary.base }}</p>
            </div>
            
            <div class="content-section">
                <h4>digital_presence:</h4>
                <p>{{ compilation_data.improvements_summary.digital_presence }}</p>
            </div>
            
            <div class="content-section">
                <h4>visual_identity:</h4>
                <p>{{ compilation_data.improvements_summary.visual_identity }}</p>
            </div>
        </div>
    </div>
</div>
```

---

#### **3.4.6 Linha 4: Plano de Marketing**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha4.html`

```django
<div class="perfil-viz-card perfil-viz-marketing">
    <div class="card-header">
        <h3>Plano de Marketing (4 semanas)</h3>
    </div>
    
    <div class="card-body">
        <div class="marketing-table-wrapper">
            <table class="marketing-table">
                <thead>
                    <tr>
                        <th>Semana</th>
                        <th>Foco</th>
                        <th>Ações</th>
                        <th>Canais</th>
                        <th>Ideias</th>
                        <th>KPIs</th>
                        <th>Responsável</th>
                        <th>Cadência</th>
                    </tr>
                </thead>
                <tbody>
                    {% for week in compilation_data.marketing_plan_4w %}
                        <tr>
                            <td>{{ week.week }}</td>
                            <td>{{ week.focus }}</td>
                            <td>
                                <ul class="table-list">
                                    {% for action in week.actions %}
                                        <li>{{ action }}</li>
                                    {% endfor %}
                                </ul>
                            </td>
                            <td>
                                <ul class="table-list">
                                    {% for channel in week.channels %}
                                        <li>{{ channel }}</li>
                                    {% endfor %}
                                </ul>
                            </td>
                            <td>
                                <ul class="table-list">
                                    {% for idea in week.content_ideas %}
                                        <li>{{ idea }}</li>
                                    {% endfor %}
                                </ul>
                            </td>
                            <td>
                                <ul class="table-list">
                                    {% for kpi in week.kpis %}
                                        <li>{{ kpi }}</li>
                                    {% endfor %}
                                </ul>
                            </td>
                            <td>{{ week.owner }}</td>
                            <td>{{ week.cadence }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

---

#### **3.4.7 Linha 5: Lacunas Encontradas**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha5.html`

```django
<div class="perfil-viz-card">
    <div class="card-header">
        <h3>Lacunas encontradas</h3>
    </div>
    
    <div class="card-body">
        {% if compilation_data.gaps %}
            {% for gap_key, gap_value in compilation_data.gaps.items %}
                <div class="content-section gap-section">
                    <h4>{{ gap_key }}:</h4>
                    <p>{{ gap_value }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p class="text-muted">Nenhuma lacuna encontrada.</p>
        {% endif %}
    </div>
</div>
```

---

#### **3.4.8 Linha 6: Links Verificados**

**Arquivo:** `app/templates/knowledge/partials/perfil_viz_linha6.html`

```django
<div class="perfil-viz-card">
    <div class="card-header">
        <h3>Links verificados</h3>
    </div>
    
    <div class="card-body">
        {% if compilation_data.link_checks %}
            <div class="links-list">
                {% for link in compilation_data.link_checks %}
                    <div class="link-check-item">
                        <a href="{{ link.url }}" target="_blank" class="link-title">
                            {{ link.title }}
                        </a>
                        <span class="link-status link-status-{{ link.status_hint }}">
                            — {{ link.status_hint }} ({{ link.verification }})
                        </span>
                        <p class="link-summary">— {{ link.summary }}</p>
                        {% if link.notes %}
                            <p class="link-notes">{{ link.notes }}</p>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p class="text-muted">Nenhum link verificado.</p>
        {% endif %}
    </div>
</div>
```

---

## 🎨 PARTE 4: CSS

### **4.1 Arquivo Principal**

**Arquivo:** `app/static/css/perfil-visualizacao.css`

```css
/* ============================================
   PERFIL DA EMPRESA - MODO VISUALIZAÇÃO
   ============================================ */

.perfil-visualizacao-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

/* ============================================
   ESTADO: COMPILANDO
   ============================================ */

.perfil-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    padding: 3rem;
}

.perfil-empty-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
}

.perfil-empty-state h2 {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 1rem;
}

.perfil-empty-state p {
    font-size: 1rem;
    color: var(--color-text-secondary);
    margin-bottom: 0.5rem;
}

.perfil-empty-state .btn {
    margin-top: 2rem;
}

/* ============================================
   HEADER COM LOGO
   ============================================ */

.perfil-header {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 3rem;
    margin-bottom: 3rem;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.perfil-header-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 2rem;
}

.company-logo {
    max-width: 100%;
    max-height: 200px;
    object-fit: contain;
}

.company-logo-placeholder {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    font-weight: 700;
    color: white;
}

.perfil-header-content h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
}

.perfil-header-content .subtitle {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-primary);
    margin-bottom: 1.5rem;
}

.perfil-header-content .description {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--color-text-secondary);
    margin-bottom: 1rem;
}

/* ============================================
   SEÇÕES E CARDS
   ============================================ */

.perfil-viz-section {
    margin-bottom: 3rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
}

.section-subtitle {
    font-size: 0.95rem;
    color: var(--color-text-secondary);
    margin-bottom: 2rem;
}

.perfil-viz-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    padding: 2rem;
    margin-bottom: 1.5rem;
}

.perfil-viz-card .card-header {
    margin-bottom: 1.5rem;
}

.card-tag {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-text-tertiary);
    margin-bottom: 0.5rem;
}

.perfil-viz-card h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
}

.perfil-viz-card h4 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
}

.content-section {
    margin-bottom: 1.5rem;
}

.content-section:last-child {
    margin-bottom: 0;
}

.content-section p {
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--color-text-secondary);
}

/* ============================================
   GRIDS
   ============================================ */

.perfil-viz-grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}

/* ============================================
   LISTAS
   ============================================ */

.key-messages-list,
.social-list,
.competitors-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.key-messages-list li,
.social-list li,
.competitors-list li {
    padding: 0.5rem 0;
    padding-left: 1.5rem;
    position: relative;
    font-size: 0.95rem;
    color: var(--color-text-secondary);
}

.key-messages-list li::before {
    content: "•";
    position: absolute;
    left: 0;
    color: var(--color-primary);
    font-weight: 700;
}

/* ============================================
   PALETA DE CORES
   ============================================ */

.color-palette-horizontal {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.color-item-viz {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.color-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.color-hex {
    font-size: 0.75rem;
    font-family: 'Courier New', monospace;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
}

/* ============================================
   TIPOGRAFIAS
   ============================================ */

.typography-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.typography-item-viz {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.typography-icon {
    color: var(--color-primary);
    font-weight: 700;
}

.typography-text {
    font-size: 0.95rem;
    color: var(--color-text-secondary);
}

/* ============================================
   LOGOTIPOS E REFERÊNCIAS
   ============================================ */

.logos-grid-viz,
.references-grid-viz {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 1rem;
}

.logo-item-viz,
.reference-item-viz {
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    background: #f8f9fa;
    border: 1px solid rgba(0, 0, 0, 0.05);
}

.logo-item-viz img,
.reference-item-viz img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 0.5rem;
}

.reference-item-viz img {
    object-fit: cover;
    padding: 0;
}

/* ============================================
   TABELA DE MARKETING
   ============================================ */

.marketing-table-wrapper {
    overflow-x: auto;
}

.marketing-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.marketing-table th,
.marketing-table td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid #e9ecef;
}

.marketing-table th {
    font-weight: 600;
    color: var(--color-text-primary);
    background: #f8f9fa;
}

.marketing-table td {
    color: var(--color-text-secondary);
}

.table-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.table-list li {
    padding: 0.25rem 0;
}

/* ============================================
   LACUNAS E LINKS
   ============================================ */

.gap-section {
    padding: 1rem;
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    border-radius: 4px;
}

.links-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.link-check-item {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 6px;
}

.link-title {
    font-weight: 600;
    color: var(--color-primary);
    text-decoration: none;
}

.link-title:hover {
    text-decoration: underline;
}

.link-status {
    font-size: 0.875rem;
    margin-left: 0.5rem;
}

.link-status-ok {
    color: #28a745;
}

.link-status-invalid_format {
    color: #dc3545;
}

.link-summary,
.link-notes {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-top: 0.5rem;
}

/* ============================================
   AÇÕES
   ============================================ */

.perfil-viz-actions {
    display: flex;
    justify-content: center;
    padding: 2rem 0;
}

/* ============================================
   RESPONSIVO
   ============================================ */

@media (max-width: 768px) {
    .perfil-header {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
    
    .perfil-viz-grid-2 {
        grid-template-columns: 1fr;
    }
    
    .marketing-table {
        font-size: 0.75rem;
    }
    
    .marketing-table th,
    .marketing-table td {
        padding: 0.5rem;
    }
}
```

---

## 📜 PARTE 5: JAVASCRIPT

### **5.1 Arquivo Principal**

**Arquivo:** `app/static/js/perfil-visualizacao.js`

```javascript
/**
 * Perfil da Empresa - Modo Visualização
 * Gerencia lazy loading de imagens e interações
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Perfil Visualização carregado');
    
    // Inicializar lazy loading de imagens
    initLazyLoadImages();
});

/**
 * Inicializa lazy loading para imagens de referência
 */
function initLazyLoadImages() {
    const lazyImages = document.querySelectorAll('[data-lazy-load]');
    
    if (lazyImages.length === 0) return;
    
    // Reutilizar ImagePreviewLoader existente
    if (window.ImagePreviewLoader) {
        lazyImages.forEach(img => {
            const s3Key = img.getAttribute('data-lazy-load');
            if (s3Key) {
                window.ImagePreviewLoader.loadImage(s3Key, img);
            }
        });
    } else {
        console.warn('ImagePreviewLoader não encontrado');
    }
}
```

---

## 📊 PARTE 6: CHECKLIST DE IMPLEMENTAÇÃO

### **Fase 1: Backend - Envio N8N**
- [ ] Adicionar variáveis de ambiente (`.env.development` e `.env.example`)
- [ ] Criar migração para novos campos (`compilation_status`, etc)
- [ ] Adicionar método `send_for_compilation` em `N8NService`
- [ ] Modificar `perfil_apply_suggestions` para enviar ao N8N
- [ ] Modificar JavaScript `perfil.js` para redirecionar

### **Fase 2: Backend - Recebimento N8N**
- [ ] Criar endpoint `n8n_compilation_webhook` em `views_n8n.py`
- [ ] Adicionar rota `/webhook/compilation/` em `urls.py`
- [ ] Testar webhook com curl

### **Fase 3: View de Visualização**
- [ ] Criar view `perfil_visualizacao_view` em `views.py`
- [ ] Adicionar rota `/perfil-visualizacao/` em `urls.py`
- [ ] Criar template principal `perfil_visualizacao.html`

### **Fase 4: Templates Partials**
- [ ] Criar `perfil_compilando.html`
- [ ] Criar `perfil_viz_header.html`
- [ ] Criar `perfil_viz_linha1.html`
- [ ] Criar `perfil_viz_linha2.html`
- [ ] Criar `perfil_viz_linha3.html`
- [ ] Criar `perfil_viz_linha4.html`
- [ ] Criar `perfil_viz_linha5.html`
- [ ] Criar `perfil_viz_linha6.html`

### **Fase 5: CSS e JavaScript**
- [ ] Criar `perfil-visualizacao.css`
- [ ] Criar `perfil-visualizacao.js`
- [ ] Testar responsividade

### **Fase 6: Testes**
- [ ] Testar fluxo SEMSUGEST
- [ ] Testar fluxo COMSUGEST
- [ ] Testar estado "Compilando"
- [ ] Testar estado "Compilado"
- [ ] Testar lazy loading de imagens
- [ ] Testar botão "Editar Base"

---

## 🔄 PARTE 7: FLUXO COMPLETO (RESUMO)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO CLICA "APLICAR SUGESTÕES" (Modo Edição)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BACKEND: Salvar dados no banco                          │
│    - Campos editados                                        │
│    - Sugestões aceitas                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND: Marcar suggestions_reviewed = True              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKEND: Decidir fluxo N8N                               │
│    - SEMSUGEST: nenhuma sugestão aceita                     │
│    - COMSUGEST: pelo menos 1 aceita                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BACKEND: Enviar para N8N                                 │
│    - Payload: mesmo da Base de Conhecimento                 │
│    - Endpoint: variável de ambiente                         │
│    - Status: compilation_status = 'processing'              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. FRONTEND: Redirecionar para /perfil-visualizacao/       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. PÁGINA: Exibir estado "Compilando"                      │
│    - Ícone ⏳                                                │
│    - Mensagem: "Sua base está sendo compilada..."           │
│    - Botão: "Verificar Status" (reload)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. N8N: Processar dados e retornar                          │
│    - Webhook: /knowledge/webhook/compilation/               │
│    - Salvar em: n8n_compilation (JSONField)                 │
│    - Status: compilation_status = 'completed'               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. USUÁRIO: Clicar "Verificar Status"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. PÁGINA: Exibir conteúdo completo                        │
│     - Header com logo                                       │
│     - Resumo da Base (6 linhas)                             │
│     - Botão "Editar Base de Conhecimento"                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 OBSERVAÇÕES IMPORTANTES

1. **Reutilização de Código:**
   - Payload N8N: usar `_build_knowledge_base_payload` existente
   - Estado "Compilando": usar mesmo modelo do estado "Processando"
   - Lazy loading: usar `ImagePreviewLoader` existente
   - Segurança webhook: usar mesmas camadas do webhook de análise

2. **Endpoints N8N:**
   - NUNCA hardcoded
   - SEMPRE em variáveis de ambiente
   - Validar presença no settings.py

3. **Campos do Modelo:**
   - `suggestions_reviewed`: marcar True após enviar ao N8N
   - `compilation_status`: novo campo (não reutilizar `analysis_status`)
   - `n8n_compilation`: JSONField para armazenar retorno

4. **Layout:**
   - Estrutura das imagens de referência
   - Cores e estilos da aplicação
   - Nenhum campo editável
   - Botão "Editar Base" no final

5. **Tipografias:**
   - Usar mesma estrutura da Base de Conhecimento
   - Formato: "Fonte #1 - Nome da Fonte - Uso"
   - Ícone ▸ antes de cada item

---

**FIM DO PLANEJAMENTO**
