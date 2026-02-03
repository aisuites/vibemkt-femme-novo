# CHECKLIST DE IMPLEMENTAÇÃO - POSTS
## Comparação resumo.html vs posts.js

Data: 2026-02-03
Objetivo: Implementar TODAS as funcionalidades do resumo.html na aplicação posts

---

## 1. ESTRUTURA DE DADOS

### postsState
- [x] items: Array de posts
- [x] filtered: Posts filtrados
- [x] page: Página atual
- [x] perPage: Posts por página (1)
- [x] filters.date: Filtro por data
- [x] filters.status: Filtro por status
- [x] filters.search: Busca por título
- [x] selectedId: ID do post selecionado
- [x] restoredFromStorage: Flag de restauração

### editingPostRef
- [x] Referência ao post sendo editado

### statusInfo
- [x] pending: Pendente de Aprovação
- [x] approved: Aprovado
- [x] rejected: Rejeitado
- [x] agent: Agente Alterando
- [x] generating: Agente Gerando Conteúdo
- [x] image_generating: Agente Gerando Imagem
- [x] image_ready: Imagem Disponível

---

## 2. ELEMENTOS DOM

### Containers Principais
- [ ] postsPane (ADAPTAÇÃO: não é aba, é página - remover verificação)
- [ ] postsEmpty: Mensagem vazia
- [ ] postsMain: Container principal

### Detalhes do Post
- [ ] postStatus: Pill de status
- [ ] postTags: Tags/redes sociais
- [ ] postTitulo: Título
- [ ] postSubtitulo: Subtítulo
- [ ] postLegenda: Legenda
- [ ] postHashtags: Hashtags
- [ ] postCTA: Call to action
- [ ] postDescricaoImagem: Descrição da imagem
- [ ] postRevisoes: Contador de revisões
- [ ] postDataCriacao: Data de criação

### Solicitações de Alteração
- [x] textRequestBox: Container texto
- [x] textRequestInput: Input texto
- [x] imageRequestBox: Container imagem
- [x] imageRequestInput: Input imagem

### Ações e Visual
- [ ] postActions: Botões de ação
- [ ] postImageActions: Ações da imagem
- [ ] postImageFrame: Frame da imagem
- [ ] postGallery: Galeria de miniaturas

### Paginação
- [ ] postPagerInfo: Info da paginação
- [ ] pagerButtons: Botões de navegação

### Filtros
- [ ] filtroStatus: Select de status
- [ ] filtroData: Input de data
- [ ] filtroBusca: Input de busca
- [ ] btnBuscar: Botão buscar
- [ ] btnLimparFiltros: Botão limpar

### Modal Editar
- [ ] editModal: Modal
- [ ] editForm: Formulário
- [ ] editTitulo: Input título
- [ ] editSubtitulo: Input subtítulo
- [ ] editLegenda: Textarea legenda
- [ ] editHashtags: Input hashtags
- [ ] editCTA: Input CTA
- [ ] editDescricaoImagem: Textarea descrição

---

## 3. FUNÇÕES PRINCIPAIS

### Renderização
- [x] applyFilters() - Aplica filtros
- [x] getCurrentPost() - Obtém post atual
- [x] renderPosts(scrollIntoView) - Renderiza posts
- [x] buildPagination(totalItems, totalPages) - Cria paginação

### Detalhes e Visual
- [ ] updatePostDetails(post) - Atualiza detalhes
- [ ] updatePostVisual(post) - Atualiza visual/imagem
- [ ] shouldShowTextGenerationBanner(post) - Verifica banner texto
- [ ] shouldShowImageGenerationBanner(post) - Verifica banner imagem
- [ ] calculateImageDeadline(createdAtStr) - Calcula prazo imagem
- [ ] formatDeadline(date) - Formata prazo

### Ações do Post
- [x] buildPostActions(post) - Cria botões de ação
- [x] rejectPost(post) - Rejeita post
- [ ] approvePost(post) - Aprova post (IMPLEMENTAR COMPLETO)
- [x] startImageGeneration(post) - Inicia geração imagem
- [ ] submitTextRequest(post, text) - Solicitação texto (CORRIGIR PAYLOAD/URL)
- [ ] submitImageRequest(post, text) - Solicitação imagem

### Modal Edição
- [x] openEditPostModal(post) - Abre modal
- [x] closeEditPostModal() - Fecha modal
- [x] resetEditPostForm() - Reseta formulário

### Funções Auxiliares
- [x] getServerId(post) - Obtém ID servidor
- [ ] formatDateTime(dateStr) - Formata data/hora
- [ ] formatDateKey(dateStr) - Formata data para filtro

---

## 4. EVENT LISTENERS

### Solicitações de Alteração
- [x] Cancelar solicitação texto (data-action="cancel-text-request")
- [x] Enviar solicitação texto (data-action="submit-text-request")
- [x] Cancelar solicitação imagem (data-action="cancel-image-request")
- [x] Enviar solicitação imagem (data-action="submit-image-request")

### Filtros
- [ ] Filtro de status (change)
- [ ] Filtro de data (change)
- [ ] Busca por título (click + enter)
- [ ] Limpar filtros (click)

### Modal Edição
- [x] Submit formulário edição

### Paginação
- [x] Botões de página (click) - CRÍTICO: limpar selectedId

---

## 5. BANNERS DE STATUS

### Banner de Texto (coluna esquerda)
- [ ] Mostrar quando status === 'generating'
- [ ] Texto: "Seu conteúdo será gerado em até 3 minutos."
- [ ] Botão "Atualizar Status" que recarrega página
- [ ] Classe: .post-text-status-banner
- [ ] Inserir antes de dom.postStatus.parentElement

### Banner de Imagem (coluna direita)
- [ ] Mostrar quando status === 'image_generating' OU imageStatus === 'generating'
- [ ] Calcular prazo: 3 dias úteis a partir de createdAt
- [ ] Texto: "Sua imagem será gerada até DD/MM/YY às HH:MM"
- [ ] Botão "Atualizar Status" que recarrega página
- [ ] Classe: .post-image-status-banner
- [ ] Inserir antes de dom.postImageFrame

---

## 6. GALERIA DE IMAGENS

### Carrossel
- [ ] Verificar se post.imagens.length > 1
- [ ] Criar miniaturas clicáveis
- [ ] Destacar miniatura ativa (classe 'active')
- [ ] Atualizar post.activeImageIndex ao clicar
- [ ] Re-renderizar com updatePostVisual()

### Ações da Imagem
- [ ] Se imageChanges >= 1: mostrar badge "Limite atingido"
- [ ] Se imageChanges < 1: botão "Solicitar Alteração de imagem"
- [ ] Ocultar ações se imageRequestOpen === true

---

## 7. VALIDAÇÕES E TRATAMENTOS

### Normalização Inicial
- [ ] Garantir serverId em cada post
- [ ] Garantir imageChanges como número
- [ ] Garantir statusLabel

### LocalStorage
- [x] Salvar selectedPostId ao navegar
- [x] Restaurar selectedPostId na primeira renderização
- [x] Flag restoredFromStorage para evitar loop

### Rollback em Erro
- [ ] submitTextRequest: salvar estado anterior
- [ ] submitTextRequest: restaurar se falhar
- [ ] Reabrir caixa de texto com conteúdo

---

## 8. ENDPOINTS E PAYLOADS

### CRÍTICO: Ajustar URLs
resumo.html usa: `/api/posts/${serverId}/...`
Nossa app deve usar: `/posts/${serverId}/...`

### Rejeitar Post
- URL: `/posts/${serverId}/reject/`
- Payload: `{}`
- Resposta: `{ success, status, statusLabel, revisoesRestantes }`

### Aprovar Post
- URL: `/posts/${serverId}/approve/`
- Payload: `{}`
- Resposta: `{ success, status, statusLabel }`

### Gerar Imagem
- URL: `/posts/${serverId}/generate-image/`
- Payload: `{}`
- Resposta: `{ success, status, statusLabel }`

### Solicitar Alteração Texto
- URL: `/posts/${serverId}/request-text-change/`
- Payload: `{ mensagem: "texto" }` (CRÍTICO: 'mensagem' não 'request')
- Resposta: `{ success, status, statusLabel, revisoesRestantes, imageChanges }`

### Solicitar Alteração Imagem
- URL: `/posts/${serverId}/request-image-change/`
- Payload: `{ mensagem: "texto" }` (CRÍTICO: 'mensagem' não 'request')
- Resposta: `{ success, status, statusLabel }`

### Editar Post
- URL: `/posts/${serverId}/edit/`
- Payload: `{ titulo, subtitulo, legenda, hashtags, cta, descricaoImagem }`
- Resposta: `{ success, message }`

---

## 9. CAMPOS DO POST (Model)

### Verificar se existem no Model Post:
- [ ] title (titulo no JS)
- [ ] subtitle (subtitulo no JS)
- [ ] caption (legenda no JS)
- [ ] hashtags
- [ ] cta
- [ ] image_prompt (descricaoImagem no JS)
- [ ] status
- [ ] image_status (imageStatus no JS)
- [ ] image_changes (imageChanges no JS)
- [ ] images (imagens no JS) - JSONField?
- [ ] active_image_index (activeImageIndex no JS)
- [ ] formats (formatos no JS) - JSONField?
- [ ] network (rede no JS)
- [ ] created_at (createdAt no JS)
- [ ] revisions_remaining (revisoesRestantes no JS)

---

## 10. CSS CLASSES (verificar em posts.css)

### Banners
- [ ] .post-text-status-banner
- [ ] .post-image-status-banner
- [ ] .status-icon
- [ ] .status-text

### Status Pills
- [ ] .status-pill
- [ ] .is-pending
- [ ] .is-approved
- [ ] .is-rejected
- [ ] .is-agent

### Badges
- [ ] .badge-muted
- [ ] .badge-success
- [ ] .badge-danger

### Outros
- [ ] .placeholder (imagem)
- [ ] .post-tag (tags/redes)
- [ ] .post-request (caixa solicitação)
- [ ] .request-actions (botões cancelar/enviar)

---

## 11. GAPS IDENTIFICADOS (O QUE FALTA)

### ALTA PRIORIDADE
1. [ ] Implementar updatePostDetails() COMPLETO
   - Banners de texto
   - Tags/redes sociais formatadas
   - Contador de revisões
   - Data de criação
   
2. [ ] Implementar updatePostVisual() COMPLETO
   - Banners de imagem com deadline
   - Galeria de carrossel
   - Ações da imagem
   - Placeholder de estados
   
3. [ ] Corrigir submitTextRequest()
   - Payload: 'mensagem' não 'request'
   - Rollback em caso de erro
   - Atualizar revisoesRestantes
   
4. [ ] Implementar event listeners de filtros
   - Status, data, busca, limpar

5. [ ] Verificar campos do Model Post
   - Mapear todos os campos necessários
   - Criar migration se necessário

### MÉDIA PRIORIDADE
6. [ ] Funções auxiliares de formatação
   - formatDateTime()
   - formatDateKey()
   - calculateImageDeadline()
   - formatDeadline()
   
7. [ ] submitImageRequest() completo
   - Payload correto
   - Validação limite

8. [ ] approvePost() implementação

### BAIXA PRIORIDADE
9. [ ] Remover logs de debug
10. [ ] Otimizações de performance

---

## 12. PLANO DE EXECUÇÃO

### FASE 1: Análise e Preparação
- [x] Criar este checklist
- [ ] Verificar Model Post e campos
- [ ] Verificar views_actions.py e ajustar se necessário
- [ ] Verificar CSS e adicionar classes faltantes

### FASE 2: Funções Core
- [ ] Implementar formatDateTime()
- [ ] Implementar formatDateKey()
- [ ] Implementar calculateImageDeadline()
- [ ] Implementar formatDeadline()
- [ ] Implementar shouldShowTextGenerationBanner()
- [ ] Implementar shouldShowImageGenerationBanner()

### FASE 3: updatePostDetails()
- [ ] Banner de texto
- [ ] Tags formatadas
- [ ] Revisões
- [ ] Data criação
- [ ] Testar

### FASE 4: updatePostVisual()
- [ ] Banner de imagem
- [ ] Galeria carrossel
- [ ] Ações da imagem
- [ ] Placeholders
- [ ] Testar

### FASE 5: Correções e Event Listeners
- [ ] Corrigir submitTextRequest()
- [ ] Implementar filtros
- [ ] Testar todas as ações

### FASE 6: Finalização
- [ ] Remover logs debug
- [ ] Testes completos
- [ ] Commit final

---

## NOTAS IMPORTANTES

1. **NÃO MUDAR** lógica do resumo.html
2. **APENAS ADAPTAR**: HTML/CSS/JS separados, endpoints, aba→página
3. **MANTER IDÊNTICO**: classes, funções, estruturas, payloads
4. **TESTAR** cada funcionalidade após implementar
5. **COMMIT** a cada fase concluída
