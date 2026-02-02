# 📊 ANÁLISE COMPLETA - resumo.html (Aplicação Antiga)

**Data:** 02/02/2026  
**Objetivo:** Mapear estrutura completa para adaptar à nova aplicação seguindo melhores práticas

---

## 🚨 PROBLEMAS IDENTIFICADOS (A CORRIGIR)

### **1. CSS INLINE (CRÍTICO) ❌**

**Total identificado:** ~30+ ocorrências de `style=""`

**Principais violações:**
```html
<!-- Linha 313 -->
<div style="display:grid; grid-template-columns:1fr 380px; gap:40px;">

<!-- Linha 315 -->
<div class="kicker" style="margin-bottom:12px">

<!-- Linha 316-318 -->
<h2 style="margin:0 0 16px; font-size:3.5rem; font-weight:900;">
<p style="margin:0 0 24px; font-size:1.15rem;">

<!-- Linha 325 -->
<div style="display:flex; gap:12px; margin-bottom:20px;">

<!-- Linha 329, 333 -->
<button style="--bgc:var(--accent-2)">
<button style="--bgc:#9333ea">

<!-- Linha 720, 827 -->
<div class="head" style="margin-bottom:4px">

<!-- Linha 751 -->
<span style="white-space: nowrap;">

<!-- Linha 807, 809 -->
<div class="input-file card pad" style="padding:.7rem">
<div class="subtitle" style="opacity:.8; margin-top:.35rem">

<!-- E muitos outros... -->
```

**SOLUÇÃO:** Criar classes CSS em arquivo separado `posts.css`

---

### **2. CSS NO BLOCO <style> (CRÍTICO) ❌**

**Localização:** Linhas 11-279 (268 linhas de CSS inline no HTML)

**Conteúdo:**
- Variáveis CSS (--bg, --card, --accent, etc)
- Estilos globais (body, a, container, etc)
- Componentes (modal, card, btn, chip, etc)
- Posts específicos (post-card, post-details, etc)
- Pautas (pauta-container, pauta-actions, etc)
- Paginação, filtros, formulários

**SOLUÇÃO:** Extrair TODO CSS para arquivo separado `posts.css`

---

### **3. JAVASCRIPT INLINE (CRÍTICO) ❌**

**Localização:** Linhas 890-3566 (2676 linhas de JS no HTML)

**Conteúdo:**
- Funções de modal (abrir/fechar)
- Lógica de posts (renderização, filtros, paginação)
- Lógica de pautas
- Lógica de vídeos avatar
- Upload de arquivos
- Contadores de caracteres
- Toggles e chips
- Fetch/AJAX

**SOLUÇÃO:** Mover TODO JavaScript para arquivo separado `posts.js`

---

### **4. HARDCODES IDENTIFICADOS ❌**

**Cores hardcoded:**
```css
--bg:#0f0f12;
--card:#16171b;
--accent:#7c4dff;  /* Deve ser #6366f1 na nossa app */
--accent-2:#00d2a8;
--success:#21c37a;
--warning:#ffb020;
--danger:#ff5d5d;
```

**URLs hardcoded:**
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display...">
```

**Valores hardcoded:**
```javascript
maxlength="3000"
maxlength="220"
maxlength="160"
max="5"  // limite de imagens
```

**SOLUÇÃO:** Usar variáveis de ambiente e settings.py

---

## 📋 ESTRUTURA MAPEADA

### **MODAL "GERAR POSTS" (Linhas 717-821)**

**Estrutura HTML:**
```
.modal#modalGerarPost
  .panel
    .head
      h3 "Gerar Posts"
      button.close "Fechar"
    
    form#formGerarPost.form
      <!-- LINHA 1: Rede Social | Formato -->
      .row.format-row
        div
          label "Rede social"
          select#redePost (Instagram, Facebook, LinkedIn, WhatsApp)
        
        div.format-col
          label "Formato"
          .format-controls
            .format-options#formatOptions (radiogroup)
              label.chip-choice.active
                input[type=radio][name=formatOption][value=feed][checked]
                span "Feed"
              label.chip-choice
                input[type=radio][name=formatOption][value=stories]
                span "Stories"
              label.chip-choice
                input[type=radio][name=formatOption][value=both]
                span "Feed + Stories"
      
      <!-- LINHA 2: CTA | Carrossel -->
      .row.format-row
        div
          label "Call to Action (CTA)"
          .cta-toggle-group
            label.cta-toggle-option.active
              input[type=radio][name=ctaOption][value=sim][checked]
              span "Sim"
            label.cta-toggle-option
              input[type=radio][name=ctaOption][value=nao]
              span "Não"
        
        div.carrossel-col
          .carrossel-controls
            .carrossel-item
              label "Carrossel"
              .chip-group
                button.chip#carrosselToggle "Ativar"
            
            .carrossel-item#carrosselQtyField[hidden]
              label "Qtd Imagens"
              .qty-control
                button[data-step=-1] "−"
                input#qtdImagens[type=number][min=2][max=5][value=3][readonly]
                button[data-step=1] "+"
      
      <!-- LINHA 3: Tema -->
      div
        .field-label
          label "Tema"
          span#temaContador "0/3000"
        textarea#temaPost[maxlength=3000][placeholder="Restrições, exemplos, referências..."][required]
      
      <!-- LINHA 4: Imagens de Referência -->
      div
        label "Imagens de Referência"
        .input-file.card.pad
          input#refImgs[type=file][accept=".jpg,.jpeg,.png"][multiple]
          .subtitle#refImgsInfo "Nenhum arquivo selecionado — Máx. 5 imagens (.JPG ou .PNG)"
      
      <!-- FOOTER -->
      .form-footer
        button.btn.ghost[data-close] "Cancelar"
        button.btn[type=submit] "Enviar ao agente"
```

---

### **BLOCO DE FILTROS (Linhas 393-406)**

**Estrutura HTML:**
```
.posts-toolbar#postsToolbar
  .field
    label "Data"
    input#filtroData[type=date]
  
  .field
    label "Status"
    select#filtroStatus
      option[value=""] "Todos"
      option[value="pending"] "Pendente"
      option[value="in_progress"] "Gerando"
      option[value="delivered"] "Entregue"
      option[value="approved"] "Aprovado"
      option[value="rejected"] "Rejeitado"
  
  .field.field-search
    label "Buscar por título"
    .search-box
      input#filtroBusca[type=text][placeholder="Buscar por título..."]
      button[type=button] (ícone de busca)
  
  button.btn.ghost#btnLimparFiltros "Limpar Filtros"
```

---

### **CARDS DE POST (Estados Diferentes)**

**Estado 1: GERANDO (in_progress)**
```
.post-card
  .post-details
    .status-pill.is-in_progress "Agente Gerando Conteúdo"
    .post-request (alerta verde)
      "Seu conteúdo será gerado em até 3 minutos"
      button "Atualizar Status"
    
    .post-tags
      .post-tag "Instagram"
      .post-tag "FEED"
    
    .post-section
      h4 "TÍTULO"
      p "—"
    
    .post-section
      h4 "SUBTÍTULO"
      p "—"
    
    (... outros campos vazios ...)
    
    .post-footer
      "Revisões restantes: 2"
      "Data da criação: 02/02/2026"
  
  .post-visual
    .post-image-frame
      .placeholder "SEM IMAGEM GERADA"
```

**Estado 2: PENDENTE APROVAÇÃO (delivered/pending)**
```
.post-card
  .post-details
    .status-pill.is-pending "Pendente de Aprovação"
    
    .post-tags
      .post-tag "Instagram"
    
    .post-section
      h4 "TÍTULO"
      p "Global Minds na Black Friday"
    
    .post-section
      h4 "SUBTÍTULO"
      p "Inovação em Estratégias de Marcas Globais"
    
    .post-section
      h4 "LEGENDA"
      p (texto completo)
    
    .post-section
      h4 "HASHES"
      p "#GlobalMinds #BlackFriday..."
    
    .post-section
      h4 "CTA"
      p "Transforme sua Black Friday com influenciadores!"
    
    .post-section
      h4 "DESCRIÇÃO DA IMAGEM A SER GERADA"
      p (descrição detalhada)
    
    .post-footer
      "Revisões restantes: 2"
      "Data da criação: 02/02/2026"
    
    .post-actions
      button.btn.ghost.danger "Rejeitar"
      button.btn.ghost "Solicitar Alteração"
      button.btn.ghost "Editar"
      button.btn "Gerar Imagem"
  
  .post-visual
    .post-image-frame
      .placeholder "SEM IMAGEM GERADA"
```

---

### **MODAL EDITAR POST (Linhas 677-715)**

**Estrutura HTML:**
```
.modal#modalEditarPost
  .panel
    .head
      h3 "Editar Post"
      button.close "Fechar"
    
    form#formEditarPost.form
      .form-grid
        label
          span "Título"
          input#editTitulo[maxlength=220][required]
        
        label
          span "Subtítulo"
          input#editSubtitulo[maxlength=220]
        
        label
          span "Legenda"
          textarea#editLegenda[rows=4]
        
        label
          span "Hashes"
          input#editHashes[maxlength=220]
        
        label
          span "CTA"
          input#editCTA[maxlength=160]
        
        label
          span "Descrição da imagem"
          textarea#editDescricaoImagem[rows=3]
      
      .form-footer
        button.btn.ghost[data-close] "Cancelar"
        button.btn[type=submit] "Salvar alterações"
```

---

## 🎨 CORES DA APLICAÇÃO ANTIGA vs NOVA

### **Aplicação Antiga:**
```css
--bg: #0f0f12        (fundo principal)
--card: #16171b      (cards)
--muted: #a9b0be     (texto secundário)
--text: #eef2f7      (texto principal)
--accent: #7c4dff    (roxo primário) ❌
--accent-2: #00d2a8  (verde/cyan)
--border: #24262c    (bordas)
--success: #21c37a   (verde sucesso)
--warning: #ffb020   (laranja aviso)
--danger: #ff5d5d    (vermelho erro)
```

### **Nossa Aplicação (Adaptar para):**
```css
--bg: #1f2937        (cinza escuro)
--accent: #6366f1    (roxo primário) ✅
--border: #374151    (cinza médio)
--muted: #9ca3af     (texto secundário)
--text: #fff         (branco)
--danger: #dc3545    (vermelho)
--success: #21c37a   (verde - manter)
```

---

## 📝 JAVASCRIPT - FUNÇÕES PRINCIPAIS

### **Modal Management:**
- `openModal(id)` - Abre modal
- `closeModal(id)` - Fecha modal
- `resetGerarPostForm()` - Reseta formulário
- `prefillPostModal(data)` - Preenche modal com dados

### **Contadores:**
- `updateTemaCounter()` - Atualiza contador 0/3000
- `updateRefsInfo()` - Atualiza info de arquivos

### **Toggles e Chips:**
- `setCarrossel(enabled)` - Ativa/desativa carrossel
- `syncFormatUI()` - Sincroniza UI de formato
- `selectedFormats()` - Retorna formatos selecionados

### **Posts:**
- `requestPostFromAgent(payload)` - Envia para backend
- `renderPosts()` - Renderiza lista de posts
- `applyPostFilters()` - Aplica filtros
- `renderPostPagination()` - Renderiza paginação

### **Upload:**
- Validação de 5 imagens máximo
- DataTransfer API para limitar arquivos

---

## 🎯 PLANO DE ADAPTAÇÃO

### **FASE 1: Extrair CSS**
1. Criar `/opt/iamkt/app/static/css/posts.css`
2. Mover TODO CSS do bloco `<style>` para arquivo
3. Adaptar cores para paleta da aplicação (#6366f1)
4. Criar classes para substituir TODOS os `style=""`
5. Remover variáveis CSS hardcoded

### **FASE 2: Extrair JavaScript**
1. Criar `/opt/iamkt/app/static/js/posts.js`
2. Mover TODO JavaScript do bloco `<script>` para arquivo
3. Usar `window.confirmModal` (não criar modal próprio)
4. Usar `window.toaster` para notificações
5. Usar `logger.debug()` ao invés de `console.log()`
6. Usar funções de `utils.js` (getCookie, etc)

### **FASE 3: Criar Templates**
1. Criar `/opt/iamkt/app/templates/content/posts_list.html`
2. Reutilizar header existente (não criar novo)
3. Reutilizar sidebar existente (não criar novo)
4. Criar bloco de background azul (similar pautas)
5. Criar bloco de filtros (estrutura da referência)
6. Criar bloco de paginação (igual pautas)
7. Criar cards de post (3 estados diferentes)

### **FASE 4: Criar Modals**
1. Modal Gerar Post (estrutura exata da referência)
2. Modal Editar Post (estrutura da referência)
3. Usar sistema de modal existente

### **FASE 5: Backend**
1. Verificar models Post existentes
2. Criar/adaptar views (generate_post, edit_post, delete_post)
3. Criar service layer (PostService)
4. Criar URLs
5. Integração N8N (webhook)

### **FASE 6: Remover Hardcodes**
1. Cores → variáveis CSS
2. URLs → settings.py
3. Limites → settings.py
4. Textos → i18n (se necessário)

---

## ✅ CHECKLIST DE CONFORMIDADE

### **Código Limpo:**
- [ ] Sem CSS inline (`style=""`)
- [ ] Sem CSS no HTML (`<style>`)
- [ ] Sem JavaScript no HTML (`<script>`)
- [ ] Sem hardcodes (cores, URLs, limites)

### **Melhores Práticas:**
- [ ] CSS em arquivo separado
- [ ] JavaScript em arquivo separado
- [ ] Variáveis de ambiente para configs
- [ ] Componentes reutilizáveis
- [ ] DRY (sem duplicação)

### **Sistemas Existentes:**
- [ ] Usar `window.confirmModal`
- [ ] Usar `window.toaster`
- [ ] Usar `logger.debug()`
- [ ] Usar funções de `utils.js`

### **Cores:**
- [ ] Roxo primário: #6366f1 (não #7c4dff)
- [ ] Seguir paleta da aplicação

---

## 📊 ESTATÍSTICAS

- **Total de linhas:** 3566
- **CSS inline:** ~268 linhas (11-279)
- **JavaScript inline:** ~2676 linhas (890-3566)
- **Ocorrências `style="`:** ~30+
- **Hardcodes identificados:** ~15+

---

## 🚀 PRÓXIMOS PASSOS

**Aguardando aprovação do usuário para:**
1. Iniciar extração de CSS
2. Iniciar extração de JavaScript
3. Criar estrutura de templates
4. Adaptar cores e estilos
5. Implementar backend

**NÃO EXECUTAR NADA AINDA - APENAS PLANEJAMENTO**

---

**Status:** ✅ Análise completa finalizada  
**Pronto para:** Aguardar aprovação e instruções do usuário
