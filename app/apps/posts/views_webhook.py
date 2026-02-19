"""
Views de Webhook para receber dados processados do N8N
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from apps.posts.models import Post

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def n8n_post_callback(request):
    """
    Webhook para receber post processado do N8N
    
    Segurança (seguindo padrão de knowledge/views_n8n.py):
    - Validação de token interno (X-INTERNAL-TOKEN)
    - Validação de IP
    - Rate limiting
    
    Payload esperado do N8N:
    {
        "post_id": 123,
        "status": "pending",  # ou "image_generating", "image_ready", etc
        "titulo": "Post gerado - Instagram",
        "subtitulo": "Subtítulo sugerido",
        "legenda": "Legenda completa do post...",
        "hashtags": ["#pizza", "#gastronomia"],
        "cta": "Visite nosso site!",
        "descricaoImagem": "Prompt para gerar imagem...",
        "imagens": [
            {
                "url": "https://s3.amazonaws.com/...",
                "s3_key": "org-456/posts/2026-02-02/abc123.jpg"
            }
        ]
    }
    """
    
    # CAMADA 1: Validação de Token Interno
    internal_token = request.headers.get('X-INTERNAL-TOKEN')
    
    if internal_token != settings.N8N_WEBHOOK_SECRET:
        logger.warning(
            f"❌ [N8N_POST_CALLBACK] Token inválido do IP: {request.META.get('REMOTE_ADDR')}"
        )
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized'
        }, status=401)
    
    # CAMADA 2: Validação de IP
    # Usar HTTP_CF_CONNECTING_IP pois requisições passam pelo Cloudflare
    client_ip = request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR')
    allowed_ips = settings.N8N_ALLOWED_IPS.split(',')
    
    if client_ip not in allowed_ips:
        logger.warning(
            f"❌ [N8N_POST_CALLBACK] IP não autorizado: {client_ip}"
        )
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized IP'
        }, status=403)
    
    # CAMADA 3: Rate Limiting por IP
    cache_key = f"n8n_post_callback_{client_ip}"
    current_count = cache.get(cache_key, 0)
    
    limit_str = settings.N8N_RATE_LIMIT_PER_IP
    max_requests = int(limit_str.split('/')[0])
    
    if current_count >= max_requests:
        logger.warning(
            f"⚠️ [N8N_POST_CALLBACK] Rate limit excedido para IP {client_ip}"
        )
        return JsonResponse({
            'success': False,
            'error': 'Rate limit exceeded'
        }, status=429)
    
    cache.set(cache_key, current_count + 1, 60)
    
    # CAMADA 4: Validação de JSON
    try:
        data = json.loads(request.body)
        logger.info(f"🔍 [N8N_POST_CALLBACK] Payload recebido - Keys: {list(data.keys())}")
    except json.JSONDecodeError:
        logger.warning("❌ [N8N_POST_CALLBACK] JSON inválido")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    # N8N pode enviar array ou objeto - normalizar para objeto
    if isinstance(data, list):
        if len(data) == 0:
            logger.warning("❌ [N8N_POST_CALLBACK] Array vazio recebido")
            return JsonResponse({
                'success': False,
                'error': 'Empty array received'
            }, status=400)
        data = data[0]
    
    # CAMADA 5: Validação de identificador (post_id ou thread_id)
    post_id = data.get('post_id')
    thread_id = data.get('thread_id')
    
    if not post_id and not thread_id:
        logger.warning("❌ [N8N_POST_CALLBACK] post_id e thread_id ausentes")
        return JsonResponse({
            'success': False,
            'error': 'post_id ou thread_id obrigatório'
        }, status=400)
    
    # CAMADA 6: Buscar Post (por post_id ou thread_id)
    try:
        if post_id:
            post = Post.objects.get(id=post_id)
            logger.info(f"📝 [N8N_POST_CALLBACK] Post {post_id} encontrado por post_id")
        else:
            post = Post.objects.get(thread_id=thread_id)
            logger.info(f"📝 [N8N_POST_CALLBACK] Post {post.id} encontrado por thread_id: {thread_id}")
    except Post.DoesNotExist:
        logger.error(
            f"❌ [N8N_POST_CALLBACK] Post não encontrado - post_id: {post_id}, thread_id: {thread_id}"
        )
        return JsonResponse({
            'success': False,
            'error': f'Post não encontrado'
        }, status=404)
    
    # CAMADA 7: Atualizar Post com dados do N8N
    try:
        logger.info(f"🔍 [N8N_POST_CALLBACK] Atualizando post {post.id} com dados do N8N")
        
        # Atualizar campos de texto (aceitar português e inglês)
        if 'titulo' in data or 'title' in data:
            post.title = data.get('titulo') or data.get('title') or ''
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Título atualizado: {post.title[:50] if post.title else 'vazio'}...")
        
        if 'subtitulo' in data or 'subtitle' in data:
            post.subtitle = data.get('subtitulo') or data.get('subtitle') or ''
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Subtítulo atualizado")
        
        if 'legenda' in data or 'caption' in data:
            post.caption = data.get('legenda') or data.get('caption') or ''
            if post.caption:
                logger.debug(f"✏️ [N8N_POST_CALLBACK] Legenda atualizada: {len(post.caption)} chars")
        
        if 'hashtags' in data:
            post.hashtags = data['hashtags'] if isinstance(data['hashtags'], list) else []
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Hashtags atualizadas: {len(post.hashtags)}")
        
        # CTA - garantir que nunca seja null (campo obrigatório no banco)
        if 'cta' in data or 'cta_text' in data:
            post.cta = data.get('cta') or data.get('cta_text') or ''
            logger.debug(f"✏️ [N8N_POST_CALLBACK] CTA atualizado: {post.cta}")
        
        if 'descricaoImagem' in data or 'image_prompt' in data or 'visual_brief' in data:
            post.image_prompt = data.get('descricaoImagem') or data.get('image_prompt') or data.get('visual_brief') or ''
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Descrição da imagem atualizada")
        
        # Atualizar thread_id (se N8N enviar e post ainda não tiver)
        if 'thread_id' in data and data['thread_id']:
            if not post.thread_id:
                post.thread_id = data['thread_id']
                logger.debug(f"✏️ [N8N_POST_CALLBACK] Thread ID salvo: {post.thread_id}")
            elif post.thread_id != data['thread_id']:
                logger.warning(f"⚠️ [N8N_POST_CALLBACK] Thread ID diferente - Atual: {post.thread_id}, Recebido: {data['thread_id']}")
        
        # Atualizar status (se N8N enviar, usar; senão, mudar de 'generating' para 'pending')
        if 'status' in data:
            post.status = data['status']
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Status atualizado: {post.status}")
        elif post.status == 'generating':
            post.status = 'pending'
            logger.debug(f"✏️ [N8N_POST_CALLBACK] Status mudado de 'generating' para 'pending'")
        
        # Atualizar imagens (se fornecidas)
        if 'imagens' in data and isinstance(data['imagens'], list):
            from apps.posts.models import PostImage
            from urllib.parse import urlparse
            
            imagens_data = data['imagens']
            imagens_processadas = []
            
            for img in imagens_data:
                if isinstance(img, dict) and img.get('url'):
                    imagens_processadas.append(img)
                elif isinstance(img, str) and img:
                    imagens_processadas.append({'url': img})
            
            if imagens_processadas:
                # Remover imagens anteriores geradas automaticamente (manter uploads manuais se necessário)
                PostImage.objects.filter(post=post).delete()
                
                for order, img in enumerate(imagens_processadas):
                    url = img.get('url', '')
                    
                    # s3_key: usar explícita se disponível, senão derivar da URL
                    s3_key = img.get('s3_key', '')
                    if not s3_key and url:
                        parsed = urlparse(url)
                        s3_key = parsed.path.lstrip('/')
                    
                    PostImage.objects.create(
                        post=post,
                        s3_url=url,
                        s3_key=s3_key,
                        order=order,
                    )
                
                # Atualizar campos principais do post com a primeira imagem
                post.image_s3_url = imagens_processadas[0].get('url', '')
                post.image_s3_key = (
                    imagens_processadas[0].get('s3_key', '')
                    or urlparse(post.image_s3_url).path.lstrip('/')
                )
                post.has_image = True
                logger.debug(
                    f"✏️ [N8N_POST_CALLBACK] {len(imagens_processadas)} imagem(ns) salva(s) via PostImage"
                )
        
        # Salvar alterações
        post.save()
        
        logger.info(
            f"✅ [N8N_POST_CALLBACK] Post {post_id} atualizado com sucesso. "
            f"Status: {post.status}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Post {post_id} atualizado com sucesso',
            'post': {
                'id': post.id,
                'status': post.status,
                'titulo': post.title,
                'has_image': post.has_image
            }
        })
        
    except Exception as e:
        logger.exception(
            f"❌ [N8N_POST_CALLBACK] Erro ao processar post {post_id}: {str(e)}"
        )
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar post: {str(e)}'
        }, status=500)
