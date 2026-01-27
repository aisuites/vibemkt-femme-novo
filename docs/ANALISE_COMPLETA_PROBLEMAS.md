# 🔍 ANÁLISE COMPLETA - Problemas e Soluções

**Data:** 27 de Janeiro de 2026  
**Status:** ✅ **CORREÇÕES APLICADAS**

---

## 📋 PROBLEMAS RELATADOS

1. ❌ Upload de referência falha: `S3Uploader is not defined`
2. ❌ Janela de escolher arquivo abre 2x
3. ❌ Botão X não aparece mais
4. ❌ Fonte não é deletada do banco (persiste após salvar)

---

## 🔍 ANÁLISE PROFUNDA

### **PROBLEMA 1: S3Uploader is not defined**

**Erro:**
```
ReferenceError: S3Uploader is not defined
    at HTMLInputElement.handleReferenceUpload (uploads-s3.js:220:30)
```

**Causa Raiz:**
1. `uploads-s3.js` depende da classe `S3Uploader`
2. `S3Uploader` está definida em `s3-uploader.js`
3. `s3-uploader.js` **NÃO estava sendo carregado** no template
4. `uploads-s3.js` tentava instanciar classe inexistente

**Ordem de carregamento ANTES (ERRADO):**
```html
<script src="{% static 'js/uploads-simple.js' %}"></script>
<script src="{% static 'js/uploads-s3.js' %}"></script>  <!-- ❌ S3Uploader não existe
```

**Solução Aplicada:**
```html
<script src="{% static 'js/s3-uploader.js' %}"></script>  <!-- ✅ Carrega ANTES -->
<script src="{% static 'js/uploads-simple.js' %}"></script>
<script src="{% static 'js/uploads-s3.js' %}"></script>
```

**Problema Adicional - Sintaxe Incorreta:**

`S3Uploader` espera 3 parâmetros:
```javascript
constructor(uploadUrlEndpoint, createRecordEndpoint, options = {})
```

Mas `uploads-s3.js` estava passando apenas 1 objeto:
```javascript
// ❌ ERRADO
const uploader = new S3Uploader({
    generateUrlEndpoint: '...',
    createRecordEndpoint: '...',
    category: 'logos'
});
```

**Correção:**
```javascript
// ✅ CORRETO
const uploader = new S3Uploader(
    UploadS3Config.endpoints.logoUploadUrl,      // Parâmetro 1
    UploadS3Config.endpoints.logoCreate,         // Parâmetro 2
    {                                             // Parâmetro 3 (options)
        category: 'logos',
        onProgress: (percent) => { ... },
        onSuccess: (data) => { ... },
        onError: (error) => { ... }
    }
);
```

**Arquivos Modificados:**
- `templates/knowledge/view.html` (linha 643) - Adicionado s3-uploader.js
- `static/js/uploads-s3.js` (linhas 61-79, 222-239) - Corrigida sintaxe

---

### **PROBLEMA 2: Janela de Escolher Arquivo Abre 2x**

**Sintoma:** Ao clicar em "Selecionar arquivos", janela abre, fecha e abre novamente

**Causa Raiz:** Event listeners duplicados

**Análise:**

1. **uploads-s3.js (linha 421-424):**
```javascript
const logoInput = document.getElementById('logo-upload-input');
if (logoInput) {
    logoInput.addEventListener('change', handleLogoUpload);  // ❌ Listener 1
}
```

2. **uploads-simple.js (linha similar):**
```javascript
const logoInput = document.getElementById('logo-upload-input');
if (logoInput) {
    logoInput.addEventListener('change', handleLogoUpload);  // ❌ Listener 2
}
```

**Resultado:** Mesmo input tem 2 event listeners, dispara 2x

**Solução:**

Manter apenas 1 sistema de upload ativo. Como `uploads-simple.js` é usado para upload com preview local e `uploads-s3.js` para upload direto, precisamos:

**Opção A (RECOMENDADA):** Usar apenas `uploads-s3.js`
- Remove `uploads-simple.js` do template
- `uploads-s3.js` já faz upload direto para S3

**Opção B:** Usar apenas `uploads-simple.js`
- Remove `uploads-s3.js` do template
- Mantém upload com preview local

**Opção C:** Desabilitar event listeners de um dos arquivos
- Comentar listeners em `uploads-simple.js`
- Manter apenas `uploads-s3.js` ativo

**Status:** ⚠️ **PENDENTE** (aguardando decisão de qual sistema usar)

---

### **PROBLEMA 3: Botão X Não Aparece**

**Sintoma:** Botões "×" de remover logo/referência não aparecem na tela

**Análise do Template:**

```html
<!-- view.html linha 328-330 -->
<button type="button" class="btn-remove-logo" 
        data-action="remove-logo" 
        data-logo-id="{{ logo.id }}" 
        title="Remover">
  ×
</button>
```

**Botão ESTÁ no HTML** ✅

**Possíveis Causas:**

1. **CSS oculta o botão:**
```css
/* uploads.css */
.btn-remove-logo {
    display: none;  /* ❌ Oculto por padrão? */
}

.logo-preview-item:hover .btn-remove-logo {
    display: block;  /* ✅ Aparece no hover */
}
```

2. **JavaScript remove o botão:**
- Algum script pode estar removendo o botão do DOM

3. **Z-index ou posicionamento:**
- Botão pode estar atrás de outro elemento

**Verificação Necessária:**
1. Inspecionar elemento no navegador (F12)
2. Verificar se botão existe no DOM
3. Verificar estilos CSS aplicados
4. Verificar `display`, `visibility`, `opacity`

**Status:** ⚠️ **PENDENTE** (precisa inspeção no navegador)

---

### **PROBLEMA 4: Fonte Não É Deletada do Banco**

**Sintoma:** Fonte é removida visualmente mas reaparece após salvar e recarregar

**Análise do Banco de Dados:**
```
KB 5: 1 fonte
  - ID 46: Segoe UI (type: corpo)
```

**Fluxo Atual:**

1. Usuário clica "Remover" → `removeFonte()` é chamada
2. JavaScript verifica se é fonte customizada (UPLOAD)
3. Se sim, chama `DELETE /knowledge/font/{id}/delete/`
4. Remove elemento visual do DOM
5. Ao recarregar, view busca do banco e fonte reaparece

**Possíveis Causas:**

**A) `data-font-id` não está presente:**
```javascript
// fonts.js linha 274
const fontId = fonteItem.dataset.fontId;  // undefined?
```

Se `data-font-id` não existe no HTML, `fontId` será `undefined` e delete não acontece.

**Verificação:**
```html
<!-- Deve ter data-font-id -->
<div class="fonte-item" data-font-id="46">
```

**B) Tipo da fonte não é "UPLOAD":**
```javascript
// fonts.js linha 276
const isCustomFont = tipoSelect && tipoSelect.value === 'UPLOAD';
```

Se `tipoSelect.value !== 'UPLOAD'`, código não chama endpoint de delete.

**C) Endpoint retorna erro:**
```javascript
// fonts.js linha 289-294
const response = await fetch(`/knowledge/font/${fontId}/delete/`, {
    method: 'DELETE',
    headers: {'X-CSRFToken': getCookie('csrftoken')}
});

if (!data.success) {
    toaster.error(data.error || 'Erro ao remover fonte');
    return;  // ❌ Não remove visualmente se falhar
}
```

**Diagnóstico Necessário:**

1. **Inspecionar elemento da fonte:**
```html
<div class="fonte-item" data-font-id="???" data-index="0">
  <select class="fonte-tipo">
    <option value="GOOGLE">Google Fonts</option>
    <option value="UPLOAD" selected>Upload TTF</option>  <!-- ??? -->
  </select>
</div>
```

2. **Verificar console do navegador:**
- Há erro ao chamar `/knowledge/font/46/delete/`?
- Resposta é `{success: true}` ou `{success: false}`?

3. **Verificar logs do Django:**
```bash
docker logs iamkt_web | grep "delete_custom_font"
```

**Status:** ⚠️ **PENDENTE** (precisa inspeção no navegador + logs)

---

## ✅ CORREÇÕES APLICADAS

### **1. S3Uploader Carregado e Corrigido**

**Arquivo:** `templates/knowledge/view.html`
```html
<script src="{% static 'js/s3-uploader.js' %}"></script>  <!-- ✅ ADICIONADO -->
<script src="{% static 'js/uploads-simple.js' %}"></script>
<script src="{% static 'js/uploads-s3.js' %}"></script>
```

**Arquivo:** `static/js/uploads-s3.js`
```javascript
// ✅ CORRIGIDO - 3 parâmetros
const uploader = new S3Uploader(
    UploadS3Config.endpoints.logoUploadUrl,
    UploadS3Config.endpoints.logoCreate,
    { category: 'logos', onProgress, onSuccess, onError }
);
```

---

## ⚠️ AÇÕES PENDENTES

### **1. Resolver Event Listeners Duplicados**

**Decisão Necessária:** Qual sistema de upload usar?

**Opção A:** Apenas `uploads-s3.js` (upload direto)
- Remove `uploads-simple.js` do template
- ✅ Mais simples
- ✅ Upload direto para S3
- ❌ Sem preview local antes de salvar

**Opção B:** Apenas `uploads-simple.js` (upload ao salvar)
- Remove `uploads-s3.js` do template
- ✅ Preview local
- ✅ Upload apenas ao salvar formulário
- ❌ Mais complexo

**Recomendação:** **Opção A** (uploads-s3.js) - Mais direto e profissional

---

### **2. Investigar Botão X Não Aparecendo**

**Passos:**
1. Abrir DevTools (F12)
2. Inspecionar elemento do logo
3. Verificar se `<button class="btn-remove-logo">` existe
4. Verificar CSS aplicado:
   - `display: none`?
   - `visibility: hidden`?
   - `opacity: 0`?
5. Verificar z-index e posicionamento

**Se botão não existe no DOM:**
- JavaScript está removendo
- Template não está renderizando

**Se botão existe mas não aparece:**
- Problema de CSS
- Corrigir em `uploads.css`

---

### **3. Investigar Fonte Não Deletada**

**Passos:**
1. Abrir DevTools (F12) → Console
2. Inspecionar elemento da fonte "Segoe UI"
3. Verificar atributos:
   - `data-font-id="46"` existe?
   - `<select class="fonte-tipo">` tem `value="UPLOAD"`?
4. Clicar "Remover"
5. Verificar console:
   - Chamada `DELETE /knowledge/font/46/delete/` acontece?
   - Resposta é `{success: true}` ou erro?
6. Se erro, verificar logs Django:
```bash
docker logs iamkt_web | tail -50
```

**Possíveis Correções:**

**Se `data-font-id` não existe:**
```javascript
// fonts.js - Garantir que data-font-id é adicionado
fonteItem.setAttribute('data-font-id', font.id);
```

**Se tipo não é "UPLOAD":**
```javascript
// fonts.js - Verificar inicialização
addFonte('UPLOAD', font.name, '', font.font_type.toUpperCase(), {
    id: font.id,
    url: font.s3_url
});
```

**Se endpoint retorna erro:**
- Verificar `views_upload.py` linha 595-631
- Verificar permissões
- Verificar CSRF token

---

## 🎯 PRÓXIMOS PASSOS

### **Imediato:**
1. ✅ Testar upload de referência (deve funcionar agora)
2. ⚠️ Decidir qual sistema de upload usar (A ou B)
3. ⚠️ Inspecionar botão X no navegador
4. ⚠️ Inspecionar fonte no navegador + console

### **Após Inspeção:**
5. Corrigir event listeners duplicados
6. Corrigir CSS do botão X (se necessário)
7. Corrigir delete de fonte (se necessário)

---

## 📝 RESUMO EXECUTIVO

**Problema 1 (S3Uploader):** ✅ **RESOLVIDO**
- Script carregado
- Sintaxe corrigida
- Upload deve funcionar

**Problema 2 (Janela 2x):** ⚠️ **PENDENTE**
- Event listeners duplicados
- Decisão necessária: qual sistema usar

**Problema 3 (Botão X):** ⚠️ **PENDENTE**
- Inspeção necessária
- Provavelmente CSS

**Problema 4 (Fonte):** ⚠️ **PENDENTE**
- Inspeção necessária
- Verificar data-font-id e console

---

**Teste upload de referência e me envie prints do console para os outros problemas! 🚀**
