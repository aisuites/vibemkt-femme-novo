"""
Views para deletar recursos da Knowledge Base
"""

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from apps.knowledge.models import Logo, ReferenceImage, CustomFont
from apps.core.services import S3Service


@login_required
@require_http_methods(["DELETE"])
def delete_logo(request, logo_id):
    """
    Deleta logo do banco e do S3
    
    URL params:
        - logo_id: ID do logo
    
    Returns:
        {'success': bool}
    """
    try:
        organization = request.organization
        
        logo = Logo.objects.get(
            id=logo_id,
            knowledge_base__organization=organization
        )
        
        # Deletar do S3
        if logo.s3_key:
            S3Service.delete_file(logo.s3_key)
        
        # Deletar do banco
        logo.delete()
        
        return JsonResponse({'success': True})
        
    except Logo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Logo não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar logo'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_reference_image(request, reference_id):
    """
    Deleta imagem de referência do banco e do S3
    
    URL params:
        - reference_id: ID da imagem de referência
    
    Returns:
        {'success': bool}
    """
    try:
        organization = request.organization
        
        reference = ReferenceImage.objects.get(
            id=reference_id,
            knowledge_base__organization=organization
        )
        
        # Deletar do S3
        if reference.s3_key:
            S3Service.delete_file(reference.s3_key)
        
        # Deletar do banco
        reference.delete()
        
        return JsonResponse({'success': True})
        
    except ReferenceImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Imagem de referência não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar imagem de referência'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_custom_font(request, font_id):
    """
    Deleta fonte customizada do banco e do S3
    
    URL params:
        - font_id: ID da fonte
    
    Returns:
        {'success': bool}
    """
    try:
        organization = request.organization
        
        font = CustomFont.objects.get(
            id=font_id,
            knowledge_base__organization=organization
        )
        
        # Deletar do S3
        if font.s3_key:
            S3Service.delete_file(font.s3_key)
        
        # Deletar do banco
        font.delete()
        
        return JsonResponse({'success': True})
        
    except CustomFont.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Fonte não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar fonte'
        }, status=500)
