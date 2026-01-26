from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import require_organization
from .models import Pauta, Post, TrendMonitor


@login_required
@require_organization
def pautas_list(request):
    """Listar pautas da organization"""
    # CRÍTICO: Filtrar explicitamente por organization do request
    pautas = Pauta.objects.for_request(request).order_by('-created_at')
    context = {'pautas': pautas}
    return render(request, 'content/pautas_list.html', context)


@login_required
@require_organization
def pauta_create(request):
    """Criar nova pauta"""
    # TODO: Implementar formulário
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('content:pautas')


@login_required
@require_organization
def posts_list(request):
    """Listar posts da organization"""
    # CRÍTICO: Filtrar explicitamente por organization do request
    posts = Post.objects.for_request(request).order_by('-created_at')
    context = {'posts': posts}
    return render(request, 'content/posts_list.html', context)


@login_required
@require_organization
def post_create(request):
    """Criar novo post"""
    # TODO: Implementar formulário
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('content:posts')


@login_required
@require_organization
def trends_list(request):
    """Listar trends monitoradas da organization"""
    # CRÍTICO: Filtrar explicitamente por organization do request
    trends = TrendMonitor.objects.for_request(request).filter(is_active=True).order_by('-created_at')
    context = {'trends': trends}
    return render(request, 'content/trends_list.html', context)
