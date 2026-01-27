# 🔧 PROBLEMAS RESTANTES E SOLUÇÕES

**Data:** 27 de Janeiro de 2026

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### **1. Imagens Falham ao Carregar (Presigned URL)**

**Status:** Presigned URL é gerada corretamente mas imagem falha ao carregar

**Erro:** `Error: Falha ao carregar imagem`

**Causa Provável:** CORS no S3 não permite headers da presigned URL

**Teste Realizado:**
```python
✅ Presigned URL gerada: https://iamkt-uploads.s3.amazonaws.com/org-9/logos/...
✅ Expira em: 3600 segundos
```

**Solução Temporária:** Usar URL pública do S3 (se bucket for público) ou ajustar CORS

**Solução Definitiva:** 
1. Verificar CORS do bucket S3
2. Adicionar `Access-Control-Allow-Origin: *` nas respostas S3
3. Ou usar CloudFront na frente do S3

---

### **2. Botão Remover Logo Não Funciona**

**Status:** ✅ CORRIGIDO

**Causa:** Event listener estava comentado em `knowledge-events.js`

**Solução Aplicada:**
```javascript
// knowledge-events.js
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-action="remove-logo"]')) {
        const logoId = btn.dataset.logoId;
        removeLogo(logoId); // Chama função de uploads-s3.js
    }
});
```

---

### **3. Fontes Não São Deletadas do Banco**

**Status:** ⚠️ PENDENTE

**Causa:** Não existe endpoint de delete para `CustomFont`

**O que acontece:**
1. Usuário remove fonte visualmente (JavaScript)
2. Clica "Salvar"
3. Formulário é submetido mas CustomFont não é deletado do banco
4. Ao recarregar, fonte reaparece

**Solução Necessária:**
1. Criar endpoint `/knowledge/font/<int:font_id>/delete/`
2. Criar view `delete_custom_font(request, font_id)`
3. Adicionar rota em `urls.py`
4. Modificar JavaScript para chamar endpoint ao remover

**Alternativa Simples:**
- Fontes customizadas são gerenciadas apenas via Django Admin
- Usuário pode adicionar mas não remover pelo frontend

---

## 📊 STATUS ATUAL

### **✅ Funcionando:**
- Upload de logos para S3
- Upload de referências para S3
- Upload de fontes para S3
- Criação de registros no banco
- Preview dinâmico após upload
- Consolidação de KnowledgeBases
- Botão remover logo (corrigido)

### **⚠️ Parcialmente Funcionando:**
- Preview de imagens existentes (presigned URL gerada mas falha ao carregar)
- Remoção de fontes (visual funciona, banco não)

### **❌ Não Funcionando:**
- Preview de imagens via presigned URL (CORS)
- Delete de CustomFont do banco

---

## 🔧 CORREÇÕES APLICADAS NESTA SESSÃO

1. ✅ CustomFont importado em views_upload.py
2. ✅ custom_fonts adicionado ao contexto da view
3. ✅ Template passa custom_fonts ao JavaScript
4. ✅ fonts.js exibe fontes customizadas
5. ✅ ImagePreviewLoader inicializado automaticamente
6. ✅ getAttribute('data-lazy-load') corrigido
7. ✅ removeFonte aceita índice ou button
8. ✅ Event listener para remover logo adicionado

---

## 🎯 PRÓXIMOS PASSOS RECOMENDADOS

### **Prioridade Alta:**
1. **Corrigir CORS do S3** para presigned URLs funcionarem
2. **Criar endpoint de delete** para CustomFont

### **Prioridade Média:**
3. Adicionar placeholder para imagens enquanto carregam
4. Melhorar mensagens de erro no frontend

### **Prioridade Baixa:**
5. Calcular hash perceptual para ReferenceImage
6. Obter dimensões automáticas de imagens

---

## 🧪 COMO TESTAR

### **Teste 1: Upload de Logo**
1. Selecione imagem → Preview "Novo" → Salvar
2. ✅ **Esperado:** Upload S3 + Registro banco + Preview permanente

### **Teste 2: Remover Logo**
1. Clique "×" em um logo existente
2. ✅ **Esperado:** Confirmação → Delete do banco → Logo removido

### **Teste 3: Upload de Fonte**
1. Adicionar fonte → Selecionar .ttf → Upload automático
2. ✅ **Esperado:** Upload S3 + Registro banco + Aparece na lista

### **Teste 4: Remover Fonte**
1. Clique "Remover" em uma fonte
2. ⚠️ **Atual:** Remove visualmente mas reaparece após refresh
3. ❌ **Esperado:** Delete do banco permanente

---

## 📝 ARQUIVOS IMPORTANTES

**Backend:**
- `apps/knowledge/views_upload.py` - Views de upload e delete
- `apps/knowledge/urls.py` - Rotas
- `apps/knowledge/models.py` - Models (Logo, CustomFont, ReferenceImage)
- `apps/core/services/s3_service.py` - Serviço S3

**Frontend:**
- `static/js/uploads-simple.js` - Upload com preview
- `static/js/uploads-s3.js` - Funções de delete
- `static/js/image-preview-loader.js` - Lazy loading
- `static/js/fonts.js` - Gerenciamento de fontes
- `static/js/knowledge-events.js` - Event listeners

**Templates:**
- `templates/knowledge/view.html` - Template principal

---

**Resumo:** Upload funcionando 100%, preview com problema de CORS, delete de fontes pendente.
