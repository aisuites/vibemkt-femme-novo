#!/usr/bin/env python
"""
Script para consolidar dados de KnowledgeBases duplicados
Organização: fulanas (ID 9)
"""

import sys
import os

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings.development')

import django
django.setup()

from apps.knowledge.models import Logo, CustomFont, ReferenceImage, KnowledgeBase, Typography
from apps.core.models import Organization

def consolidar_dados():
    """Consolida todos os dados no KB principal da organização"""
    
    print("=" * 60)
    print("CONSOLIDAÇÃO DE DADOS - KNOWLEDGE BASES")
    print("=" * 60)
    
    # Organização fulanas
    org = Organization.objects.get(id=9)
    print(f"\n📋 Organização: {org.name} (ID: {org.id})")
    
    # Buscar KB principal (com nome preenchido)
    kb_principal = KnowledgeBase.objects.filter(
        organization=org,
        nome_empresa__isnull=False
    ).exclude(nome_empresa='').first()
    
    if not kb_principal:
        print("❌ KB principal não encontrado!")
        return
    
    print(f"✅ KB Principal: ID {kb_principal.id} - {kb_principal.nome_empresa}")
    
    # Buscar todos os KBs da organização
    todos_kbs = KnowledgeBase.objects.filter(organization=org)
    print(f"\n📊 Total de KBs encontrados: {todos_kbs.count()}")
    
    # Consolidar Logos
    print("\n--- LOGOS ---")
    logos_outros = Logo.objects.filter(
        knowledge_base__organization=org
    ).exclude(knowledge_base=kb_principal)
    
    if logos_outros.exists():
        count = logos_outros.count()
        logos_outros.update(knowledge_base=kb_principal)
        print(f"✅ {count} logo(s) movido(s) para KB principal")
    else:
        print("ℹ️  Nenhum logo em outros KBs")
    
    # Consolidar Custom Fonts
    print("\n--- CUSTOM FONTS ---")
    fonts_outros = CustomFont.objects.filter(
        knowledge_base__organization=org
    ).exclude(knowledge_base=kb_principal)
    
    if fonts_outros.exists():
        count = fonts_outros.count()
        fonts_outros.update(knowledge_base=kb_principal)
        print(f"✅ {count} fonte(s) movida(s) para KB principal")
    else:
        print("ℹ️  Nenhuma fonte em outros KBs")
    
    # Consolidar Reference Images
    print("\n--- REFERENCE IMAGES ---")
    refs_outros = ReferenceImage.objects.filter(
        knowledge_base__organization=org
    ).exclude(knowledge_base=kb_principal)
    
    if refs_outros.exists():
        count = refs_outros.count()
        refs_outros.update(knowledge_base=kb_principal)
        print(f"✅ {count} referência(s) movida(s) para KB principal")
    else:
        print("ℹ️  Nenhuma referência em outros KBs")
    
    # Consolidar Typography
    print("\n--- TYPOGRAPHY ---")
    typo_outros = Typography.objects.filter(
        knowledge_base__organization=org
    ).exclude(knowledge_base=kb_principal)
    
    if typo_outros.exists():
        count = typo_outros.count()
        typo_outros.update(knowledge_base=kb_principal)
        print(f"✅ {count} tipografia(s) movida(s) para KB principal")
    else:
        print("ℹ️  Nenhuma tipografia em outros KBs")
    
    # Deletar KBs vazios
    print("\n--- LIMPEZA ---")
    kbs_vazios = KnowledgeBase.objects.filter(
        organization=org
    ).exclude(id=kb_principal.id)
    
    if kbs_vazios.exists():
        count = kbs_vazios.count()
        ids = list(kbs_vazios.values_list('id', flat=True))
        kbs_vazios.delete()
        print(f"✅ {count} KB(s) vazio(s) deletado(s): {ids}")
    else:
        print("ℹ️  Nenhum KB vazio para deletar")
    
    # Resultado final
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    
    logos_final = Logo.objects.filter(knowledge_base=kb_principal).count()
    fonts_final = CustomFont.objects.filter(knowledge_base=kb_principal).count()
    refs_final = ReferenceImage.objects.filter(knowledge_base=kb_principal).count()
    typo_final = Typography.objects.filter(knowledge_base=kb_principal).count()
    kbs_final = KnowledgeBase.objects.filter(organization=org).count()
    
    print(f"\n📊 KB Principal (ID {kb_principal.id}):")
    print(f"   - Logos: {logos_final}")
    print(f"   - Custom Fonts: {fonts_final}")
    print(f"   - Reference Images: {refs_final}")
    print(f"   - Typography: {typo_final}")
    print(f"\n📊 Total de KBs restantes: {kbs_final}")
    
    print("\n✅ CONSOLIDAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)

if __name__ == '__main__':
    consolidar_dados()
