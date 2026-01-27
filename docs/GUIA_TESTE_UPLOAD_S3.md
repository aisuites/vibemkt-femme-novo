# 🧪 Guia de Teste - Upload S3

**Data:** 27 de Janeiro de 2026  
**Status:** ✅ Pronto para testar

---

## ✅ PRÉ-REQUISITOS VERIFICADOS

- [x] Backend Python implementado (S3Service, validators, views)
- [x] Frontend JavaScript implementado (s3-uploader.js, image-validator.js, image-preview-loader.js, uploads-s3.js)
- [x] Template atualizado (view.html)
- [x] URLs configuradas
- [x] Variáveis AWS no .env.development (confirmado pelo usuário)
- [x] Bucket S3 iamkt-uploads existe (confirmado pelo usuário)

---

## 🎯 O QUE TESTAR

### **1. Upload de Logos** 📷

**Localização:** Base IAMKT > Bloco 5 (Identidade Visual) > Logotipos

**Passos:**
1. Acesse `/knowledge/` (Base IAMKT)
2. Role até o **Bloco 5: Identidade Visual**
3. Na seção **Logotipos**, clique em "📁 Selecionar arquivos" ou arraste uma imagem
4. Selecione um arquivo PNG, JPG ou SVG (máx 5MB)

**Validações Automáticas:**
- ✅ Tipo de arquivo (PNG, JPG, SVG, WEBP)
- ✅ Tamanho máximo (5MB)
- ✅ Dimensões mínimas (100x100px)
- ✅ Dimensões máximas (5000x5000px)

**O que deve acontecer:**
1. Preview da imagem aparece imediatamente
2. Barra de progresso mostra upload (0-100%)
3. Após upload, imagem fica disponível na galeria
4. Botão "×" permite remover o logo

**Erros esperados (se houver):**
- ❌ "Tipo não permitido" → Arquivo não é imagem válida
- ❌ "Arquivo muito grande" → Maior que 5MB
- ❌ "Dimensões muito pequenas" → Menor que 100x100px

---

### **2. Upload de Imagens de Referência** 🖼️

**Localização:** Base IAMKT > Bloco 5 (Identidade Visual) > Imagens de referência

**Passos:**
1. Na mesma página, role até **Imagens de referência**
2. Clique em "📁 Selecionar imagens" ou arraste arquivos
3. Selecione imagens (PNG, JPG, GIF, WEBP - máx 10MB)

**Validações Automáticas:**
- ✅ Tipo de arquivo (PNG, JPG, GIF, WEBP)
- ✅ Tamanho máximo (10MB)
- ✅ Dimensões mínimas (200x200px)
- ✅ Dimensões máximas (10000x10000px)

**O que deve acontecer:**
1. Preview da imagem aparece imediatamente
2. Barra de progresso mostra upload
3. Imagem fica disponível na galeria
4. Botão "×" permite remover

---

### **3. Drag & Drop** 🖱️

**Teste:**
1. Arraste um arquivo de imagem do seu computador
2. Solte sobre a área de upload (deve ficar destacada)
3. Upload deve iniciar automaticamente

---

### **4. Validação de Erros** ⚠️

**Teste com arquivos inválidos:**

**Arquivo muito grande:**
- Tente enviar logo > 5MB
- Tente enviar referência > 10MB
- **Esperado:** Mensagem de erro antes do upload

**Tipo inválido:**
- Tente enviar PDF, TXT, etc
- **Esperado:** Mensagem "Tipo não permitido"

**Dimensões inválidas:**
- Logo < 100x100px
- **Esperado:** Mensagem "Dimensões muito pequenas"

---

## 🔍 O QUE VERIFICAR NO CONSOLE DO NAVEGADOR

Abra o DevTools (F12) e vá na aba **Console**. Você deve ver:

**Ao carregar a página:**
```
ImageValidator inicializado para categoria: logos
ImageValidator inicializado para categoria: references
ImagePreviewLoader inicializado
```

**Durante upload:**
```
Validando arquivo: logo.png
Gerando preview...
Iniciando upload para S3...
Upload concluído: 100%
```

**Se houver erros:**
```
Erro ao validar: [mensagem do erro]
Erro ao fazer upload: [mensagem do erro]
```

---

## 🐛 TROUBLESHOOTING

### **Erro: "CSRF token missing"**
**Causa:** Cookie de sessão não está sendo enviado  
**Solução:** Faça login novamente

### **Erro: "Access denied: arquivo não pertence à organização"**
**Causa:** Tentativa de acessar arquivo de outra organização  
**Solução:** Isso é esperado - segurança funcionando

### **Erro: "Erro AWS ao gerar URL"**
**Causa:** Credenciais AWS inválidas ou bucket não existe  
**Solução:** Verifique `.env.development`:
```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=iamkt-uploads
AWS_REGION=us-east-1
```

### **Erro: "Failed to fetch"**
**Causa:** Backend não está rodando  
**Solução:** Inicie o servidor Django

### **Imagens não aparecem após upload**
**Causa:** URLs pré-assinadas expiraram (1 hora)  
**Solução:** Recarregue a página

---

## 📊 VERIFICAR NO AWS S3

Após upload bem-sucedido, verifique no AWS Console:

1. Acesse S3 > Bucket `iamkt-uploads`
2. Navegue até `org-{id}/logos/` ou `org-{id}/references/`
3. Deve ver os arquivos com nomenclatura:
   - **Logos:** `org-1/logos/1706356800000-abc123-logo.png`
   - **Referências:** `org-1/references/1706356800000-def456-imagem.jpg`
4. Verifique propriedades:
   - **Storage Class:** INTELLIGENT_TIERING ✅
   - **Encryption:** AES256 ✅
   - **Metadata:** organization-id, category, etc ✅

---

## ✅ CHECKLIST DE TESTE

**Funcionalidades Básicas:**
- [ ] Upload de logo via botão funciona
- [ ] Upload de logo via drag & drop funciona
- [ ] Upload de imagem de referência via botão funciona
- [ ] Upload de imagem de referência via drag & drop funciona
- [ ] Preview aparece antes do upload
- [ ] Barra de progresso funciona
- [ ] Imagem aparece na galeria após upload
- [ ] Botão remover funciona

**Validações:**
- [ ] Rejeita arquivo muito grande
- [ ] Rejeita tipo de arquivo inválido
- [ ] Rejeita dimensões muito pequenas
- [ ] Aceita arquivos válidos

**Segurança:**
- [ ] Não consegue acessar arquivo de outra organização
- [ ] URLs expiram após 1 hora
- [ ] CSRF token é validado

**Performance:**
- [ ] Upload de arquivo 1MB leva < 5 segundos
- [ ] Preview é gerado instantaneamente
- [ ] Múltiplos uploads simultâneos funcionam

---

## 🚀 PRÓXIMOS PASSOS APÓS TESTE

**Se tudo funcionar:**
1. ✅ Deletar `uploads.js` antigo
2. ✅ Deletar `uploads_old.js.bak`
3. ✅ Remover comentário do template
4. ✅ Commit das mudanças

**Se houver problemas:**
1. 📝 Anotar erro específico
2. 🔍 Verificar console do navegador
3. 🔍 Verificar logs do Django
4. 💬 Reportar para ajuste

---

## 📞 SUPORTE

**Arquivos criados/modificados:**
- `apps/core/services/s3_service.py` (refatorado)
- `apps/core/utils/file_validators.py` (novo)
- `apps/core/utils/image_validators.py` (novo)
- `apps/knowledge/views_upload.py` (refatorado)
- `static/js/s3-uploader.js` (já existia)
- `static/js/image-validator.js` (novo)
- `static/js/image-preview-loader.js` (novo)
- `static/js/uploads-s3.js` (novo)
- `templates/knowledge/view.html` (atualizado)

**Documentação:**
- `MUDANCAS_S3_GUIA_2026-01-27.md` - Detalhes técnicos
- `GUIA_TESTE_UPLOAD_S3.md` - Este arquivo

---

**Boa sorte nos testes! 🎉**
