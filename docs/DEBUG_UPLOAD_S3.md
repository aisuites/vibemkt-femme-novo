# 🔍 DEBUG - Erro 403 no Upload S3

**Status:** Investigando erro 403 Forbidden

---

## ✅ O QUE JÁ FUNCIONA

1. ✅ Backend gera Presigned URL corretamente (200 OK)
2. ✅ CORS configurado no bucket
3. ✅ Boto3 instalado no Docker
4. ✅ Headers AWS adicionados no JavaScript

---

## ❌ PROBLEMA ATUAL

**Erro:** 403 Forbidden ao fazer PUT para S3

**Headers assinados na Presigned URL:**
```
content-type
host
x-amz-meta-category
x-amz-meta-organization-id
x-amz-meta-original-name
x-amz-meta-upload-timestamp
x-amz-server-side-encryption
x-amz-storage-class
```

**Headers que o JavaScript DEVE enviar:**
```javascript
{
    'Content-Type': 'image/png',
    'x-amz-server-side-encryption': 'AES256',
    'x-amz-storage-class': 'INTELLIGENT_TIERING',
    'x-amz-meta-original-name': 'logo.png',
    'x-amz-meta-organization-id': '9',
    'x-amz-meta-category': 'logos',
    'x-amz-meta-upload-timestamp': '1706356800'
}
```

---

## 🧪 TESTE COM DEBUG MELHORADO

### **1. Recarregue a página** (Ctrl+Shift+R)

### **2. Abra o Console (F12)**

### **3. Selecione uma imagem e clique "Salvar"**

### **4. Copie e me envie TUDO que aparecer no console:**

**Especialmente estas linhas:**
```
Headers enviados para S3: {...}
URL S3: https://...
S3 Response status: 403
S3 Error response: <?xml...>
```

---

## 🔍 POSSÍVEIS CAUSAS DO 403

### **Causa 1: Headers não estão sendo enviados**
**Sintoma:** Console não mostra "Headers enviados para S3"  
**Solução:** Verificar se JavaScript foi atualizado

### **Causa 2: Valores dos headers não correspondem**
**Sintoma:** Headers enviados mas valores diferentes dos assinados  
**Solução:** Verificar timestamp, organization_id, etc

### **Causa 3: Permissões IAM insuficientes**
**Sintoma:** Headers corretos mas ainda 403  
**Solução:** Verificar política IAM do usuário AWS

### **Causa 4: Bucket Policy bloqueando**
**Sintoma:** Headers corretos mas ainda 403  
**Solução:** Verificar Bucket Policy do S3

---

## 🔧 VERIFICAR PERMISSÕES IAM

O usuário IAM precisa ter permissão para:
- `s3:PutObject`
- `s3:PutObjectAcl`

**Política IAM necessária:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::iamkt-uploads/*"
        }
    ]
}
```

---

## 🔧 VERIFICAR BUCKET POLICY

O bucket `iamkt-uploads` não deve ter política que bloqueie uploads.

**Bucket Policy recomendada:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPresignedUploads",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT_ID:user/iamkt-upload-user"
            },
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::iamkt-uploads/*"
        }
    ]
}
```

---

## 📋 PRÓXIMOS PASSOS

1. **Teste com debug** e me envie o console completo
2. **Se headers estão corretos:** Verificar permissões IAM
3. **Se permissões OK:** Verificar Bucket Policy
4. **Se tudo OK:** Testar com curl manualmente

---

**Aguardando output do console com o novo debug! 🔍**
