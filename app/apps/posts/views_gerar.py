"""
Views para geração de posts
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from apps.posts.models import Post
import json


@login_required
@require_http_methods(["POST"])
def gerar_post(request):
    """
    Cria um novo Post no banco de dados
    
    POST params (JSON):
        - rede_social: str (instagram, facebook, linkedin, whatsapp)
        - formato: str (feed, stories, both)
        - cta_requested: bool
        - is_carousel: bool
        - image_count: int (2-5)
        - tema: str (required)
        - reference_images: list[dict] (opcional)
    
    Returns:
        {
            'success': bool,
            'data': {
                'post_id': int,
                'message': str
            }
        }
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        
        # Validações
        rede_social = data.get('rede_social')
        formato = data.get('formato', 'feed')
        cta_requested = data.get('cta_requested', True)
        is_carousel = data.get('is_carousel', False)
        image_count = data.get('image_count', 1)
        tema = data.get('tema', '').strip()
        reference_images = data.get('reference_images', [])
        
        # Validar campos obrigatórios
        if not rede_social:
            return JsonResponse({
                'success': False,
                'error': 'Rede social é obrigatória'
            }, status=400)
        
        if not tema:
            return JsonResponse({
                'success': False,
                'error': 'Tema é obrigatório'
            }, status=400)
        
        # Validar rede social
        valid_networks = ['instagram', 'facebook', 'linkedin', 'whatsapp']
        if rede_social not in valid_networks:
            return JsonResponse({
                'success': False,
                'error': f'Rede social inválida. Opções: {", ".join(valid_networks)}'
            }, status=400)
        
        # Validar formato
        valid_formats = ['feed', 'stories', 'both']
        if formato not in valid_formats:
            return JsonResponse({
                'success': False,
                'error': f'Formato inválido. Opções: {", ".join(valid_formats)}'
            }, status=400)
        
        # Validar quantidade de imagens
        if is_carousel:
            if image_count < 2 or image_count > 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Quantidade de imagens deve ser entre 2 e 5'
                }, status=400)
        
        # Preparar formatos (lista)
        if formato == 'both':
            formats = ['feed', 'stories']
        else:
            formats = [formato]
        
        # Determinar content_type baseado no formato
        if is_carousel:
            content_type = 'carrossel'
        elif formato == 'stories':
            content_type = 'story'
        else:
            content_type = 'post'
        
        # Criar Post com transaction
        with transaction.atomic():
            post = Post.objects.create(
                # Multi-tenant - CRÍTICO
                organization=request.user.organization,
                user=request.user,
                
                # Dados do formulário
                requested_theme=tema,
                social_network=rede_social,
                content_type=content_type,
                formats=formats,
                cta_requested=cta_requested,
                is_carousel=is_carousel,
                image_count=image_count if is_carousel else 1,
                reference_images=reference_images,
                
                # Status inicial
                status='draft',
                
                # Campos vazios (serão preenchidos pelo agente)
                caption='',
                hashtags=[],
                ia_provider='openai',
                ia_model_text='gpt-4',
            )
        
        return JsonResponse({
            'success': True,
            'data': {
                'post_id': post.id,
                'message': 'Post criado com sucesso! Aguardando processamento.'
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao criar post: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar post: {str(e)}'
        }, status=500)
