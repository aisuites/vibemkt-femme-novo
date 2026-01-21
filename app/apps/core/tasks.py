"""
IAMKT - Celery Tasks para Core

Tasks assíncronas para monitoramento de quotas e envio de alertas.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal

from apps.core.models import Organization, QuotaUsageDaily, QuotaAlert


@shared_task
def check_quota_alerts():
    """
    Task periódica que verifica uso de quotas e envia alertas.
    Deve ser executada a cada hora via Celery Beat.
    """
    today = timezone.now().date()
    organizations = Organization.objects.filter(
        is_active=True,
        alert_enabled=True
    )
    
    alerts_sent = 0
    
    for org in organizations:
        # Verificar alertas diários
        alerts_sent += check_daily_quota_alerts(org, today)
        
        # Verificar alertas mensais
        alerts_sent += check_monthly_quota_alerts(org, today)
    
    return f"Alertas verificados: {alerts_sent} enviados"


def check_daily_quota_alerts(org, today):
    """Verificar alertas de quotas diárias (pautas e posts)"""
    alerts_sent = 0
    
    # Buscar uso de hoje
    try:
        usage = QuotaUsageDaily.objects.get(organization=org, date=today)
    except QuotaUsageDaily.DoesNotExist:
        return 0
    
    # Verificar Pautas Diárias
    if org.quota_pautas_dia > 0:
        percentage = (usage.pautas_count / org.quota_pautas_dia) * 100
        
        if percentage >= 100 and org.alert_threshold_100:
            if not alert_already_sent(org, 'pautas_dia', 100, today):
                send_quota_alert(
                    org=org,
                    alert_type='pautas_dia',
                    threshold=100,
                    current=usage.pautas_count,
                    limit=org.quota_pautas_dia,
                    date=today
                )
                alerts_sent += 1
        
        elif percentage >= 80 and org.alert_threshold_80:
            if not alert_already_sent(org, 'pautas_dia', 80, today):
                send_quota_alert(
                    org=org,
                    alert_type='pautas_dia',
                    threshold=80,
                    current=usage.pautas_count,
                    limit=org.quota_pautas_dia,
                    date=today
                )
                alerts_sent += 1
    
    # Verificar Posts Diários
    if org.quota_posts_dia > 0:
        percentage = (usage.posts_count / org.quota_posts_dia) * 100
        
        if percentage >= 100 and org.alert_threshold_100:
            if not alert_already_sent(org, 'posts_dia', 100, today):
                send_quota_alert(
                    org=org,
                    alert_type='posts_dia',
                    threshold=100,
                    current=usage.posts_count,
                    limit=org.quota_posts_dia,
                    date=today
                )
                alerts_sent += 1
        
        elif percentage >= 80 and org.alert_threshold_80:
            if not alert_already_sent(org, 'posts_dia', 80, today):
                send_quota_alert(
                    org=org,
                    alert_type='posts_dia',
                    threshold=80,
                    current=usage.posts_count,
                    limit=org.quota_posts_dia,
                    date=today
                )
                alerts_sent += 1
    
    return alerts_sent


def check_monthly_quota_alerts(org, today):
    """Verificar alertas de quotas mensais (posts e custo)"""
    alerts_sent = 0
    
    # Calcular uso do mês
    first_day = today.replace(day=1)
    usage_month = QuotaUsageDaily.objects.filter(
        organization=org,
        date__gte=first_day,
        date__lte=today
    ).aggregate(
        total_posts=Sum('posts_count'),
        total_cost=Sum('cost_usd')
    )
    
    posts_mes = usage_month['total_posts'] or 0
    cost_mes = float(usage_month['total_cost'] or 0)
    
    # Verificar Posts Mensais
    if org.quota_posts_mes > 0:
        percentage = (posts_mes / org.quota_posts_mes) * 100
        
        if percentage >= 100 and org.alert_threshold_100:
            if not alert_already_sent(org, 'posts_mes', 100, today):
                send_quota_alert(
                    org=org,
                    alert_type='posts_mes',
                    threshold=100,
                    current=posts_mes,
                    limit=org.quota_posts_mes,
                    date=today
                )
                alerts_sent += 1
        
        elif percentage >= 80 and org.alert_threshold_80:
            if not alert_already_sent(org, 'posts_mes', 80, today):
                send_quota_alert(
                    org=org,
                    alert_type='posts_mes',
                    threshold=80,
                    current=posts_mes,
                    limit=org.quota_posts_mes,
                    date=today
                )
                alerts_sent += 1
    
    # Verificar Custo Mensal
    if org.quota_cost_mes_usd and org.quota_cost_mes_usd > 0:
        percentage = (cost_mes / float(org.quota_cost_mes_usd)) * 100
        
        if percentage >= 100 and org.alert_threshold_100:
            if not alert_already_sent(org, 'cost_mes', 100, today):
                send_quota_alert(
                    org=org,
                    alert_type='cost_mes',
                    threshold=100,
                    current=cost_mes,
                    limit=float(org.quota_cost_mes_usd),
                    date=today
                )
                alerts_sent += 1
        
        elif percentage >= 80 and org.alert_threshold_80:
            if not alert_already_sent(org, 'cost_mes', 80, today):
                send_quota_alert(
                    org=org,
                    alert_type='cost_mes',
                    threshold=80,
                    current=cost_mes,
                    limit=float(org.quota_cost_mes_usd),
                    date=today
                )
                alerts_sent += 1
    
    return alerts_sent


def alert_already_sent(org, alert_type, threshold, date):
    """Verificar se alerta já foi enviado hoje para evitar duplicatas"""
    return QuotaAlert.objects.filter(
        organization=org,
        alert_type=alert_type,
        threshold_percentage=threshold,
        sent_at__date=date
    ).exists()


def send_quota_alert(org, alert_type, threshold, current, limit, date):
    """Enviar email de alerta de quota"""
    
    # Mapear tipos de alerta para nomes legíveis
    alert_names = {
        'pautas_dia': 'Pautas Diárias',
        'posts_dia': 'Posts Diários',
        'posts_mes': 'Posts Mensais',
        'cost_mes': 'Custo Mensal (USD)'
    }
    
    alert_name = alert_names.get(alert_type, alert_type)
    percentage = (current / limit * 100) if limit > 0 else 0
    
    # Definir assunto e mensagem
    if threshold >= 100:
        subject = f'⚠️ ALERTA: Quota de {alert_name} ESGOTADA - {org.name}'
        status = 'ESGOTADA (100%)'
        urgency = 'CRÍTICO'
    else:
        subject = f'⚠️ Alerta: Quota de {alert_name} em {threshold}% - {org.name}'
        status = f'em {percentage:.1f}%'
        urgency = 'ATENÇÃO'
    
    # Formatar valores
    if 'cost' in alert_type:
        current_str = f'${current:.2f}'
        limit_str = f'${limit:.2f}'
    else:
        current_str = str(int(current))
        limit_str = str(int(limit))
    
    # Compor mensagem
    message = f"""
Olá,

{urgency}: A quota de {alert_name} da organização {org.name} está {status}.

Detalhes:
- Tipo: {alert_name}
- Uso atual: {current_str}
- Limite: {limit_str}
- Percentual: {percentage:.1f}%
- Data: {date.strftime('%d/%m/%Y')}

{'⚠️ A quota foi totalmente utilizada. Novas criações podem ser bloqueadas.' if threshold >= 100 else '⚠️ A quota está próxima do limite. Considere ajustar ou aguardar renovação.'}

---
Sistema IAMKT - Alertas de Quota
    """.strip()
    
    # Email de destino
    email_to = org.alert_email or settings.DEFAULT_FROM_EMAIL
    
    # Enviar email
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_to],
            fail_silently=False,
        )
        
        # Registrar alerta enviado
        QuotaAlert.objects.create(
            organization=org,
            alert_type=alert_type,
            threshold_percentage=threshold,
            current_usage=Decimal(str(current)),
            quota_limit=Decimal(str(limit)),
            email_sent_to=email_to
        )
        
        return True
    
    except Exception as e:
        # Log do erro (em produção, usar logging adequado)
        print(f"Erro ao enviar alerta para {org.name}: {e}")
        return False


@shared_task
def cleanup_old_quota_alerts(days=90):
    """
    Limpar alertas antigos para evitar acúmulo no banco.
    Manter apenas últimos 90 dias por padrão.
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    deleted_count = QuotaAlert.objects.filter(sent_at__lt=cutoff_date).delete()[0]
    return f"Alertas antigos removidos: {deleted_count}"
