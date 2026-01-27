"""
Views para upload de arquivos usando S3 Presigned URLs
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from apps.core.services import S3Service, ImageProcessor
from apps.knowledge.models import Logo, ReferenceImage, KnowledgeBase
import json


# ============================================
# UPLOAD DE LOGOS
# ============================================

@login_required
@require_http_methods(["POST"])
def generate_logo_upload_url(request):
    """
    Gera Presigned URL para upload de logo
    
    POST params:
        - fileName: Nome do arquivo
        - fileType: MIME type
        - fileSize: Tamanho em bytes
        - logoType: Tipo do logo (principal, horizontal, etc)
    
    Returns:
        {
            'success': bool,
            'data': {
                'upload_url': str,
                's3_key': str,
                'bucket': str,
                'expires_in': int
            }
        }
    """
    try:
        # Obter organização do usuário
        organization = request.organization
        
        # Validar parâmetros
        file_name = request.POST.get('fileName')
        file_type = request.POST.get('fileType')
        file_size = request.POST.get('fileSize')
        logo_type = request.POST.get('logoType', 'principal')
        
        if not all([file_name, file_type, file_size]):
            return JsonResponse({
                'success': False,
                'error': 'Parâmetros obrigatórios: fileName, fileType, fileSize'
            }, status=400)
        
        # Gerar Presigned URL
        result = S3Service.generate_presigned_upload_url(
            file_type='logo',
            file_name=file_name,
            mime_type=file_type,
            file_size=int(file_size),
            organization_id=organization.id,
            custom_data={'logo_type': logo_type},
            metadata={
                'user-id': str(request.user.id),
                'logo-type': logo_type,
            }
        )
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de upload'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def create_logo(request):
    """
    Cria registro de Logo após upload bem-sucedido no S3
    
    POST params:
        - name: Nome do logo
        - logoType: Tipo do logo
        - s3Key: Chave do arquivo no S3
        - fileFormat: Formato do arquivo (png, svg, jpg)
        - isPrimary: Se é logo principal (opcional)
    
    Returns:
        {
            'success': bool,
            'data': {
                'id': int,
                'name': str,
                'preview_url': str,
                'logo_type': str
            }
        }
    """
    try:
        # Obter organização e knowledge base
        organization = request.organization
        kb = KnowledgeBase.objects.filter(organization=organization).first()
        
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Validar parâmetros
        name = request.POST.get('name')
        logo_type = request.POST.get('logoType')
        s3_key = request.POST.get('s3Key')
        file_format = request.POST.get('fileFormat')
        is_primary = request.POST.get('isPrimary', 'false').lower() == 'true'
        
        if not all([name, logo_type, s3_key, file_format]):
            return JsonResponse({
                'success': False,
                'error': 'Parâmetros obrigatórios: name, logoType, s3Key, fileFormat'
            }, status=400)
        
        # Se é logo principal, desmarcar outros
        if is_primary:
            Logo.objects.filter(knowledge_base=kb, is_primary=True).update(is_primary=False)
        
        # Criar registro do logo
        logo = Logo.objects.create(
            knowledge_base=kb,
            name=name,
            logo_type=logo_type,
            s3_key=s3_key,
            s3_url=S3Service.get_file_url(s3_key, organization.id),
            file_format=file_format,
            is_primary=is_primary,
            uploaded_by=request.user
        )
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(
            s3_key=s3_key,
            organization_id=organization.id,
            url_type='preview'
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': logo.id,
                'name': logo.name,
                'logo_type': logo.logo_type,
                'preview_url': preview_url,
                'is_primary': logo.is_primary
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar logo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def get_logo_preview_url(request):
    """
    Gera Presigned URL para preview de logo existente
    
    POST params:
        - logoId: ID do logo
    
    Returns:
        {
            'success': bool,
            'data': {
                'preview_url': str,
                'expires_in': int
            }
        }
    """
    try:
        organization = request.organization
        logo_id = request.POST.get('logoId')
        
        if not logo_id:
            return JsonResponse({
                'success': False,
                'error': 'logoId é obrigatório'
            }, status=400)
        
        # Buscar logo
        logo = Logo.objects.filter(
            id=logo_id,
            knowledge_base__organization=organization
        ).first()
        
        if not logo:
            return JsonResponse({
                'success': False,
                'error': 'Logo não encontrado'
            }, status=404)
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(
            s3_key=logo.s3_key,
            organization_id=organization.id,
            url_type='preview'
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'preview_url': preview_url,
                'expires_in': S3Service.PRESIGNED_URL_EXPIRATION['preview']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de preview'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_logo(request, logo_id):
    """
    Deleta logo do banco e do S3
    
    URL params:
        - logo_id: ID do logo
    
    Returns:
        {
            'success': bool,
            'message': str
        }
    """
    try:
        organization = request.organization
        
        # Buscar logo
        logo = Logo.objects.filter(
            id=logo_id,
            knowledge_base__organization=organization
        ).first()
        
        if not logo:
            return JsonResponse({
                'success': False,
                'error': 'Logo não encontrado'
            }, status=404)
        
        # Deletar do S3
        s3_key = logo.s3_key
        S3Service.delete_file(s3_key, organization.id)
        
        # Deletar do banco
        logo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Logo deletado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar logo'
        }, status=500)


# ============================================
# UPLOAD DE IMAGENS DE REFERÊNCIA
# ============================================

@login_required
@require_http_methods(["POST"])
def generate_reference_upload_url(request):
    """
    Gera Presigned URL para upload de imagem de referência
    
    POST params:
        - fileName: Nome do arquivo
        - fileType: MIME type
        - fileSize: Tamanho em bytes
    
    Returns:
        {
            'success': bool,
            'data': {
                'upload_url': str,
                's3_key': str,
                'bucket': str,
                'expires_in': int
            }
        }
    """
    try:
        organization = request.organization
        
        # Validar parâmetros
        file_name = request.POST.get('fileName')
        file_type = request.POST.get('fileType')
        file_size = request.POST.get('fileSize')
        
        if not all([file_name, file_type, file_size]):
            return JsonResponse({
                'success': False,
                'error': 'Parâmetros obrigatórios: fileName, fileType, fileSize'
            }, status=400)
        
        # Gerar Presigned URL
        result = S3Service.generate_presigned_upload_url(
            file_type='reference',
            file_name=file_name,
            mime_type=file_type,
            file_size=int(file_size),
            organization_id=organization.id,
            metadata={
                'user-id': str(request.user.id),
            }
        )
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de upload'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def create_reference(request):
    """
    Cria registro de ReferenceImage após upload bem-sucedido no S3
    
    POST params:
        - title: Título da imagem
        - description: Descrição (opcional)
        - s3Key: Chave do arquivo no S3
        - fileSize: Tamanho do arquivo em bytes
        - width: Largura da imagem
        - height: Altura da imagem
        - perceptualHash: Hash perceptual (opcional)
    
    Returns:
        {
            'success': bool,
            'data': {
                'id': int,
                'title': str,
                'preview_url': str
            }
        }
    """
    try:
        organization = request.organization
        kb = KnowledgeBase.objects.filter(organization=organization).first()
        
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Validar parâmetros
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        s3_key = request.POST.get('s3Key')
        file_size = request.POST.get('fileSize')
        width = request.POST.get('width')
        height = request.POST.get('height')
        perceptual_hash = request.POST.get('perceptualHash', '')
        
        if not all([title, s3_key, file_size, width, height]):
            return JsonResponse({
                'success': False,
                'error': 'Parâmetros obrigatórios: title, s3Key, fileSize, width, height'
            }, status=400)
        
        # Criar registro da imagem
        reference = ReferenceImage.objects.create(
            knowledge_base=kb,
            title=title,
            description=description,
            s3_key=s3_key,
            s3_url=S3Service.get_file_url(s3_key, organization.id),
            file_size=int(file_size),
            width=int(width),
            height=int(height),
            perceptual_hash=perceptual_hash,
            uploaded_by=request.user
        )
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(
            s3_key=s3_key,
            organization_id=organization.id,
            url_type='preview'
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': reference.id,
                'title': reference.title,
                'preview_url': preview_url,
                'width': reference.width,
                'height': reference.height
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao criar imagem de referência: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def get_reference_preview_url(request):
    """
    Gera Presigned URL para preview de imagem de referência existente
    
    POST params:
        - referenceId: ID da imagem
    
    Returns:
        {
            'success': bool,
            'data': {
                'preview_url': str,
                'expires_in': int
            }
        }
    """
    try:
        organization = request.organization
        reference_id = request.POST.get('referenceId')
        
        if not reference_id:
            return JsonResponse({
                'success': False,
                'error': 'referenceId é obrigatório'
            }, status=400)
        
        # Buscar imagem
        reference = ReferenceImage.objects.filter(
            id=reference_id,
            knowledge_base__organization=organization
        ).first()
        
        if not reference:
            return JsonResponse({
                'success': False,
                'error': 'Imagem não encontrada'
            }, status=404)
        
        # Gerar URL de preview
        preview_url = S3Service.generate_presigned_download_url(
            s3_key=reference.s3_key,
            organization_id=organization.id,
            url_type='preview'
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'preview_url': preview_url,
                'expires_in': S3Service.PRESIGNED_URL_EXPIRATION['preview']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar URL de preview'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_reference(request, reference_id):
    """
    Deleta imagem de referência do banco e do S3
    
    URL params:
        - reference_id: ID da imagem
    
    Returns:
        {
            'success': bool,
            'message': str
        }
    """
    try:
        organization = request.organization
        
        # Buscar imagem
        reference = ReferenceImage.objects.filter(
            id=reference_id,
            knowledge_base__organization=organization
        ).first()
        
        if not reference:
            return JsonResponse({
                'success': False,
                'error': 'Imagem não encontrada'
            }, status=404)
        
        # Deletar do S3
        s3_key = reference.s3_key
        S3Service.delete_file(s3_key, organization.id)
        
        # Deletar do banco
        reference.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagem deletada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao deletar imagem'
        }, status=500)
