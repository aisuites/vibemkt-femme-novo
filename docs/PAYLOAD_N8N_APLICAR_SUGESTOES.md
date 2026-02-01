# PAYLOAD N8N - APLICAR SUGESTÕES

**Data:** 31/01/2026  
**Objetivo:** Documentar estrutura do payload que será enviado ao N8N ao clicar em "Aplicar Sugestões" e os campos que serão retornados.

---

## 📋 CONTEXTO

### **Fluxo Atual**
1. Usuário visualiza sugestões do agente IAMKT na página de Perfil
2. Cada campo tem botões "Aceitar" e "Rejeitar" (exceto campos readonly)
3. Ao clicar em "Aceitar", a sugestão deve ser aplicada ao campo
4. Sistema deve enviar payload ao N8N para processar a aplicação

### **Ponto de Rollback**
- **Commit:** `d3502c4`
- **Mensagem:** "feat: Refatoração campos Perfil - Site, Redes Sociais e Concorrentes com prefixo https:// fixo + correções de bugs"
- **Data:** 31/01/2026 21:08

---

## 🔄 ESTRUTURA DO PAYLOAD A SER ENVIADO

### **Endpoint N8N**
```
POST https://n8n.iamkt.com.br/webhook/apply-suggestion
```

### **Headers**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {token}"
}
```

### **Body do Payload**
```json
{
  "kb_id": 5,
  "organization_id": 9,
  "action": "apply_suggestion",
  "campo": "mission",
  "campo_label": "Missão",
  "valor_atual": "Promover a saúde integral da mulher...",
  "sugestao": "Nova sugestão do agente IAMKT",
  "timestamp": "2026-01-31T21:10:00Z",
  "user_id": 1,
  "user_email": "usuario@exemplo.com"
}
```

### **Campos do Payload**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `kb_id` | integer | Sim | ID da Base de Conhecimento |
| `organization_id` | integer | Sim | ID da Organização |
| `action` | string | Sim | Ação a ser executada (`apply_suggestion`) |
| `campo` | string | Sim | Nome do campo (ex: `mission`, `vision`, `values`) |
| `campo_label` | string | Não | Label do campo para logs (ex: "Missão", "Visão") |
| `valor_atual` | string/object | Sim | Valor atual do campo no banco de dados |
| `sugestao` | string/object | Sim | Sugestão do agente IAMKT a ser aplicada |
| `timestamp` | string | Sim | Timestamp ISO 8601 da ação |
| `user_id` | integer | Sim | ID do usuário que aplicou a sugestão |
| `user_email` | string | Não | Email do usuário para logs |

---

## 📥 ESTRUTURA DA RESPOSTA DO N8N

### **Resposta de Sucesso**
```json
{
  "status": "success",
  "message": "Sugestão aplicada com sucesso",
  "campo": "mission",
  "novo_valor": "Nova missão aplicada pelo agente",
  "metadata": {
    "processed_at": "2026-01-31T21:10:05Z",
    "processing_time_ms": 150
  }
}
```

### **Resposta de Erro**
```json
{
  "status": "error",
  "message": "Erro ao processar sugestão",
  "error_code": "VALIDATION_ERROR",
  "details": "Campo 'mission' não pode estar vazio",
  "campo": "mission"
}
```

### **Campos da Resposta**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `status` | string | Status da operação (`success` ou `error`) |
| `message` | string | Mensagem descritiva |
| `campo` | string | Nome do campo processado |
| `novo_valor` | string/object | Novo valor aplicado (apenas em sucesso) |
| `error_code` | string | Código do erro (apenas em erro) |
| `details` | string | Detalhes do erro (apenas em erro) |
| `metadata` | object | Metadados adicionais |

---

## 🎯 CAMPOS SUPORTADOS

### **Campos de Texto Simples**
- `mission` (Missão)
- `vision` (Visão)
- `values` (Valores)
- `description` (Descrição do Produto/Serviço)
- `target_audience` (Público Externo)
- `internal_audience` (Público Interno)
- `positioning` (Posicionamento)
- `value_proposition` (Proposta de Valor)
- `differentials` (Diferenciais)
- `tone_of_voice` (Tom de Voz)
- `internal_tone_of_voice` (Tom de Voz Interno)

### **Campos de Lista (Array)**
- `recommended_words` (Palavras Recomendadas)
- `words_to_avoid` (Palavras a Evitar)
- `internal_segments` (Segmentos Internos)

### **Campos Complexos (Relacionamentos)**
- `palette_colors` (Cores da Marca) - Relacionamento com `ColorPalette`
- `fonts` (Tipografia) - Relacionamento com `Typography` e `CustomFont`
- `logo_files` (Logotipos) - Relacionamento com `Logo`
- `reference_images` (Imagens de Referência) - Relacionamento com `ReferenceImage`
- `social_networks` (Redes Sociais) - Relacionamento com `SocialNetwork`
- `competitors` (Concorrentes) - JSONField

### **Campos Readonly (Não Aceitam Sugestões)**
- `palette_colors`
- `fonts`
- `logo_files`
- `reference_images`

---

## 🔧 TRATAMENTO ESPECIAL POR TIPO DE CAMPO

### **1. Campos de Texto Simples**
```json
{
  "campo": "mission",
  "valor_atual": "Missão antiga",
  "sugestao": "Nova missão sugerida"
}
```
**Ação:** Substituir valor diretamente no banco.

### **2. Campos de Lista**
```json
{
  "campo": "recommended_words",
  "valor_atual": ["palavra1", "palavra2"],
  "sugestao": ["palavra1", "palavra2", "palavra3", "palavra4"]
}
```
**Ação:** Substituir lista completa no banco.

### **3. Campos de URL (Site, Redes Sociais)**
```json
{
  "campo": "website_url",
  "valor_atual": "https://exemplo.com",
  "sugestao": "https://novosite.com"
}
```
**Ação:** Validar URL e salvar com prefixo `https://`.

### **4. Campos de Relacionamento**
```json
{
  "campo": "social_networks",
  "valor_atual": {
    "instagram": "https://instagram.com/antigo",
    "facebook": "https://facebook.com/antigo"
  },
  "sugestao": {
    "instagram": "https://instagram.com/novo",
    "facebook": "https://facebook.com/novo",
    "linkedin": "https://linkedin.com/company/novo"
  }
}
```
**Ação:** Atualizar/criar registros no modelo relacionado.

### **5. Concorrentes (JSONField)**
```json
{
  "campo": "competitors",
  "valor_atual": [
    {"nome": "Concorrente 1", "url": "https://site1.com"}
  ],
  "sugestao": [
    {"nome": "Concorrente 1", "url": "https://site1.com"},
    {"nome": "Concorrente 2", "url": "https://site2.com"}
  ]
}
```
**Ação:** Substituir JSON completo no campo `concorrentes`.

---

## 🚀 IMPLEMENTAÇÃO BACKEND

### **View Django**
```python
# app/apps/knowledge/views_perfil.py

@require_http_methods(["POST"])
@login_required
def apply_suggestion(request):
    """
    Aplica sugestão do agente IAMKT a um campo específico
    """
    try:
        data = json.loads(request.body)
        kb_id = data.get('kb_id')
        campo = data.get('campo')
        sugestao = data.get('sugestao')
        
        # Validações
        kb = KnowledgeBase.objects.get(id=kb_id, organization=request.user.organization)
        
        # Enviar ao N8N
        n8n_response = send_to_n8n_apply_suggestion(
            kb_id=kb_id,
            organization_id=kb.organization.id,
            campo=campo,
            valor_atual=getattr(kb, campo, None),
            sugestao=sugestao,
            user_id=request.user.id,
            user_email=request.user.email
        )
        
        # Processar resposta
        if n8n_response['status'] == 'success':
            # Aplicar novo valor ao campo
            apply_field_value(kb, campo, n8n_response['novo_valor'])
            kb.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sugestão aplicada com sucesso'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': n8n_response['message']
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

### **Função de Envio ao N8N**
```python
# app/apps/knowledge/services/n8n_service.py

def send_to_n8n_apply_suggestion(kb_id, organization_id, campo, valor_atual, sugestao, user_id, user_email):
    """
    Envia payload ao N8N para aplicar sugestão
    """
    payload = {
        'kb_id': kb_id,
        'organization_id': organization_id,
        'action': 'apply_suggestion',
        'campo': campo,
        'valor_atual': valor_atual,
        'sugestao': sugestao,
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'user_email': user_email
    }
    
    response = requests.post(
        settings.N8N_APPLY_SUGGESTION_WEBHOOK_URL,
        json=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.N8N_API_TOKEN}'
        },
        timeout=30
    )
    
    return response.json()
```

---

## 🎨 IMPLEMENTAÇÃO FRONTEND

### **JavaScript - Botão Aceitar**
```javascript
// app/static/js/perfil.js

function acceptSuggestion(campo, sugestao) {
    if (!confirm('Deseja aplicar esta sugestão?')) {
        return;
    }
    
    const payload = {
        kb_id: window.KB_ID,
        campo: campo,
        sugestao: sugestao
    };
    
    fetch('/knowledge/apply-suggestion/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccessMessage('Sugestão aplicada com sucesso!');
            // Recarregar página ou atualizar campo dinamicamente
            location.reload();
        } else {
            showErrorMessage(data.message);
        }
    })
    .catch(error => {
        showErrorMessage('Erro ao aplicar sugestão');
        console.error(error);
    });
}
```

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### **Prioridades**
1. Implementar campos de texto simples primeiro
2. Implementar campos de lista
3. Implementar campos de URL com validação
4. Implementar campos de relacionamento (mais complexo)

### **Validações Necessárias**
- ✅ Verificar se usuário tem permissão para editar KB
- ✅ Validar formato da sugestão conforme tipo do campo
- ✅ Validar URLs (adicionar https:// se necessário)
- ✅ Validar tamanho máximo dos campos
- ✅ Sanitizar entrada para evitar XSS

### **Logs e Auditoria**
- Registrar todas as aplicações de sugestões em `KnowledgeChangeLog`
- Incluir: campo, valor anterior, novo valor, usuário, timestamp
- Permitir rollback de sugestões aplicadas

### **Tratamento de Erros**
- Timeout do N8N (30s)
- Erro de validação
- Erro de permissão
- Erro de conexão
- Campo não encontrado

---

## 🧪 TESTES

### **Casos de Teste**
1. ✅ Aplicar sugestão em campo de texto simples
2. ✅ Aplicar sugestão em campo de lista
3. ✅ Aplicar sugestão em campo de URL
4. ✅ Aplicar sugestão em campo de relacionamento
5. ✅ Rejeitar sugestão (não enviar ao N8N)
6. ✅ Timeout do N8N
7. ✅ Erro de validação
8. ✅ Usuário sem permissão

---

## 🔐 SEGURANÇA

### **Autenticação**
- Token Bearer no header
- Validar token no N8N
- Expiração de token (1 hora)

### **Autorização**
- Verificar se usuário pertence à organização
- Verificar se usuário tem permissão de edição
- Validar KB_ID pertence à organização do usuário

### **Sanitização**
- Escapar HTML em campos de texto
- Validar formato de URLs
- Limitar tamanho de payloads (max 1MB)

---

**Status:** 📋 DOCUMENTAÇÃO COMPLETA - PRONTO PARA DESENVOLVIMENTO
