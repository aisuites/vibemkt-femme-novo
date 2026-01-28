# 📋 PLANEJAMENTO: Página "Perfil da Empresa" com Integração N8N

**Data de Criação:** 28 de Janeiro de 2026  
**Última Atualização:** 28 de Janeiro de 2026 - 16:39  
**Status:** Em Desenvolvimento

---

## 🎯 OBJETIVO GERAL

Implementar página "Perfil da Empresa" que:
1. Coleta dados da empresa durante onboarding
2. Envia dados para N8N para análise
3. Recebe análise com avaliações e sugestões por campo
4. Permite usuário aceitar/rejeitar sugestões
5. Gera compilação final com plano de marketing
6. Exibe resultado em modo visualização

---

## 👤 FLUXO DO USUÁRIO COMPLETO

### **1. CADASTRO E ONBOARDING**

#### **1.1 Cadastro Inicial**
- Usuário acessa `/signup`
- Preenche: nome, email, senha, organização
- Sistema cria conta e redireciona para dashboard

#### **1.2 Modal de Onboarding (Primeira Vez)**
- Ao acessar dashboard pela primeira vez
- Modal aparece automaticamente (`onboarding_completed = False`)
- Título: "Bem-vindo! Vamos começar?"
- Botão: "Iniciar Onboarding"
- Link: "Pular por enquanto"

#### **1.3 Fluxo de Onboarding**
- **Passo 1:** Informações básicas da empresa
  - Nome da empresa
  - Missão, visão, valores
  - Descrição do produto/serviço
  
- **Passo 2:** Público e segmentos
  - Público externo
  - Público interno
  - Segmentos internos (opcional)

- **Passo 3:** Posicionamento
  - Posicionamento de mercado
  - Diferenciais competitivos
  - Proposta de valor

- **Passo 4:** Tom de voz
  - Tom de voz externo
  - Tom de voz interno
  - Palavras recomendadas
  - Palavras a evitar

- **Passo 5:** Identidade visual
  - Cores da marca (hex + nome)
  - Tipografia (Google Fonts ou upload)
  - Logos (upload)

- **Passo 6:** Redes e concorrência
  - Site institucional
  - Redes sociais (Instagram, Facebook, LinkedIn, YouTube)
  - Concorrentes (nome + URL)
  - Templates de redes sociais

- **Passo 7:** Dados e insights
  - Fontes confiáveis (URLs)
  - Canais de trends
  - Palavras-chave para trends

#### **1.4 Finalização do Onboarding**
- Ao completar todos os passos
- Sistema marca `onboarding_completed = True`
- Redireciona para dashboard
- Modal não aparece mais automaticamente

---

### **2. PÁGINA "PERFIL DA EMPRESA"**

#### **2.1 Acesso**
- Menu sidebar: "Perfil da Empresa"
- URL: `/knowledge/perfil/`
- Badge de status no menu (opcional)

#### **2.2 Estados da Página**

##### **ESTADO 1: Dados Incompletos**
- Exibir mensagem: "Complete seu perfil para solicitar análise"
- Botão: "Completar Perfil" → Redireciona para `/knowledge/view/`
- Mostrar % de completude

##### **ESTADO 2: Pronto para Análise**
- Exibir resumo dos dados preenchidos
- Botão: "Solicitar Análise N8N"
- Ao clicar:
  - Envia dados para N8N
  - Status muda para 'processing'
  - Redireciona para ESTADO 3

##### **ESTADO 3: Processando Análise**
- Loading state com animação
- Mensagem: "Analisando seus dados... Isso pode levar alguns minutos."
- Polling a cada 10 segundos para verificar status
- Quando N8N retorna análise → ESTADO 4

##### **ESTADO 4: Modo Edição (Análise Recebida)**
- Exibir análise por campo:
  - Campo: "Missão"
  - Informado pelo usuário: [texto]
  - Avaliação: "Fraco" (badge vermelho)
  - Sugestão: [texto sugerido]
  - Checkbox: "Aceitar sugestão"
  
- Resumo geral:
  - X campos fracos
  - Y campos médios
  - Z campos bons
  
- Botão: "Aplicar Sugestões Selecionadas"
- Ao clicar:
  - Atualiza campos da KB com sugestões aceitas
  - Solicita compilação ao N8N
  - Status muda para 'compiling'
  - Redireciona para ESTADO 5

##### **ESTADO 5: Processando Compilação**
- Loading state com animação
- Mensagem: "Gerando seu plano de marketing... Quase lá!"
- Polling a cada 10 segundos
- Quando N8N retorna compilação → ESTADO 6

##### **ESTADO 6: Modo Visualização (Compilação Recebida)**
- **Seção 1: Plano de Marketing**
  - Texto completo do plano gerado
  - Formatação markdown
  
- **Seção 2: Avaliações por Campo**
  - Lista de campos com status
  - Filtros: Todos / Fracos / Médios / Bons
  
- **Seção 3: Resumos**
  - Resumo geral da empresa
  - Pontos fortes
  - Pontos de melhoria
  
- Botões:
  - "Editar Perfil" → Volta para `/knowledge/view/`
  - "Solicitar Nova Análise" → Volta para ESTADO 2

---

## 📊 ESTRUTURA DE DADOS

### **Campos do Modelo KnowledgeBase**

#### **Campos Existentes (Bloco 1-7)**
```python
# Bloco 1: Identidade Institucional
nome_empresa = CharField
missao = TextField
visao = TextField
valores = TextField
descricao_produto = TextField  # Renomeado de 'historia'

# Bloco 2: Público e Segmentos
publico_externo = TextField
publico_interno = TextField
# Segmentos: InternalSegment (model separado)

# Bloco 3: Posicionamento e Diferenciais
posicionamento = TextField
diferenciais = TextField
proposta_valor = TextField

# Bloco 4: Tom de Voz e Linguagem
tom_voz_externo = TextField
tom_voz_interno = TextField
palavras_recomendadas = TextField
palavras_evitar = TextField

# Bloco 5: Identidade Visual
# Cores: ColorPalette (model separado)
# Fontes: Typography (model separado)
# Logos: Logo (model separado)
# Imagens: ReferenceImage (model separado)

# Bloco 6: Sites e Redes Sociais
site_institucional = URLField
concorrentes = JSONField  # [{"nome": "X", "url": "..."}]
# Redes sociais: SocialNetwork (model separado)
# Templates: SocialNetworkTemplate (model separado)

# Bloco 7: Dados e Insights
fontes_confiaveis = JSONField  # ["url1", "url2"]
canais_trends = JSONField  # ["canal1", "canal2"]
palavras_chave_trends = JSONField  # ["palavra1", "palavra2"]
```

#### **Campos de Análise N8N (Novos)**
```python
# Primeira Análise (campo por campo)
n8n_analysis = JSONField(default=dict, blank=True)
# Estrutura:
{
  "missao": {
    "informado_pelo_usuario": "texto original",
    "avaliacao": "fraco",  # fraco/médio/bom
    "status": "fraco",
    "sugestao": "texto sugerido"
  },
  "visao": { ... },
  ...
}

# Compilação Final
n8n_compilation = JSONField(default=dict, blank=True)
# Estrutura:
{
  "plano_marketing": "texto completo do plano",
  "avaliacoes": {
    "campo1": "avaliação detalhada",
    ...
  },
  "resumos": {
    "resumo_geral": "texto",
    "pontos_fortes": ["ponto1", "ponto2"],
    "pontos_melhoria": ["ponto1", "ponto2"]
  }
}

# Decisões do Usuário
accepted_suggestions = JSONField(default=dict, blank=True)
# Estrutura:
{
  "missao": true,  # aceitou sugestão
  "visao": false,  # rejeitou sugestão
  ...
}

# Status e Metadados
analysis_status = CharField(
  choices=[
    ('pending', 'Pendente'),
    ('processing', 'Processando Análise'),
    ('completed', 'Análise Completa'),
    ('compiling', 'Gerando Compilação'),
    ('compiled', 'Compilação Completa'),
    ('error', 'Erro')
  ],
  default='pending'
)

analysis_revision_id = CharField(blank=True)  # ID da revisão N8N
analysis_requested_at = DateTimeField(null=True)
analysis_completed_at = DateTimeField(null=True)
compilation_requested_at = DateTimeField(null=True)
compilation_completed_at = DateTimeField(null=True)
```

---

## 🔄 INTEGRAÇÃO N8N

### **Fluxo de Comunicação**

```
┌─────────────────┐
│  Django (IAMKT) │
└────────┬────────┘
         │
         │ 1. POST /n8n/analyze
         │    Payload: dados da KB
         ▼
┌─────────────────┐
│   N8N Workflow  │
│   (Análise)     │
└────────┬────────┘
         │
         │ 2. Processa dados
         │    Avalia cada campo
         │    Gera sugestões
         │
         │ 3. POST /knowledge/webhook/analysis/
         │    Payload: análises + revision_id
         ▼
┌─────────────────┐
│  Django (IAMKT) │
│  Armazena       │
│  n8n_analysis   │
└────────┬────────┘
         │
         │ 4. Usuário aceita sugestões
         │
         │ 5. POST /n8n/compile
         │    Payload: dados atualizados
         ▼
┌─────────────────┐
│   N8N Workflow  │
│   (Compilação)  │
└────────┬────────┘
         │
         │ 6. Gera plano de marketing
         │    Cria resumos e avaliações
         │
         │ 7. POST /knowledge/webhook/compilation/
         │    Payload: compilação completa
         ▼
┌─────────────────┐
│  Django (IAMKT) │
│  Armazena       │
│  n8n_compilation│
└─────────────────┘
```

### **Endpoints Django**

#### **1. Solicitar Análise**
```
POST /knowledge/perfil/request-analysis/
```

**Request:**
```json
{
  "organization_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "Análise solicitada com sucesso",
  "revision_id": "rev_abc123",
  "status": "processing"
}
```

**Ação:**
- Monta payload com todos os campos da KB
- Envia para N8N via POST
- Atualiza `analysis_status` para 'processing'
- Salva `analysis_revision_id`
- Registra `analysis_requested_at`

---

#### **2. Webhook - Receber Análise**
```
POST /knowledge/webhook/analysis/
```

**Request (do N8N):**
```json
{
  "revision_id": "rev_abc123",
  "organization_id": 123,
  "analysis": {
    "missao": {
      "informado_pelo_usuario": "Texto original",
      "avaliacao": "fraco",
      "status": "fraco",
      "sugestao": "Texto sugerido melhorado"
    },
    "visao": { ... },
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Análise recebida e armazenada"
}
```

**Ação:**
- Valida `revision_id`
- Armazena em `n8n_analysis`
- Atualiza `analysis_status` para 'completed'
- Registra `analysis_completed_at`

---

#### **3. Aplicar Sugestões**
```
POST /knowledge/perfil/apply-suggestions/
```

**Request:**
```json
{
  "accepted_suggestions": {
    "missao": true,
    "visao": false,
    "valores": true,
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "3 sugestões aplicadas com sucesso",
  "applied_count": 3
}
```

**Ação:**
- Atualiza campos da KB com sugestões aceitas
- Salva `accepted_suggestions`
- Solicita compilação ao N8N
- Atualiza `analysis_status` para 'compiling'

---

#### **4. Solicitar Compilação**
```
POST /knowledge/perfil/request-compilation/
```

**Request:**
```json
{
  "organization_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "Compilação solicitada",
  "status": "compiling"
}
```

**Ação:**
- Monta payload com dados atualizados
- Envia para N8N via POST
- Registra `compilation_requested_at`

---

#### **5. Webhook - Receber Compilação**
```
POST /knowledge/webhook/compilation/
```

**Request (do N8N):**
```json
{
  "revision_id": "rev_abc123",
  "organization_id": 123,
  "compilation": {
    "plano_marketing": "Texto completo do plano...",
    "avaliacoes": {
      "missao": "Avaliação detalhada da missão...",
      ...
    },
    "resumos": {
      "resumo_geral": "Resumo geral da empresa...",
      "pontos_fortes": ["Ponto 1", "Ponto 2"],
      "pontos_melhoria": ["Ponto 1", "Ponto 2"]
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Compilação recebida e armazenada"
}
```

**Ação:**
- Armazena em `n8n_compilation`
- Atualiza `analysis_status` para 'compiled'
- Registra `compilation_completed_at`

---

#### **6. Verificar Status**
```
GET /knowledge/perfil/status/
```

**Response:**
```json
{
  "status": "completed",
  "has_analysis": true,
  "has_compilation": false,
  "completude": 85,
  "can_request_analysis": false,
  "is_processing": false
}
```

---

## 📝 PLANEJAMENTO DETALHADO (11 FASES)

### **✅ FASE 1: PREPARAÇÃO DO MODELO** (COMPLETA)

**Objetivo:** Preparar modelo KnowledgeBase para receber dados de análise N8N

**Etapas:**
1. ✅ Migration renomear `historia` → `descricao_produto`
2. ✅ Migration adicionar campo `concorrentes`
3. ✅ Migration adicionar campos de análise N8N
4. ✅ Helper methods no modelo

**Arquivos modificados:**
- `apps/knowledge/models.py`
- `apps/knowledge/migrations/0012_*.py`
- `apps/knowledge/migrations/0013_*.py`
- `apps/knowledge/migrations/0014_*.py`

**Status:** ✅ COMPLETA

---

### **✅ FASE 2: UI - CAMPO CONCORRENTES** (COMPLETA)

**Objetivo:** Implementar interface para adicionar/remover concorrentes

**Etapas:**
1. ✅ Template atualizado com formulário
2. ✅ JavaScript `concorrentes.js` criado
3. ✅ View de salvamento atualizada
4. ✅ CSS responsivo adicionado

**Arquivos criados/modificados:**
- `templates/knowledge/view.html`
- `static/js/concorrentes.js`
- `static/css/knowledge.css`
- `apps/knowledge/views.py`

**Status:** ✅ COMPLETA

---

### **⏭️ FASE 3: INTEGRAÇÃO N8N - PRIMEIRO ENVIO** (PRÓXIMA)

**Objetivo:** Criar endpoint para enviar dados da KB para N8N

**Etapas:**
1. Criar view `request_analysis`
2. Montar payload com todos os campos
3. Enviar POST para N8N
4. Atualizar status para 'processing'
5. Retornar revision_id

**Arquivos a criar/modificar:**
- `apps/knowledge/views.py` (nova view)
- `apps/knowledge/urls.py` (nova rota)
- `apps/knowledge/services/n8n_service.py` (novo)

**Payload para N8N:**
```json
{
  "organization_id": 123,
  "organization_name": "Empresa X",
  "data": {
    "missao": "texto",
    "visao": "texto",
    "valores": "texto",
    "descricao_produto": "texto",
    "publico_externo": "texto",
    "publico_interno": "texto",
    "posicionamento": "texto",
    "diferenciais": "texto",
    "proposta_valor": "texto",
    "tom_voz_externo": "texto",
    "tom_voz_interno": "texto",
    "palavras_recomendadas": "texto",
    "palavras_evitar": "texto",
    "site_institucional": "url",
    "concorrentes": [...],
    "fontes_confiaveis": [...],
    "canais_trends": [...],
    "palavras_chave_trends": [...]
  }
}
```

**Testes:**
- [ ] Payload montado corretamente
- [ ] POST enviado para N8N
- [ ] Status atualizado
- [ ] revision_id salvo

---

### **FASE 4: WEBHOOK N8N - RECEBER PRIMEIRA ANÁLISE**

**Objetivo:** Criar endpoint webhook para receber análise do N8N

**Etapas:**
1. Criar view `webhook_analysis`
2. Validar revision_id
3. Processar payload do N8N
4. Armazenar em `n8n_analysis`
5. Atualizar status para 'completed'

**Arquivos a criar/modificar:**
- `apps/knowledge/views.py` (nova view)
- `apps/knowledge/urls.py` (nova rota)

**Testes:**
- [ ] Webhook recebe dados
- [ ] Validação de revision_id
- [ ] Dados armazenados corretamente
- [ ] Status atualizado

---

### **FASE 5: PÁGINA PERFIL - ESTADO PROCESSANDO**

**Objetivo:** Criar template com loading state durante análise

**Etapas:**
1. Criar template `perfil.html`
2. View `perfil_empresa`
3. JavaScript para polling de status
4. CSS para loading state

**Arquivos a criar:**
- `templates/knowledge/perfil.html`
- `static/js/perfil.js`
- `static/css/perfil.css`
- `apps/knowledge/views.py` (nova view)

**Testes:**
- [ ] Loading state exibido
- [ ] Polling funciona
- [ ] Transição para próximo estado

---

### **FASE 6: PÁGINA PERFIL - MODO EDIÇÃO**

**Objetivo:** Exibir análises e permitir aceitar/rejeitar sugestões

**Etapas:**
1. Template com lista de campos
2. Checkboxes para sugestões
3. Resumo geral (fracos/médios/bons)
4. Botão "Aplicar Sugestões"

**Arquivos a modificar:**
- `templates/knowledge/perfil.html`
- `static/js/perfil.js`
- `static/css/perfil.css`

**Testes:**
- [ ] Análises exibidas corretamente
- [ ] Checkboxes funcionam
- [ ] Resumo calculado
- [ ] Botão envia dados

---

### **FASE 7: PROCESSAR SUGESTÕES ACEITAS**

**Objetivo:** Aplicar sugestões aceitas e solicitar compilação

**Etapas:**
1. View `apply_suggestions`
2. Atualizar campos da KB
3. Salvar `accepted_suggestions`
4. Solicitar compilação ao N8N

**Arquivos a criar/modificar:**
- `apps/knowledge/views.py` (nova view)
- `apps/knowledge/urls.py` (nova rota)

**Testes:**
- [ ] Sugestões aplicadas
- [ ] Campos atualizados
- [ ] Compilação solicitada
- [ ] Status atualizado

---

### **FASE 8: WEBHOOK N8N - RECEBER COMPILAÇÃO**

**Objetivo:** Receber plano de marketing e resumos do N8N

**Etapas:**
1. View `webhook_compilation`
2. Processar payload
3. Armazenar em `n8n_compilation`
4. Atualizar status para 'compiled'

**Arquivos a criar/modificar:**
- `apps/knowledge/views.py` (nova view)
- `apps/knowledge/urls.py` (nova rota)

**Testes:**
- [ ] Webhook recebe dados
- [ ] Compilação armazenada
- [ ] Status atualizado

---

### **FASE 9: PÁGINA PERFIL - MODO VISUALIZAÇÃO**

**Objetivo:** Exibir plano de marketing e resultados finais

**Etapas:**
1. Template com plano de marketing
2. Seção de avaliações
3. Seção de resumos
4. Botões de ação

**Arquivos a modificar:**
- `templates/knowledge/perfil.html`
- `static/js/perfil.js`
- `static/css/perfil.css`

**Testes:**
- [ ] Plano exibido
- [ ] Avaliações listadas
- [ ] Resumos formatados
- [ ] Botões funcionam

---

### **FASE 10: ATUALIZAÇÃO DO SIDEBAR**

**Objetivo:** Adicionar badge de status no menu

**Etapas:**
1. Atualizar template do sidebar
2. Adicionar lógica de badge
3. CSS para badge

**Arquivos a modificar:**
- `templates/base/sidebar.html`
- `static/css/sidebar.css`

**Testes:**
- [ ] Badge aparece
- [ ] Cores corretas por status
- [ ] Link funciona

---

### **FASE 11: TESTES E AJUSTES**

**Objetivo:** Testar fluxo completo e ajustar UX

**Etapas:**
1. Teste completo do fluxo
2. Ajustes de UX
3. Tratamento de erros
4. Documentação

**Testes:**
- [ ] Fluxo completo funciona
- [ ] Erros tratados
- [ ] UX polida
- [ ] Documentação atualizada

---

## 🎓 DECISÕES TÉCNICAS

### **Por que JSONField para análises?**
- Flexibilidade para adicionar novos campos sem migrations
- N8N pode retornar estruturas variadas
- Facilita evolução do sistema

### **Por que estados claros (pending/processing/completed)?**
- Facilita renderização condicional de templates
- Permite rastreamento do progresso
- Simplifica lógica de polling

### **Por que separar análise e compilação?**
- Usuário pode revisar análise antes de gerar plano
- Permite aceitar/rejeitar sugestões
- Compilação só acontece com dados validados

### **Por que helper methods no modelo?**
- Encapsula lógica complexa
- Facilita uso em views e templates
- Código mais legível e manutenível

---

## 📈 PROGRESSO ATUAL

**Fases Completas:** 2/11 (18%)

- ✅ FASE 1: Preparação do Modelo
- ✅ FASE 2: UI Campo Concorrentes
- ⏭️ FASE 3: Integração N8N - Primeiro Envio (PRÓXIMA)
- ⏸️ FASE 4-11: Pendentes

---

## 🔗 REFERÊNCIAS

- Documento de sessão: `docs/SESSAO_2026-01-28.md`
- Melhores práticas: `docs/MELHORES_PRATICAS_PROJETO.md`
- Modelo: `apps/knowledge/models.py`
- Migrations: `apps/knowledge/migrations/`

---

**Documento mantido atualizado durante o desenvolvimento.**
