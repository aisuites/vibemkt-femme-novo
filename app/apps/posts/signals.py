from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post


@receiver(post_save, sender=Post)
def post_post_save(sender, instance, created, **kwargs):
    """
    Signal executado após salvar um Post
    """
    if created:
        # TODO: Implementar lógica após criação do post
        # Ex: enviar notificação, criar audit log, etc
        pass
