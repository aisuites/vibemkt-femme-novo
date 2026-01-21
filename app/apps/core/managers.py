"""
IAMKT - Tenant-Aware Managers

Managers customizados que filtram automaticamente por organization.
Garante isolamento de tenant em todas as queries.
"""
from django.db import models
from django.db.models import Q


class TenantManager(models.Manager):
    """
    Manager que filtra automaticamente por organization.
    
    Uso:
        class MyModel(models.Model):
            organization = models.ForeignKey(Organization, ...)
            objects = TenantManager()
    
    Queries automáticas:
        MyModel.objects.all()  # Filtra por request.organization automaticamente
        MyModel.objects.filter(...)  # Também filtra por organization
    
    Queries sem filtro (use com cuidado!):
        MyModel.objects.all_tenants()  # Retorna TODOS os registros
    """
    
    def __init__(self, *args, **kwargs):
        self._organization = None
        super().__init__(*args, **kwargs)
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por organization.
        """
        qs = super().get_queryset()
        
        # Se organization foi definida, filtrar
        if self._organization:
            return qs.filter(organization=self._organization)
        
        return qs
    
    def for_organization(self, organization):
        """
        Define organization para filtro.
        
        Uso:
            MyModel.objects.for_organization(org).all()
        """
        manager = self._clone()
        manager._organization = organization
        return manager
    
    def all_tenants(self):
        """
        Retorna TODOS os registros, sem filtro de tenant.
        
        ⚠️ USE COM CUIDADO! Apenas para:
        - Tarefas administrativas
        - Migrations
        - Relatórios globais
        
        Uso:
            MyModel.objects.all_tenants()
        """
        return super().get_queryset()
    
    def _clone(self):
        """
        Clona o manager mantendo configurações.
        """
        manager = self.__class__()
        manager._organization = self._organization
        manager.model = self.model
        return manager


class TenantQuerySet(models.QuerySet):
    """
    QuerySet que mantém filtro de tenant em operações encadeadas.
    """
    
    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
    
    def for_organization(self, organization):
        """
        Define organization para filtro.
        """
        clone = self._clone()
        clone._organization = organization
        if organization:
            clone = clone.filter(organization=organization)
        return clone
    
    def all_tenants(self):
        """
        Remove filtro de tenant.
        """
        clone = self._clone()
        clone._organization = None
        return clone


class TenantManagerWithQuerySet(models.Manager):
    """
    Manager que usa TenantQuerySet.
    
    Combina funcionalidades de Manager e QuerySet.
    """
    
    def get_queryset(self):
        """
        Retorna TenantQuerySet.
        """
        return TenantQuerySet(self.model, using=self._db)
    
    def for_organization(self, organization):
        """
        Filtra por organization.
        """
        return self.get_queryset().for_organization(organization)
    
    def all_tenants(self):
        """
        Retorna todos os registros sem filtro.
        """
        return self.get_queryset().all_tenants()


# Atalho para facilitar uso
TenantAwareManager = TenantManagerWithQuerySet


class OrganizationScopedManager(models.Manager):
    """
    Manager para models que SEMPRE devem filtrar por organization.
    
    Diferente do TenantManager, este NUNCA retorna dados sem organization.
    Ideal para models críticas como Post, Pauta, etc.
    """
    
    def get_queryset(self):
        """
        Retorna apenas registros com organization definida.
        """
        return super().get_queryset().exclude(organization__isnull=True)
    
    def for_organization(self, organization):
        """
        Filtra por organization específica.
        """
        return self.get_queryset().filter(organization=organization)
    
    def for_request(self, request):
        """
        Filtra pela organization do request.
        
        Uso em views:
            posts = Post.objects.for_request(request)
        """
        if not hasattr(request, 'organization') or not request.organization:
            return self.get_queryset().none()
        
        return self.for_organization(request.organization)
    
    def all_tenants(self):
        """
        Acesso administrativo a todos os tenants.
        """
        return self.model._default_manager.all()


def get_tenant_from_request(request):
    """
    Utilitário para extrair organization do request.
    
    Uso:
        org = get_tenant_from_request(request)
        posts = Post.objects.for_organization(org)
    """
    if hasattr(request, 'organization'):
        return request.organization
    return None
