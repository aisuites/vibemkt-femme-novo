# 📊 ANÁLISE COMPLETA DA APLICAÇÃO IAMKT

**Data da Análise:** 11 de Fevereiro de 2026  
**Analista:** Cascade AI  
**Aplicação:** IAMKT - Plataforma de Marketing com IA  
**Localização:** /opt/iamkt

---

## 🏗️ **ARQUITETURA GERAL**

**Tipo:** Aplicação Django (Python) com frontend em HTML/CSS/JavaScript  
**Estrutura:** Monolito modular com apps Django separados  
**Deploy:** Docker + Docker Compose

---

## 📁 **ESTRUTURA DE ARQUIVOS**

### **Arquivos Analisados:**
- **47 arquivos HTML** (templates)
- **30 arquivos JavaScript** 
- **17 arquivos CSS**

### **Apps Django:**
- `core` - Funcionalidades centrais
- `knowledge` - Base de conhecimento
- `pautas` - Geração de pautas
- `posts` - Geração de posts com IA
- `campaigns` - Campanhas e projetos
- `content` - Gestão de conteúdo e trends
- `utils` - Utilitários

---

## 🎨 **PÁGINAS E FUNCIONALIDADES ATIVAS**

### **1. Autenticação** ✅ ATIVA
- **Login** (`/login/`) - `/opt/iamkt/app/templates/auth/login.html`
- **Registro** (`/register/`) - `/opt/iamkt/app/templates/auth/register.html`
- Toggle de visualização de senha
- Validação de formulários
- Máscara de telefone brasileiro

### **2. Dashboard** ✅ ATIVA
- **URL:** `/dashboard/`
- **Template:** `/opt/iamkt/app/templates/dashboard/dashboard.html`
- **Funcionalidades:**
  - Resumo de atividades (pautas, posts, projetos)
  - Estatísticas de Base de Conhecimento (completude %)
  - Quotas de uso (pautas/dia, posts/dia, posts/mês)
  - Trends em alta
  - Atividades recentes
  - Ações rápidas

### **3. Base de Conhecimento (Knowledge)** ✅ ATIVA
- **URL:** `/knowledge/view/` e `/knowledge/perfil/`
- **Templates:** 
  - `/opt/iamkt/app/templates/knowledge/perfil.html` (modo edição)
  - `/opt/iamkt/app/templates/knowledge/perfil_visualizacao.html` (modo visualização)
  - `/opt/iamkt/app/templates/knowledge/view.html`

**Estados do fluxo:**
1. **Pendente** - Base incompleta, redireciona para completar
2. **Processing** - Agente IA analisando dados
3. **Completed** - Modo edição com sugestões do agente
4. **Compiling** - Compilando alterações
5. **Compiled** - Visualização final

**Campos gerenciados:**
- Informações da empresa (nome, segmento, público-alvo)
- Identidade visual (cores, fontes, logos)
- Redes sociais (Instagram, Facebook, LinkedIn, YouTube)
- Website institucional
- Concorrentes
- Palavras recomendadas/evitadas
- Imagens de referência

**JavaScript:** `/opt/iamkt/app/static/js/knowledge.js` - Accordion colapsável com navegação por blocos

### **4. Pautas** ✅ ATIVA
- **URL:** `/pautas/`
- **Template:** `/opt/iamkt/app/templates/pautas/pautas_list.html`
- **JavaScript:** `/opt/iamkt/app/static/js/pautas.js`

**Funcionalidades:**
- **Gerar Pauta** - Modal com seleção de rede social e tema
- **Listar Pautas** - Grid com paginação
- **Editar Pauta** - Modo inline de edição
- **Excluir Pauta** - Com modal de confirmação
- **Gerar Post** - Redireciona para `/posts/` com dados pré-preenchidos
- **Filtros:** Data, busca por título
- **Paginação:** Navegação entre páginas

**Integração:** Envia dados para webhook (geração via IA)

### **5. Posts** ✅ ATIVA
- **URL:** `/posts/`
- **Template:** `/opt/iamkt/app/apps/posts/templates/posts/posts_list.html`
- **JavaScript:** `/opt/iamkt/app/static/js/posts.js` (2012 linhas - arquivo complexo)
- **CSS:** `/opt/iamkt/app/static/css/posts.css`, `posts-detail.css`

**Funcionalidades:**
- **Gerar Post** - Modal completo com:
  - Seleção de rede social (Instagram, Facebook, LinkedIn, WhatsApp)
  - Formato (Feed, Stories, Feed + Stories)
  - CTA (Sim/Não)
  - Carrossel (2-5 imagens)
  - Tema (3000 caracteres)
  - Upload de imagens de referência (máx 5)
  
- **Visualização 2 Colunas:**
  - **Esquerda:** Detalhes do post (título, subtítulo, legenda, hashtags, CTA, descrição da imagem)
  - **Direita:** Preview visual da imagem gerada
  
- **Estados do Post:**
  - `pending` - Pendente de aprovação
  - `generating` - Agente gerando conteúdo (texto)
  - `image_generating` - Agente gerando imagem
  - `image_ready` - Imagem disponível
  - `approved` - Aprovado
  - `rejected` - Rejeitado
  - `agent` - Agente alterando

- **Ações Dinâmicas:**
  - Aprovar/Rejeitar
  - Solicitar alteração de texto
  - Solicitar alteração de imagem
  - Editar post
  - Excluir post

- **Galeria de Carrossel:** Miniaturas clicáveis para posts com múltiplas imagens
- **Lazy Loading:** Imagens carregadas sob demanda via S3
- **Filtros:** Data, status, busca por título
- **Paginação:** 1 post por página

### **6. Campanhas/Projetos** ⚠️ PARCIALMENTE ATIVA
- **URL:** `/campaigns/projects/`
- **Template:** `/opt/iamkt/app/templates/campaigns/projects_list.html`
- Listagem básica de projetos
- Status: active, planning, archived
- **Nota:** Funcionalidade básica, sem CRUD completo

### **7. Trends** ⚠️ PARCIALMENTE ATIVA
- **URL:** `/content/trends/`
- **Template:** `/opt/iamkt/app/templates/content/trends_list.html`
- Monitoramento de trends com score de relevância
- Exibido no dashboard

---

## 🔧 **JAVASCRIPT - LÓGICAS E FUNÇÕES**

### **`main.js`** - Utilitários Globais
**Localização:** `/opt/iamkt/app/static/js/main.js`

**Funcionalidades:**
- Dropdown functionality
- FAQ Accordion
- Toast notifications (`showToast`)
- Form validation (`validateForm`)
- Loading states (`setLoading`)
- Copy to clipboard
- Namespace global: `window.VibeMKT`

### **`knowledge.js`** - Base de Conhecimento
**Localização:** `/opt/iamkt/app/static/js/knowledge.js`

**Funcionalidades:**
- Accordion colapsável por blocos
- Navegação por pills
- Scroll suave até seções
- Reabertura de blocos via sessionStorage

### **`perfil.js`** - Perfil da Empresa
**Localização:** `/opt/iamkt/app/static/js/perfil.js`

**Funcionalidades:**
- Gerenciamento de sugestões do agente IA
- Aceitar/Rejeitar sugestões
- Edição inline de campos
- Contador de alterações
- Envio para endpoint `/knowledge/perfil/apply-suggestions/`

**Integração com módulos especializados:**
- `perfil-tags.js` - Gerenciamento de tags
- `perfil-colors.js` - Paleta de cores
- `perfil-fonts.js` - Fontes tipográficas
- `perfil-logos.js` - Upload e gestão de logos
- `perfil-references.js` - Imagens de referência
- `perfil-social.js` - Redes sociais
- `perfil-competitors.js` - Concorrentes

### **`pautas.js`** - Geração de Pautas
**Localização:** `/opt/iamkt/app/static/js/pautas.js`

**Funcionalidades:**
- Submit do formulário de geração
- Edição inline (toggle entre visualização/edição)
- Exclusão com confirmação
- Integração com modal de confirmação
- Bloqueio de duplo clique
- Endpoint: `/pautas/gerar/`, `/pautas/editar/{id}/`, `/pautas/excluir/{id}/`

### **`posts.js`** - Sistema Completo de Posts
**Localização:** `/opt/iamkt/app/static/js/posts.js`  
**Tamanho:** 2012 linhas

**Principais funcionalidades:**
- Estado global da aplicação (`postsState`)
- Gerenciamento de modais (Gerar Post, Editar Post)
- Formulário complexo com validações
- Filtros e paginação
- Atualização dinâmica de UI
- Lazy loading de imagens via S3
- Sistema de status com banners informativos
- Cálculo de prazos (3 dias úteis para imagem)
- Normalização de hashtags
- Upload de múltiplas imagens de referência
- Integração com webhook para geração via IA

**Utilitários:**
- `postJSON()` - Requisições AJAX
- `escapeHtml()` - Sanitização
- `formatDateTime()` - Formatação de datas
- `calculateImageDeadline()` - Cálculo de prazos

### **Módulos de Suporte:**
- `logger.js` - Sistema de logging
- `toaster.js` - Notificações toast
- `confirm-modal.js` - Modal de confirmação
- `image-validator.js` - Validação de imagens
- `image-preview-loader.js` - Lazy loading de imagens
- `image-lazy-loading.js` - Carregamento otimizado
- `uploads-simple.js` - Upload para S3
- `utils.js` - Funções auxiliares
- `segments.js` - Gerenciamento de segmentos
- `tags.js` - Sistema de tags

---

## 🎨 **CSS - SISTEMA DE DESIGN**

### **`base.css`** - Design System
**Localização:** `/opt/iamkt/app/static/css/base.css`

**Variáveis CSS (Design Tokens):**
- **Cores primárias:** Purple (#7a3d8a, #9b59b6), Teal (#7ab2ca, #00bca4)
- **Cores semânticas:** primary, secondary, accent, success, warning, error
- **Tipografia:** Quicksand (Google Fonts)
- **Espaçamentos:** Sistema de 1-12 (0.25rem - 3rem)
- **Border radius:** sm (8px), md (12px), lg (18px), pill (999px)
- **Sombras:** soft, subtle, sm, md, lg, xl
- **Font sizes:** xs (10px) até 3xl (22px)

**Utilitários:**
- Progress bars (success, warning, danger)
- Card variants
- Text utilities
- Background utilities

### **`components.css`** - Componentes Reutilizáveis
**Localização:** `/opt/iamkt/app/static/css/components.css`

**Componentes:**
- Auth pages (login, register)
- Header e sidebar
- Cards e badges
- Botões (primary, secondary, outline, ghost)
- Formulários (inputs, selects, textareas)
- Modais
- Dropdowns
- Alerts e toasts
- Tabelas
- Paginação

### **CSS Especializados:**
- `knowledge.css` - Base de conhecimento
- `perfil.css` - Perfil da empresa
- `perfil-colors.css` - Seletor de cores
- `perfil-fonts.css` - Gerenciador de fontes
- `perfil-logos.css` - Upload de logos
- `perfil-visualizacao.css` - Modo visualização
- `posts.css` - Lista de posts
- `posts-detail.css` - Detalhes do post
- `confirm-modal.css` - Modal de confirmação
- `toaster.css` - Notificações
- `logo-upload-widget.css` - Widget de upload

---

## 🔌 **INTEGRAÇÕES E APIs**

### **1. Webhooks N8N** ✅
- **Geração de Pautas:** Endpoint configurado via `POSTS_WEBHOOK_URL`
- **Geração de Posts:** FormData com multipart/form-data
- **Campos enviados:**
  - rede, tema, usuario, formatos
  - carrossel, qtdImagens, ctaRequested
  - referencias (arquivos)

### **2. AWS S3** ✅
- **Upload de imagens:** Logos, referências, posts gerados
- **Preview de imagens:** Lazy loading via endpoint `/knowledge/preview-url/`
- **Validação:** Tipo, tamanho, dimensões

### **3. OpenAI / IA Generativa** ✅
- **Análise de Base de Conhecimento**
- **Geração de sugestões** para perfil da empresa
- **Geração de pautas** baseadas em trends
- **Geração de posts** (texto + imagem)
- **Alterações sob demanda** (revisões)

### **4. Sistema de Quotas** ✅
- **Pautas/dia:** Limite configurável
- **Posts/dia:** Limite configurável
- **Posts/mês:** Limite configurável
- **Custo/mês:** Tracking de custos (oculto na UI)

### **5. Email** ✅
**Templates de email:**
- `organization_approved.html`
- `organization_suspended.html`
- `organization_reactivated.html`
- `post_change_request.html`
- `post_image_request.html`
- `registration_confirmation.html`
- `registration_notification.html`

---

## 🔄 **FLUXOS DE TRABALHO**

### **Fluxo: Geração de Post**
1. Usuário clica "Gerar Post"
2. Preenche modal (rede, formato, tema, CTA, carrossel, refs)
3. Submit → Webhook N8N
4. Status: `generating` (banner: "Conteúdo será gerado em até 3 minutos")
5. Agente IA processa e retorna texto
6. Status: `image_generating` (banner: "Imagem será gerada até DD/MM/YYYY")
7. Agente IA gera imagem via DALL-E/Stable Diffusion
8. Status: `image_ready` → `pending`
9. Usuário aprova/rejeita ou solicita alterações
10. Status: `approved` (publicável)

### **Fluxo: Base de Conhecimento**
1. Usuário preenche formulário (6 blocos)
2. Solicita análise do agente
3. Status: `processing`
4. Agente IA analisa e retorna sugestões
5. Status: `completed` (modo edição)
6. Usuário aceita/rejeita sugestões
7. Submit → Endpoint `/knowledge/perfil/apply-suggestions/`
8. Status: `compiling`
9. N8N processa e compila base
10. Status: `compiled` (modo visualização)

---

## ⚠️ **FUNCIONALIDADES INATIVAS/INCOMPLETAS**

### **Módulo de Vídeos Avatar** ❌
- Mencionado no dashboard
- Sem implementação encontrada

### **Email Marketing** ❌
- Mencionado no dashboard
- Template básico existe mas sem CRUD

### **Aprovações** ⚠️
- Template `approvals_list.html` existe
- Funcionalidade parcial

### **Termos de Uso** ⚠️
- Template `legal/terms.html` existe
- Conteúdo não analisado

---

## 📊 **RESUMO EXECUTIVO**

**Status Geral:** Aplicação funcional com módulos principais ativos

**Módulos Ativos:**
- ✅ Autenticação
- ✅ Dashboard
- ✅ Base de Conhecimento (completo)
- ✅ Pautas (completo)
- ✅ Posts (completo)
- ⚠️ Campanhas (básico)
- ⚠️ Trends (básico)

**Integrações:**
- ✅ N8N Webhooks
- ✅ AWS S3
- ✅ OpenAI/IA
- ✅ Email
- ✅ Sistema de Quotas

**Tecnologias:**
- Backend: Django + Python
- Frontend: HTML5 + CSS3 + JavaScript (Vanilla)
- Banco: Não identificado (provavelmente PostgreSQL)
- Deploy: Docker + Docker Compose
- Storage: AWS S3
- Automação: N8N

---

## 📝 **OBSERVAÇÕES TÉCNICAS**

### **Pontos Fortes:**
1. **Arquitetura modular** bem organizada
2. **Sistema de design consistente** com design tokens
3. **Integração robusta** com IA generativa
4. **Lazy loading** otimizado para imagens
5. **Sistema de quotas** implementado
6. **Validações** em frontend e backend

### **Pontos de Melhoria:**
1. **posts.js muito grande** (2012 linhas) - recomenda-se modularizar
2. **Módulos desabilitados** (`posts-modal.js`, `posts-gallery.js`)
3. **Funcionalidades incompletas** (Email MKT, Vídeos Avatar)
4. **Documentação** poderia ser mais detalhada

---

## 🔍 **ARQUIVOS PRINCIPAIS**

### **Templates HTML (47 arquivos):**
- `/opt/iamkt/app/templates/base/base.html` - Template base
- `/opt/iamkt/app/templates/auth/login.html` - Login
- `/opt/iamkt/app/templates/auth/register.html` - Registro
- `/opt/iamkt/app/templates/dashboard/dashboard.html` - Dashboard
- `/opt/iamkt/app/templates/knowledge/perfil.html` - Perfil (edição)
- `/opt/iamkt/app/templates/knowledge/perfil_visualizacao.html` - Perfil (visualização)
- `/opt/iamkt/app/templates/pautas/pautas_list.html` - Lista de pautas
- `/opt/iamkt/app/apps/posts/templates/posts/posts_list.html` - Lista de posts
- `/opt/iamkt/app/templates/campaigns/projects_list.html` - Projetos
- `/opt/iamkt/app/templates/content/trends_list.html` - Trends

### **JavaScript (30 arquivos):**
- `/opt/iamkt/app/static/js/main.js` - Utilitários globais
- `/opt/iamkt/app/static/js/knowledge.js` - Base de conhecimento
- `/opt/iamkt/app/static/js/perfil.js` - Perfil da empresa
- `/opt/iamkt/app/static/js/pautas.js` - Pautas
- `/opt/iamkt/app/static/js/posts.js` - Posts (2012 linhas)
- `/opt/iamkt/app/static/js/logger.js` - Logging
- `/opt/iamkt/app/static/js/toaster.js` - Notificações
- `/opt/iamkt/app/static/js/confirm-modal.js` - Modal de confirmação
- `/opt/iamkt/app/static/js/image-validator.js` - Validação de imagens
- `/opt/iamkt/app/static/js/uploads-simple.js` - Upload S3

### **CSS (17 arquivos):**
- `/opt/iamkt/app/static/css/base.css` - Design system
- `/opt/iamkt/app/static/css/components.css` - Componentes
- `/opt/iamkt/app/static/css/knowledge.css` - Base de conhecimento
- `/opt/iamkt/app/static/css/perfil.css` - Perfil
- `/opt/iamkt/app/static/css/posts.css` - Posts
- `/opt/iamkt/app/static/css/posts-detail.css` - Detalhes do post

---

**Fim do Relatório**

---

**Gerado por:** Cascade AI  
**Data:** 11 de Fevereiro de 2026  
**Versão:** 1.0
