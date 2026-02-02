from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Post


@login_required
def posts_list(request):
    """
    Lista de posts com filtros e paginação
    """
    # Filtrar posts da organização do usuário
    posts = Post.objects.filter(organization=request.user.organization)
    
    # Aplicar filtros
    filtros = {}
    
    # Filtro por data
    data = request.GET.get('data')
    if data:
        posts = posts.filter(created_at__date=data)
        filtros['data'] = data
    
    # Filtro por status
    status = request.GET.get('status')
    if status and status != 'all':
        posts = posts.filter(status=status)
        filtros['status'] = status
    
    # Filtro por busca (título)
    search = request.GET.get('search')
    if search:
        posts = posts.filter(title__icontains=search)
        filtros['search'] = search
    
    # Paginação
    paginator = Paginator(posts, 10)  # 10 posts por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Verificar se tem knowledge base
    knowledge_base = hasattr(request.user.organization, 'knowledge_base')
    
    # Preparar dados para JavaScript
    import json
    posts_json = []
    for post in page_obj:
        posts_json.append({
            'id': post.id,
            'title': post.title or '',
            'subtitle': post.subtitle or '',
            'caption': post.caption or '',
            'status': post.status,
            'social_network': post.social_network,
            'created_at': post.created_at.isoformat(),
            'has_image': bool(post.has_image),  # Garantir que é booleano
        })
    
    # Converter para JSON string para passar ao template
    posts_json = json.dumps(posts_json)
    
    context = {
        'page_obj': page_obj,
        'filtros': filtros,
        'knowledge_base': knowledge_base,
        'posts_json': posts_json,
        'posts_webhook_url': '',  # TODO: Configurar webhook URL
    }
    
    return render(request, 'posts/posts_list.html', context)
