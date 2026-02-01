"""
Views para gerenciamento de cores no Perfil da Empresa
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.db import models
import json

from apps.knowledge.models import KnowledgeBase, ColorPalette


@never_cache
@login_required
@require_POST
@csrf_exempt  # TODO: Remover após debug
def perfil_add_color(request):
    """
    Adicionar cor à paleta no Perfil
    """
    try:
        data = json.loads(request.body)
        hex_code = data.get('hex_code', '').strip().upper()
        
        # Validar HEX
        if not hex_code.startswith('#') or len(hex_code) != 7:
            return JsonResponse({
                'success': False,
                'error': 'Código HEX inválido. Use o formato #RRGGBB'
            }, status=400)
        
        kb = KnowledgeBase.objects.for_request(request).first()
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Verificar se cor já existe
        if kb.colors.filter(hex_code=hex_code).exists():
            return JsonResponse({
                'success': False,
                'error': 'Esta cor já está cadastrada'
            }, status=400)
        
        # Criar cor
        with transaction.atomic():
            # Obter próxima ordem
            max_order = kb.colors.aggregate(models.Max('order'))['order__max'] or 0
            
            color = ColorPalette.objects.create(
                knowledge_base=kb,
                name=f'Cor {hex_code}',
                hex_code=hex_code,
                color_type='primary',  # Padrão
                order=max_order + 1
            )
            
            print(f"✅ [PERFIL_ADD_COLOR] Cor adicionada: {hex_code} (ID: {color.id})", flush=True)
            
            return JsonResponse({
                'success': True,
                'color_id': color.id,
                'hex_code': hex_code,
                'message': 'Cor adicionada com sucesso!'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        print(f"❌ [PERFIL_ADD_COLOR] Erro: {e}", flush=True)
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
def perfil_remove_color(request):
    """
    Remover cor da paleta no Perfil
    """
    try:
        data = json.loads(request.body)
        color_id = data.get('color_id')
        
        if not color_id:
            return JsonResponse({
                'success': False,
                'error': 'ID da cor não fornecido'
            }, status=400)
        
        kb = KnowledgeBase.objects.for_request(request).first()
        if not kb:
            return JsonResponse({
                'success': False,
                'error': 'Base de conhecimento não encontrada'
            }, status=404)
        
        # Buscar e remover cor
        try:
            color = kb.colors.get(id=color_id)
            hex_code = color.hex_code
            color.delete()
            
            print(f"✅ [PERFIL_REMOVE_COLOR] Cor removida: {hex_code} (ID: {color_id})", flush=True)
            
            return JsonResponse({
                'success': True,
                'message': 'Cor removida com sucesso!'
            })
        
        except ColorPalette.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cor não encontrada'
            }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        print(f"❌ [PERFIL_REMOVE_COLOR] Erro: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)
