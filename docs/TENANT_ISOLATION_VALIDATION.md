# 🔒 Guia de Validação de Isolamento de Tenants

## 📋 Objetivo

Validar que o sistema multi-tenant está funcionando corretamente e que cada organization só acessa seus próprios dados.

---

## 🎯 Dados de Teste Criados

### **Organization 1: IAMKT**
- **Plano:** Premium
- **Quotas:**
  - Pautas/Dia: 20
  - Posts/Dia: 20
  - Posts/Mês: 100
  - Vídeos/Dia: 5
  - Vídeos/Mês: 20

### **Organization 2: ACME Corp**
- **Plano:** Basic
- **Quotas:**
  - Pautas/Dia: 5
  - Posts/Dia: 5
  - Posts/Mês: 30
  - Vídeos/Dia: 2
  - Vídeos/Mês: 10

### **Usuários de Teste**

| Username | Email | Senha | Organization | Area |
|----------|-------|-------|--------------|------|
| `user_iamkt` | user@iamkt.com | senha123 | IAMKT | Marketing |
| `user_acme` | user@acmecorp.com | senha123 | ACME Corp | Vendas |

---

## 🧪 Testes de Isolamento

### **TESTE 1: Login e Dashboard**

#### **1.1. Login com user_iamkt**
1. Acesse: `http://iamkt-femmeintegra.aisuites.com.br/admin/logout/` (fazer logout se necessário)
2. Acesse: `http://iamkt-femmeintegra.aisuites.com.br/admin/`
3. Login:
   - Username: `user_iamkt`
   - Senha: `senha123`
4. Acesse: `http://iamkt-femmeintegra.aisuites.com.br/dashboard/`

**✅ Esperado:**
- Dashboard carrega sem erros
- Bem-vindo: "Bem-vindo, João!"
- Quotas de Uso mostra:
  - Pautas Hoje: 0 / 20
  - Posts Hoje: 0 / 20
  - Posts Mês: 0 / 100

#### **1.2. Login com user_acme**
1. Fazer logout
2. Login com:
   - Username: `user_acme`
   - Senha: `senha123`
3. Acesse dashboard

**✅ Esperado:**
- Dashboard carrega sem erros
- Bem-vindo: "Bem-vindo, Maria!"
- Quotas de Uso mostra:
  - Pautas Hoje: 0 / 5
  - Posts Hoje: 0 / 5
  - Posts Mês: 0 / 30

---

### **TESTE 2: Criar Dados (IAMKT)**

#### **2.1. Criar Pauta como user_iamkt**
1. Login como `user_iamkt`
2. Acesse: `/content/pautas/` ou clique em "Nova Pauta"
3. Criar pauta:
   - Título: "Pauta IAMKT 1"
   - Tema: "Marketing Digital"
   - Público-alvo: "Empresas B2B"
   - Objetivo: Engajamento
4. Salvar

**✅ Esperado:**
- Pauta criada com sucesso
- Dashboard atualiza: Pautas Hoje: 1 / 20

#### **2.2. Criar Post como user_iamkt**
1. Ainda como `user_iamkt`
2. Criar post (se houver formulário disponível)
3. Ou via Django Admin:
   - Ir em `/admin/content/post/add/`
   - Preencher campos obrigatórios
   - Organization: IAMKT
   - User: user_iamkt
   - Area: Marketing
   - Salvar

**✅ Esperado:**
- Post criado com sucesso
- Dashboard atualiza: Posts Hoje: 1 / 20

---

### **TESTE 3: Validar Isolamento**

#### **3.1. Verificar que user_acme NÃO vê dados de IAMKT**
1. Fazer logout
2. Login como `user_acme`
3. Acessar dashboard
4. Verificar estatísticas

**✅ Esperado:**
- Pautas Total: 0 (não vê a pauta de IAMKT)
- Posts Total: 0 (não vê o post de IAMKT)
- Quotas de Uso: 0 / 5 (seus próprios limites)

#### **3.2. Verificar no Django Admin**
1. Ainda como `user_acme`
2. Ir em `/admin/content/pauta/`

**✅ Esperado:**
- Lista vazia (não vê pautas de IAMKT)
- Ou apenas pautas da ACME Corp (se criar alguma)

---

### **TESTE 4: Criar Dados (ACME Corp)**

#### **4.1. Criar Pauta como user_acme**
1. Login como `user_acme`
2. Criar pauta:
   - Título: "Pauta ACME 1"
   - Tema: "Vendas B2C"
   - Público-alvo: "Consumidores finais"
   - Objetivo: Conversão
3. Salvar

**✅ Esperado:**
- Pauta criada com sucesso
- Dashboard atualiza: Pautas Hoje: 1 / 5

#### **4.2. Verificar que user_iamkt NÃO vê dados de ACME**
1. Fazer logout
2. Login como `user_iamkt`
3. Verificar dashboard

**✅ Esperado:**
- Pautas Total: 1 (apenas sua própria pauta)
- Não vê "Pauta ACME 1"

---

### **TESTE 5: Base de Conhecimento**

#### **5.1. Criar KB para IAMKT**
1. Login como `user_iamkt`
2. Acesse: `/knowledge/`
3. Preencher dados:
   - Nome da Empresa: IAMKT
   - Segmento: Tecnologia
   - Etc.
4. Salvar

**✅ Esperado:**
- KnowledgeBase criada para IAMKT
- Completude atualizada

#### **5.2. Verificar que user_acme tem KB separada**
1. Fazer logout
2. Login como `user_acme`
3. Acesse: `/knowledge/`

**✅ Esperado:**
- Nova KnowledgeBase criada automaticamente para ACME Corp
- Nome da Empresa: ACME Corp (auto-preenchido)
- Dados vazios (não vê dados de IAMKT)

---

### **TESTE 6: Quotas Diferentes**

#### **6.1. Testar limite de ACME Corp (5 posts/dia)**
1. Login como `user_acme`
2. Criar 5 posts via Admin
3. Tentar criar o 6º post

**✅ Esperado:**
- Dashboard mostra: Posts Hoje: 5 / 5 (100%)
- Barra de progresso vermelha
- Ao tentar criar 6º post: erro ou bloqueio (se validação estiver implementada)

#### **6.2. Verificar que IAMKT tem limite maior**
1. Fazer logout
2. Login como `user_iamkt`
3. Dashboard mostra: Posts Hoje: 1 / 20 (5%)

**✅ Esperado:**
- Limite diferente (20 vs 5)
- Pode criar mais posts sem atingir limite

---

### **TESTE 7: Admin (Superuser)**

#### **7.1. Verificar visão global**
1. Login como superuser (admin)
2. Ir em `/admin/content/pauta/`

**✅ Esperado:**
- Vê TODAS as pautas (IAMKT + ACME Corp)
- Filtro por organization disponível

#### **7.2. Verificar Organizations**
1. Ir em `/admin/core/organization/`

**✅ Esperado:**
- Lista com 2 organizations:
  - IAMKT (Premium)
  - ACME Corp (Basic)
- Pode editar quotas de cada uma

---

## 🐛 Problemas Comuns

### **Erro: "relation content_generatedcontent does not exist"**
**Solução:** Já foi corrigido. Reinicie o container se persistir.

### **Erro: "KnowledgeBase has no attribute get_instance"**
**Solução:** Já foi corrigido. Reinicie o container se persistir.

### **Dashboard não mostra quotas**
**Solução:** QuotaUsageDaily é criado automaticamente ao criar Pauta/Post.

### **Usuário vê dados de outra organization**
**Problema:** Isolamento não está funcionando!
**Debug:**
```bash
# Verificar se managers estão aplicados
docker compose exec -u root iamkt_web python manage.py shell

from apps.content.models import Pauta, Post
print(Pauta.objects.model._meta.managers)
print(Post.objects.model._meta.managers)
```

---

## ✅ Checklist de Validação

Marque conforme testa:

### **Isolamento Básico**
- [ ] user_iamkt vê apenas dados de IAMKT
- [ ] user_acme vê apenas dados de ACME Corp
- [ ] Dashboard mostra quotas corretas para cada org
- [ ] KnowledgeBase é separada por organization

### **Funcionalidades**
- [ ] Pode criar Pauta como user_iamkt
- [ ] Pode criar Post como user_iamkt
- [ ] Pode criar Pauta como user_acme
- [ ] Pode criar Post como user_acme
- [ ] Dashboard atualiza após criação

### **Quotas**
- [ ] IAMKT tem quotas maiores (20/dia)
- [ ] ACME Corp tem quotas menores (5/dia)
- [ ] Barras de progresso funcionam
- [ ] Cores mudam (verde → amarelo → vermelho)

### **Admin**
- [ ] Superuser vê todas as organizations
- [ ] Pode filtrar por organization
- [ ] Pode editar quotas
- [ ] QuotaUsageDaily registra uso

---

## 🎉 Sistema Validado!

Se todos os testes passarem, o **isolamento de tenants está funcionando corretamente** e o sistema está pronto para produção!

**Próximos passos:**
- Implementar FASE 4 (Autenticação/Onboarding)
- Adicionar mais validações de quota
- Implementar bloqueio ao atingir limite
- Melhorar UX do dashboard

---

## 📞 Suporte

Se encontrar problemas:
1. Verificar logs: `docker compose logs iamkt_web --tail=50`
2. Verificar migrations: `docker compose exec -u root iamkt_web python manage.py showmigrations`
3. Recriar dados de teste: `docker compose exec -u root iamkt_web python scripts/create_test_data.py`
