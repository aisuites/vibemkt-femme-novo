"""
Views para gerenciamento de fontes no Perfil da Empresa
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.db import models
import json

from apps.knowledge.models import KnowledgeBase, Typography, CustomFont


@never_cache
@login_required
@require_POST
@csrf_exempt  # TODO: Remover após debug
def perfil_add_font(request):
    """
    Adicionar fonte à tipografia no Perfil
    """
    try:
        data = json.loads(request.body)
        font_source = data.get('font_source', 'google')
        usage = data.get('usage', '').strip()
        
        if not usage:
            return JsonResponse({
                'success': False,
                'error': 'Uso da fonte é obrigatório'
            }, status=400)
        
        kb = KnowledgeBase.objects.for_request(request).first()
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Verificar se já existe fonte com esse uso
        if kb.typography_settings.filter(usage=usage).exists():
            return JsonResponse({
                'success': False,
                'error': f'Já existe uma fonte cadastrada para "{usage}"'
            }, status=400)
        
        # Criar fonte
        with transaction.atomic():
            # Obter próxima ordem
            max_order = kb.typography_settings.aggregate(models.Max('order'))['order__max'] or 0
            
            if font_source == 'google':
                google_font_name = data.get('google_font_name', '').strip()
                google_font_weight = data.get('google_font_weight', '400')
                
                if not google_font_name:
                    return JsonResponse({
                        'success': False,
                        'error': 'Nome da fonte é obrigatório'
                    }, status=400)
                
                font = Typography.objects.create(
                    knowledge_base=kb,
                    usage=usage,
                    font_source='google',
                    google_font_name=google_font_name,
                    google_font_weight=google_font_weight,
                    google_font_url=f'https://fonts.googleapis.com/css2?family={google_font_name.replace(" ", "+")}:wght@{google_font_weight}&display=swap',
                    order=max_order + 1,
                    updated_by=request.user
                )
                
                print(f"✅ [PERFIL_ADD_FONT] Fonte Google adicionada: {google_font_name} (ID: {font.id})", flush=True)
                
            else:  # upload
                custom_font_id = data.get('custom_font_id')
                
                if not custom_font_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'ID da fonte customizada é obrigatório'
                    }, status=400)
                
                # Buscar CustomFont
                try:
                    from apps.knowledge.models import CustomFont
                    custom_font = CustomFont.objects.get(id=custom_font_id, knowledge_base=kb)
                except CustomFont.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Fonte customizada não encontrada'
                    }, status=404)
                
                font = Typography.objects.create(
                    knowledge_base=kb,
                    usage=usage,
                    font_source='upload',
                    custom_font=custom_font,
                    order=max_order + 1,
                    updated_by=request.user
                )
                
                print(f"✅ [PERFIL_ADD_FONT] Fonte Upload adicionada: {custom_font.name} (ID: {font.id})", flush=True)
            
            return JsonResponse({
                'success': True,
                'font_id': font.id,
                'message': 'Fonte adicionada com sucesso!'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        print(f"❌ [PERFIL_ADD_FONT] Erro: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)


@never_cache
@login_required
@require_POST
@csrf_exempt  # TODO: Remover após debug
def perfil_remove_font(request):
    """
    Remover fonte da tipografia no Perfil
    """
    try:
        data = json.loads(request.body)
        font_id = data.get('font_id')
        
        if not font_id:
            return JsonResponse({
                'success': False,
                'error': 'ID da fonte não fornecido'
            }, status=400)
        
        kb = KnowledgeBase.objects.for_request(request).first()
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Buscar e remover fonte
        try:
            font = kb.typography_settings.get(id=font_id)
            usage = font.usage
            font.delete()
            
            print(f"✅ [PERFIL_REMOVE_FONT] Fonte removida: {usage} (ID: {font_id})", flush=True)
            
            return JsonResponse({
                'success': True,
                'message': 'Fonte removida com sucesso!'
            })
        
        except Typography.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Fonte não encontrada'
            }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        print(f"❌ [PERFIL_REMOVE_FONT] Erro: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)
