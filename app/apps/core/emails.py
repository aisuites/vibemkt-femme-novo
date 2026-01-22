"""
Sistema de Emails - IAMKT
Funções para envio de emails transacionais e notificações
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def get_notification_emails(group='operacao'):
    """
    Retorna lista de emails para notificação baseado no grupo
    
    Grupos disponíveis:
    - gestao: Notificações estratégicas e aprovações
    - operacao: Notificações operacionais e novos cadastros
    - posts: Notificações sobre posts criados
    - newuser: Compatibilidade com app antiga (novos usuários)
    """
    env_key = f'NOTIFICATION_EMAILS_{group.upper()}'
    emails_str = getattr(settings, env_key, '')
    
    if not emails_str:
        logger.warning(f'Nenhum email configurado para o grupo: {group}')
        return []
    
    # Separar por vírgula e remover espaços
    emails = [email.strip() for email in emails_str.split(',') if email.strip()]
    return emails


def send_registration_confirmation(user, organization):
    """
    Envia email de confirmação de cadastro para o usuário
    
    Args:
        user: Instância do User
        organization: Instância da Organization
    """
    subject = 'Cadastro realizado com sucesso - IAMKT'
    
    context = {
        'user_name': user.first_name or user.email.split('@')[0],
        'user_email': user.email,
        'organization_name': organization.name,
    }
    
    # Renderizar template HTML
    html_message = render_to_string('emails/registration_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email de confirmação enviado para: {user.email}')
        return True
    except Exception as e:
        logger.error(f'Erro ao enviar email de confirmação para {user.email}: {str(e)}')
        return False


def send_registration_notification(user, organization):
    """
    Envia email de notificação para equipe IAMKT sobre novo cadastro
    
    Args:
        user: Instância do User
        organization: Instância da Organization
    """
    # Buscar emails dos grupos operacao e newuser (compatibilidade)
    recipients = list(set(
        get_notification_emails('operacao') + 
        get_notification_emails('newuser')
    ))
    
    if not recipients:
        logger.warning('Nenhum destinatário configurado para notificações de novos usuários')
        return False
    
    subject = '[IAMKT] Novo cadastro aguardando aprovação'
    
    context = {
        'user_name': f"{user.first_name} {user.last_name}".strip() or user.email,
        'user_email': user.email,
        'organization_name': organization.name,
        'created_at': organization.created_at,
        'admin_url': f"{settings.SITE_URL}/admin/core/organization/{organization.id}/change/",
    }
    
    # Renderizar template HTML
    html_message = render_to_string('emails/registration_notification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email de notificação enviado para: {", ".join(recipients)}')
        return True
    except Exception as e:
        logger.error(f'Erro ao enviar email de notificação: {str(e)}')
        return False


def send_approval_email(user, organization, plan_type):
    """
    Envia email de aprovação para o usuário (futuro)
    
    Args:
        user: Instância do User
        organization: Instância da Organization
        plan_type: Tipo de plano aprovado
    """
    subject = 'Sua conta IAMKT foi aprovada! 🎉'
    
    context = {
        'user_name': user.first_name or user.email.split('@')[0],
        'organization_name': organization.name,
        'user_email': user.email,
        'plan_type': organization.get_plan_type_display(),
        'login_url': f"{settings.SITE_URL}/login/",
    }
    
    # Renderizar template HTML
    html_message = render_to_string('emails/approval_notification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email de aprovação enviado para: {user.email}')
        return True
    except Exception as e:
        logger.error(f'Erro ao enviar email de aprovação para {user.email}: {str(e)}')
        return False
