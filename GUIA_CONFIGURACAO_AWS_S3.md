# 🔧 GUIA DE CONFIGURAÇÃO AWS S3

**Data:** 27/01/2026  
**Versão:** 2.0 - Bucket Único com Prefixos  
**Status:** ✅ ATUALIZADO

---

## 🎯 ARQUITETURA FINAL

### **Decisão: Bucket Único com Prefixos por Organização**

**Por quê?**
- ✅ **Sem criação manual** - Bucket criado 1 vez só
- ✅ **Escalável** - Suporta milhares de organizações
- ✅ **CORS configurado 1 vez** - Não precisa reconfigurar
- ✅ **Padrão de mercado** - Usado por Dropbox, Google Drive, etc
- ✅ **Mais barato** - 1 bucket vs centenas

**Estrutura S3:**
```
iamkt-uploads/                          ← Bucket único
├── org-1/                              ← Organização 1
│   ├── logos/
│   │   └── org_1_logo_123.png
│   ├── references/
│   │   └── org_1_ref_456.jpg
│   └── fonts/
│       └── org_1_fonte_Roboto.ttf
├── org-2/                              ← Organização 2
│   ├── logos/
│   └── references/
└── org-3/                              ← Organização 3
    └── logos/
```

**Segurança:**
- ✅ Django valida `organization_id` em cada request
- ✅ S3Service valida que `s3_key` começa com `org-{id}/`
- ✅ Presigned URL só para path da organização
- ✅ Organização A **não acessa** arquivos da organização B

---

## 📋 PASSO A PASSO DE CONFIGURAÇÃO

### **ETAPA 1: Criar Bucket Único (1 VEZ SÓ)**

```bash
# Criar bucket
aws s3 mb s3://iamkt-uploads --region us-east-1

# Verificar se foi criado
aws s3 ls | grep iamkt-uploads
```

**Resultado esperado:**
```
2026-01-27 11:00:00 iamkt-uploads
```

---

### **ETAPA 2: Configurar CORS**

#### **2.1. Criar arquivo cors.json:**

```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["PUT", "POST", "GET"],
            "AllowedOrigins": [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "https://iamkt-femmeintegra.aisuites.com.br",
                "https://*.aisuites.com.br"
            ],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

#### **2.2. Aplicar CORS:**

```bash
aws s3api put-bucket-cors \
    --bucket iamkt-uploads \
    --cors-configuration file://cors.json
```

#### **2.3. Verificar CORS:**

```bash
aws s3api get-bucket-cors --bucket iamkt-uploads
```

**Resultado esperado:**
```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["PUT", "POST", "GET"],
            ...
        }
    ]
}
```

---

### **ETAPA 3: Configurar Encryption (Recomendado)**

```bash
aws s3api put-bucket-encryption \
    --bucket iamkt-uploads \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'
```

**Verificar:**
```bash
aws s3api get-bucket-encryption --bucket iamkt-uploads
```

---

### **ETAPA 4: Configurar Versionamento (Opcional)**

```bash
# Habilitar versionamento (permite recuperar arquivos deletados)
aws s3api put-bucket-versioning \
    --bucket iamkt-uploads \
    --versioning-configuration Status=Enabled
```

---

### **ETAPA 5: Configurar Lifecycle (Opcional)**

Para deletar versões antigas automaticamente:

```bash
# Criar lifecycle.json
cat > lifecycle.json << 'EOF'
{
    "Rules": [
        {
            "Id": "DeleteOldVersions",
            "Status": "Enabled",
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 30
            }
        }
    ]
}
EOF

# Aplicar
aws s3api put-bucket-lifecycle-configuration \
    --bucket iamkt-uploads \
    --lifecycle-configuration file://lifecycle.json
```

---

### **ETAPA 6: Configurar Permissões IAM**

#### **6.1. Política IAM para o Usuário:**

Criar arquivo `iam-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3UploadOperations",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::iamkt-uploads/*"
        },
        {
            "Sid": "AllowListBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::iamkt-uploads"
        }
    ]
}
```

#### **6.2. Anexar Política ao Usuário:**

```bash
# Criar política
aws iam create-policy \
    --policy-name IamktS3UploadPolicy \
    --policy-document file://iam-policy.json

# Anexar ao usuário (substitua USER_NAME)
aws iam attach-user-policy \
    --user-name iamkt-upload-user \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/IamktS3UploadPolicy
```

**OU anexar política inline:**

```bash
aws iam put-user-policy \
    --user-name iamkt-upload-user \
    --policy-name S3UploadAccess \
    --policy-document file://iam-policy.json
```

---

### **ETAPA 7: Validar Permissões**

#### **7.1. Testar Upload:**

```bash
# Criar arquivo de teste
echo "teste" > test.txt

# Fazer upload
aws s3 cp test.txt s3://iamkt-uploads/test.txt

# Verificar
aws s3 ls s3://iamkt-uploads/
```

**Resultado esperado:**
```
2026-01-27 11:30:00         6 test.txt
```

#### **7.2. Testar Download:**

```bash
aws s3 cp s3://iamkt-uploads/test.txt test-download.txt
cat test-download.txt
```

#### **7.3. Testar Delete:**

```bash
aws s3 rm s3://iamkt-uploads/test.txt
```

#### **7.4. Testar Presigned URL (via Python):**

```python
import boto3
from botocore.config import Config

# Configurar cliente
config = Config(region_name='us-east-1', signature_version='s3v4')
s3_client = boto3.client(
    's3',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    config=config
)

# Gerar Presigned URL para upload
url = s3_client.generate_presigned_url(
    ClientMethod='put_object',
    Params={
        'Bucket': 'iamkt-uploads',
        'Key': 'org-1/logos/test.png',
        'ContentType': 'image/png'
    },
    ExpiresIn=300,
    HttpMethod='PUT'
)

print(url)
```

---

### **ETAPA 8: Configurar Variáveis de Ambiente**

Adicionar ao `.env`:

```env
# AWS S3 Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_BUCKET_NAME=iamkt-uploads
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Marque cada item após completar:

- [ ] **Bucket criado:** `aws s3 ls | grep iamkt-uploads`
- [ ] **CORS configurado:** `aws s3api get-bucket-cors --bucket iamkt-uploads`
- [ ] **Encryption habilitado:** `aws s3api get-bucket-encryption --bucket iamkt-uploads`
- [ ] **Permissões IAM configuradas:** Política anexada ao usuário
- [ ] **Upload funciona:** `aws s3 cp test.txt s3://iamkt-uploads/test.txt`
- [ ] **Download funciona:** `aws s3 cp s3://iamkt-uploads/test.txt test-download.txt`
- [ ] **Delete funciona:** `aws s3 rm s3://iamkt-uploads/test.txt`
- [ ] **Presigned URL funciona:** Testar via Python/curl
- [ ] **Variáveis de ambiente configuradas:** `.env` atualizado

---

## 🔒 VALIDAÇÃO DE SEGURANÇA

### **Testar Isolamento entre Organizações:**

```python
# Tentar acessar arquivo de outra organização (deve falhar)
from apps.core.services import S3Service

# Organização 1 tenta acessar arquivo da Organização 2
try:
    url = S3Service.generate_presigned_download_url(
        s3_key='org-2/logos/logo.png',  # Arquivo da org 2
        organization_id=1                # Mas passando org 1
    )
    print("❌ FALHA DE SEGURANÇA: Acesso permitido!")
except ValueError as e:
    print(f"✅ SEGURANÇA OK: {e}")
    # Esperado: "Acesso negado: arquivo não pertence à organização"
```

---

## 🐛 TROUBLESHOOTING

### **Erro: "NoSuchBucket"**
**Causa:** Bucket não existe  
**Solução:**
```bash
aws s3 mb s3://iamkt-uploads --region us-east-1
```

### **Erro: "Access Denied" ao fazer upload**
**Causa:** Permissões IAM incorretas  
**Solução:** Verificar política IAM (Etapa 6)

### **Erro: "CORS policy: No 'Access-Control-Allow-Origin'"**
**Causa:** CORS não configurado ou origem não permitida  
**Solução:** 
1. Verificar CORS: `aws s3api get-bucket-cors --bucket iamkt-uploads`
2. Adicionar origem ao `cors.json` e reaplicar

### **Erro: "SignatureDoesNotMatch"**
**Causa:** Credenciais AWS incorretas  
**Solução:** Verificar `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` no `.env`

### **Erro: "Request has expired"**
**Causa:** URL Presigned expirou (5 minutos)  
**Solução:** Gerar nova URL

---

## 📊 ESTRUTURA DE ARQUIVOS GERADOS

Após configuração, você terá:

```
iamkt-uploads/
├── org-1/
│   ├── logos/
│   │   ├── org_1_logo_1706356800000_abc123.png
│   │   └── org_1_logo_1706356900000_def456.svg
│   ├── references/
│   │   ├── org_1_ref_1706357000000_ghi789.jpg
│   │   └── org_1_ref_1706357100000_jkl012.png
│   └── fonts/
│       └── org_1_fonte_Roboto.ttf
├── org-2/
│   └── logos/
│       └── org_2_logo_1706357200000_mno345.png
└── org-3/
    ├── logos/
    └── references/
```

---

## 📞 COMANDOS ÚTEIS

### **Listar arquivos de uma organização:**
```bash
aws s3 ls s3://iamkt-uploads/org-1/ --recursive
```

### **Copiar todos arquivos de uma organização:**
```bash
aws s3 cp s3://iamkt-uploads/org-1/ ./backup-org-1/ --recursive
```

### **Deletar todos arquivos de uma organização:**
```bash
# CUIDADO: Isso deleta TUDO da organização!
aws s3 rm s3://iamkt-uploads/org-1/ --recursive
```

### **Ver tamanho total por organização:**
```bash
aws s3 ls s3://iamkt-uploads/org-1/ --recursive --summarize
```

---

## 🎯 PRÓXIMOS PASSOS

Após completar esta configuração:

1. ✅ Testar upload via interface Django
2. ✅ Testar preview de imagens
3. ✅ Validar isolamento entre organizações
4. ✅ Monitorar custos no AWS Console
5. ✅ Configurar alertas de billing (opcional)

---

## 💰 ESTIMATIVA DE CUSTOS

**Bucket S3 (us-east-1):**
- **Storage:** $0.023/GB/mês
- **PUT requests:** $0.005/1000 requests
- **GET requests:** $0.0004/1000 requests

**Exemplo: 100 organizações, 1GB cada:**
- Storage: 100GB × $0.023 = **$2.30/mês**
- Uploads: 10.000 × $0.005 = **$0.05/mês**
- Downloads: 100.000 × $0.0004 = **$0.04/mês**
- **TOTAL: ~$2.40/mês**

---

**Configuração completa! Bucket único pronto para receber uploads de todas as organizações.** 🎉
