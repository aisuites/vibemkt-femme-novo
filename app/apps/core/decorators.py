"""
IAMKT - Decorators para Tenant Isolation

Decorators para garantir isolamento de tenant em views.
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def require_organization(view_func):
    """
    Decorator que garante que usuário tem organization.
    
    Uso:
        @require_organization
        def my_view(request):
            # request.organization está garantido aqui
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'organization') or not request.organization:
            return HttpResponseForbidden(
                "Acesso negado: Você não está vinculado a nenhuma organização."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def organization_required(redirect_url='/login/'):
    """
    Decorator que redireciona se usuário não tem organization.
    
    Uso:
        @organization_required(redirect_url='/sem-acesso/')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'organization') or not request.organization:
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def tenant_scoped_view(view_func):
    """
    Decorator que adiciona organization ao contexto da view.
    
    Uso:
        @tenant_scoped_view
        def my_view(request):
            org = request.organization  # Garantido
            posts = Post.objects.for_organization(org)
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Garantir que organization existe
        if not hasattr(request, 'organization'):
            request.organization = None
        
        # Adicionar helper para queries
        if request.organization:
            request.tenant = request.organization
        
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_or_organization(view_func):
    """
    Decorator que permite acesso a superusers ou usuários com organization.
    
    Útil para views administrativas.
    
    Uso:
        @superuser_or_organization
        def admin_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Superuser sempre tem acesso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Verificar organization
        if not hasattr(request, 'organization') or not request.organization:
            return HttpResponseForbidden(
                "Acesso negado: Você não está vinculado a nenhuma organização."
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper
