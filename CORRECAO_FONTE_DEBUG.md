# 🔧 CORREÇÃO FONTE - Debug Implementado

**Foco:** APENAS problemas de fonte (conforme solicitado)

---

## ✅ CORREÇÕES APLICADAS

### **1. Debug Logs Adicionados**

**Problema:** Não sabíamos por que fonte não era deletada

**Solução:** Adicionados console.logs estratégicos

```javascript
// fonts.js - removeFonte()
console.log('DEBUG removeFonte:', {
    fontId: fontId,                    // ID da fonte
    tipoValue: tipoSelect.value,       // Valor do select (GOOGLE/UPLOAD)
    isCustomFont: isCustomFont,        // Se é fonte customizada
    datasetKeys: Object.keys(fonteItem.dataset)  // Todos os data-* presentes
});
```

**O que verificar no console:**
- `fontId` deve ser número (ex: 46, 48, 49)
- `tipoValue` deve ser "UPLOAD"
- `isCustomFont` deve ser `true`
- `datasetKeys` deve incluir "fontId"

---

### **2. data-font-id Agora É Adicionado Corretamente**

**Problema:** `data-font-id` não estava sendo adicionado ao HTML

**Causa:** Parâmetro `fontId` não era passado para `addFonte()`

**Solução:**

**Assinatura modificada:**
```javascript
// ANTES
function addFonte(tipo, nomeFonte, variante, uso, arquivoUrl)

// DEPOIS
function addFonte(tipo, nomeFonte, variante, uso, arquivoUrl, fontId = null)
```

**Adição do atributo:**
```javascript
// fonts.js linha 55-58
if (fontId) {
    fonteItem.setAttribute('data-font-id', fontId);
    console.log(`DEBUG: data-font-id="${fontId}" adicionado ao fonteItem`);
}
```

**Chamada corrigida:**
```javascript
// fonts.js linha 567
// ANTES
addFonte('UPLOAD', font.name, '', font.font_type.toUpperCase(), {
    id: font.id,
    url: font.s3_url
});

// DEPOIS
addFonte('UPLOAD', font.name, '', font.font_type.toUpperCase(), font.s3_url, font.id);
```

---

## 🧪 TESTE AGORA

### **1. Recarregue a Página** (Ctrl+Shift+R)

### **2. Abra Console** (F12 → Console)

### **3. Verifique Logs de Inicialização**

Deve aparecer:
```
DEBUG: Adicionando fonte customizada: {id: 48, name: "SSTBold", font_type: "corpo", ...}
DEBUG: data-font-id="48" adicionado ao fonteItem
DEBUG: Adicionando fonte customizada: {id: 46, name: "Segoe UI", font_type: "corpo", ...}
DEBUG: data-font-id="46" adicionado ao fonteItem
DEBUG: Adicionando fonte customizada: {id: 49, name: "cordia-new-4", font_type: "corpo", ...}
DEBUG: data-font-id="49" adicionado ao fonteItem
```

### **4. Inspecione Elemento da Fonte**

1. F12 → Elements
2. Busque `.fonte-item`
3. Verifique atributos:

```html
<div class="fonte-item" 
     data-index="0" 
     data-uso-atual="CORPO" 
     data-font-id="48">  <!-- ✅ DEVE EXISTIR -->
  ...
</div>
```

### **5. Clique "Remover" em Uma Fonte**

Console deve mostrar:
```
DEBUG removeFonte: {
    fontId: "48",              // ✅ Deve ter valor
    tipoValue: "UPLOAD",       // ✅ Deve ser UPLOAD
    isCustomFont: true,        // ✅ Deve ser true
    datasetKeys: ["index", "usoAtual", "fontId"]  // ✅ fontId presente
}
```

### **6. Confirme a Remoção**

- Modal aparece
- Clique "Confirmar"
- Console deve mostrar chamada DELETE
- Toaster: "Fonte removida com sucesso!"

### **7. Recarregue e Verifique**

- Fonte NÃO deve reaparecer
- Banco de dados deve ter 1 fonte a menos

---

## ⚠️ PROBLEMA 2: Campo "uso" vs "font_type"

**Status:** ⚠️ **AINDA NÃO CORRIGIDO**

**Análise:**

**Model CustomFont:**
```python
# models.py linha 355-363
font_type = models.CharField(
    max_length=20,
    choices=[
        ('titulo', 'Título'),      # ✅ Minúsculo
        ('corpo', 'Corpo'),        # ✅ Minúsculo
        ('destaque', 'Destaque'),  # ✅ Minúsculo
    ],
    verbose_name='Tipo'
)
```

**JavaScript:**
```javascript
// fonts.js linha 567
addFonte('UPLOAD', font.name, '', font.font_type.toUpperCase(), font.s3_url, font.id);
//                                 ^^^^^^^^^^^^^^^^^^^^^^^^
//                                 Passa "CORPO" mas campo é "uso"
```

**Problema:**
- Model tem campo `font_type` com valores: `titulo`, `corpo`, `destaque`
- JavaScript passa `font.font_type.toUpperCase()` = `"CORPO"`
- Mas `addFonte()` usa 4º parâmetro como `uso`
- Valores de `uso` são: `TITULO`, `SUBTITULO`, `CORPO`, `BOTAO`, `LEGENDA`

**Mapeamento necessário:**
```javascript
const fontTypeToUso = {
    'titulo': 'TITULO',
    'corpo': 'CORPO',
    'destaque': 'SUBTITULO'  // ou outro uso apropriado
};

const uso = fontTypeToUso[font.font_type] || 'CORPO';
addFonte('UPLOAD', font.name, '', uso, font.s3_url, font.id);
```

**Ou melhor:** Usar `Typography` ao invés de `CustomFont` diretamente

---

## 📊 STATUS ATUAL

**Problema 1 (Delete):** ✅ **DEBUG IMPLEMENTADO**
- Logs adicionados
- `data-font-id` corrigido
- Pronto para testar

**Problema 2 (Campo uso):** ⚠️ **PENDENTE**
- Mapeamento necessário
- Ou usar Typography

---

## 🎯 PRÓXIMOS PASSOS

### **Imediato:**
1. Recarregue página
2. Abra console (F12)
3. Verifique logs de inicialização
4. Inspecione elemento `.fonte-item`
5. Tente remover fonte
6. **Me envie print do console**

### **Após Ver Console:**
- Se `fontId` está presente → Delete deve funcionar
- Se `fontId` está `undefined` → Investigar mais
- Se erro no DELETE → Verificar backend

### **Problema 2 (uso):**
- Decidir: mapear `font_type` → `uso` ou usar `Typography`
- Implementar solução escolhida

---

## 📁 ARQUIVOS MODIFICADOS

1. `@/opt/iamkt/app/static/js/fonts.js:45` - Assinatura `addFonte` com `fontId`
2. `@/opt/iamkt/app/static/js/fonts.js:55-58` - Adiciona `data-font-id`
3. `@/opt/iamkt/app/static/js/fonts.js:281-286` - Debug logs em `removeFonte`
4. `@/opt/iamkt/app/static/js/fonts.js:565-567` - Passa `font.id` como 6º parâmetro

---

**Teste e me envie print do console ao clicar "Remover"! 🔍**
