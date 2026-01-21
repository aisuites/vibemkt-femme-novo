# 🔔 Sistema de Alertas de Quota - IAMKT

Sistema automatizado de monitoramento e notificação de uso de quotas.

## 📋 Visão Geral

O sistema monitora o uso de quotas em tempo real e envia alertas por email quando os limites são atingidos, evitando surpresas e permitindo ação proativa.

---

## 🎯 Funcionalidades

### **Monitoramento Automático**
- ✅ Verificação a cada hora via Celery Beat
- ✅ Monitora 5 tipos de quotas:
  - Pautas Diárias
  - Posts Diários
  - Posts Mensais
  - Custo Mensal (USD)
- ✅ Suporta múltiplas organizations

### **Alertas Configuráveis**
- ✅ Threshold de 80% (aviso)
- ✅ Threshold de 100% (crítico)
- ✅ Emails personalizados por organization
- ✅ Prevenção de duplicatas

### **Registro de Histórico**
- ✅ Todos os alertas são registrados em `QuotaAlert`
- ✅ Rastreabilidade completa
- ✅ Limpeza automática de alertas antigos (90 dias)

---

## ⚙️ Configuração

### **1. Configurar Organization**

No Django Admin, configure os alertas para cada organization:

```python
organization.alert_enabled = True  # Habilitar alertas
organization.alert_email = 'admin@empresa.com'  # Email de destino
organization.alert_threshold_80 = True  # Alerta em 80%
organization.alert_threshold_100 = True  # Alerta em 100%
```

### **2. Configurar Celery Beat**

Adicionar task periódica no `celery.py` ou `settings.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-quota-alerts': {
        'task': 'apps.core.tasks.check_quota_alerts',
        'schedule': crontab(minute=0),  # A cada hora
    },
    'cleanup-old-alerts': {
        'task': 'apps.core.tasks.cleanup_old_quota_alerts',
        'schedule': crontab(hour=3, minute=0),  # Diariamente às 3h
    },
}
```

### **3. Configurar Email**

Em `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha-app'
DEFAULT_FROM_EMAIL = 'IAMKT <noreply@iamkt.com>'
```

---

## 📧 Tipos de Alertas

### **1. Alerta de 80% (Aviso)**

**Assunto:** `⚠️ Alerta: Quota de [Tipo] em 80% - [Organization]`

**Quando:** Uso atinge 80% do limite

**Ação:** Monitorar e planejar

**Exemplo:**
```
⚠️ Alerta: Quota de Posts Diários em 80% - IAMKT

ATENÇÃO: A quota de Posts Diários da organização IAMKT está em 85.0%.

Detalhes:
- Tipo: Posts Diários
- Uso atual: 17
- Limite: 20
- Percentual: 85.0%
- Data: 20/01/2026

⚠️ A quota está próxima do limite. Considere ajustar ou aguardar renovação.
```

### **2. Alerta de 100% (Crítico)**

**Assunto:** `⚠️ ALERTA: Quota de [Tipo] ESGOTADA - [Organization]`

**Quando:** Uso atinge 100% do limite

**Ação:** Ação imediata necessária

**Exemplo:**
```
⚠️ ALERTA: Quota de Posts Diários ESGOTADA - IAMKT

CRÍTICO: A quota de Posts Diários da organização IAMKT está ESGOTADA (100%).

Detalhes:
- Tipo: Posts Diários
- Uso atual: 20
- Limite: 20
- Percentual: 100.0%
- Data: 20/01/2026

⚠️ A quota foi totalmente utilizada. Novas criações podem ser bloqueadas.
```

---

## 🔄 Fluxo de Funcionamento

```
1. Celery Beat executa check_quota_alerts() a cada hora
   ↓
2. Para cada organization ativa com alertas habilitados:
   ↓
3. Buscar uso diário (QuotaUsageDaily de hoje)
   ↓
4. Buscar uso mensal (soma do mês atual)
   ↓
5. Para cada tipo de quota (pautas_dia, posts_dia, posts_mes, cost_mes):
   ↓
6. Calcular percentual de uso
   ↓
7. Se >= 100% e threshold_100 habilitado:
   → Verificar se alerta já foi enviado hoje
   → Se não, enviar email e registrar em QuotaAlert
   ↓
8. Se >= 80% e threshold_80 habilitado:
   → Verificar se alerta já foi enviado hoje
   → Se não, enviar email e registrar em QuotaAlert
```

---

## 🛡️ Prevenção de Duplicatas

O sistema garante que **não envia alertas duplicados** no mesmo dia:

```python
def alert_already_sent(org, alert_type, threshold, date):
    """Verificar se alerta já foi enviado hoje"""
    return QuotaAlert.objects.filter(
        organization=org,
        alert_type=alert_type,
        threshold_percentage=threshold,
        sent_at__date=date
    ).exists()
```

**Exemplo:**
- 10h: Uso atinge 80% → Alerta enviado ✅
- 11h: Uso ainda em 80% → Alerta NÃO enviado (já foi enviado hoje)
- 14h: Uso atinge 100% → Novo alerta enviado ✅ (threshold diferente)

---

## 📊 Monitoramento

### **Ver Alertas Enviados**

No Django Admin → `Quota Alerts`:

- Filtrar por organization
- Filtrar por tipo de alerta
- Filtrar por threshold
- Ver histórico completo

### **Verificar Uso Atual**

```python
from apps.core.models import Organization, QuotaUsageDaily
from django.utils import timezone

org = Organization.objects.get(slug='iamkt')
today = timezone.now().date()

usage = QuotaUsageDaily.objects.get(organization=org, date=today)
print(f"Pautas hoje: {usage.pautas_count}/{org.quota_pautas_dia}")
print(f"Posts hoje: {usage.posts_count}/{org.quota_posts_dia}")
```

---

## 🧪 Testes

### **Testar Envio de Alerta Manualmente**

```python
from apps.core.tasks import check_quota_alerts

# Executar verificação manualmente
result = check_quota_alerts()
print(result)  # "Alertas verificados: 2 enviados"
```

### **Simular Uso Alto**

```python
from apps.core.models import Organization, QuotaUsageDaily
from django.utils import timezone

org = Organization.objects.get(slug='iamkt')
today = timezone.now().date()

# Criar uso alto para testar alertas
usage, created = QuotaUsageDaily.objects.get_or_create(
    organization=org,
    date=today,
    defaults={
        'pautas_count': 18,  # 90% de 20
        'posts_count': 18,   # 90% de 20
        'cost_usd': 90.0     # 90% de 100
    }
)

# Executar verificação
from apps.core.tasks import check_quota_alerts
check_quota_alerts()
```

---

## 🔧 Troubleshooting

### **Alertas não estão sendo enviados**

1. **Verificar se Celery está rodando:**
   ```bash
   docker compose logs celery
   ```

2. **Verificar se Celery Beat está rodando:**
   ```bash
   docker compose logs celery-beat
   ```

3. **Verificar configuração da organization:**
   ```python
   org = Organization.objects.get(slug='iamkt')
   print(f"Alertas habilitados: {org.alert_enabled}")
   print(f"Email: {org.alert_email}")
   print(f"Threshold 80: {org.alert_threshold_80}")
   print(f"Threshold 100: {org.alert_threshold_100}")
   ```

4. **Verificar configuração de email:**
   ```python
   from django.core.mail import send_mail
   
   send_mail(
       'Teste',
       'Mensagem de teste',
       'noreply@iamkt.com',
       ['seu-email@gmail.com'],
   )
   ```

### **Alertas duplicados**

- Verificar se `alert_already_sent()` está funcionando
- Verificar registros em `QuotaAlert`
- Limpar alertas do dia se necessário:
  ```python
  from apps.core.models import QuotaAlert
  from django.utils import timezone
  
  today = timezone.now().date()
  QuotaAlert.objects.filter(sent_at__date=today).delete()
  ```

### **Limpeza de alertas antigos não funciona**

```python
from apps.core.tasks import cleanup_old_quota_alerts

# Executar manualmente
result = cleanup_old_quota_alerts(days=90)
print(result)
```

---

## 📈 Boas Práticas

1. **Configurar emails válidos:** Sempre configurar `alert_email` para cada organization

2. **Monitorar regularmente:** Verificar dashboard e QuotaAlert periodicamente

3. **Ajustar quotas proativamente:** Ao receber alerta de 80%, considerar ajuste

4. **Testar antes de produção:** Sempre testar envio de emails em staging

5. **Manter histórico:** Não deletar QuotaAlert muito cedo (mínimo 90 dias)

---

## 🚀 Próximos Passos

- [ ] Adicionar alertas via Slack/Discord
- [ ] Dashboard de alertas em tempo real
- [ ] Relatórios mensais de uso
- [ ] Alertas preditivos (baseado em tendência)
- [ ] Notificações in-app (além de email)

---

**Sistema de Alertas implementado e pronto para uso! 🎉**
