#!/usr/bin/env python3
"""
Script de teste para view create_logo
"""
import os
import sys
import django

sys.path.insert(0, '/opt/iamkt/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings.development')
django.setup()

from apps.knowledge.models import Logo, KnowledgeBase
from apps.core.models import Organization, User

def test_create_logo():
    """Testa criação de logo"""
    
    print("=" * 60)
    print("TESTE: Criação de Logo")
    print("=" * 60)
    
    try:
        # Buscar organização 9
        org = Organization.objects.get(id=9)
        print(f"\n✅ Organização encontrada: {org.name}")
        
        # Verificar se tem knowledge_base
        if hasattr(org, 'knowledge_base'):
            kb = org.knowledge_base
            print(f"✅ Knowledge Base encontrada: ID {kb.id}")
        else:
            print("❌ Organização não tem knowledge_base!")
            print("   Criando knowledge_base...")
            kb = KnowledgeBase.objects.create(organization=org)
            print(f"✅ Knowledge Base criada: ID {kb.id}")
        
        # Buscar usuário
        user = User.objects.first()
        print(f"✅ Usuário: {user.email}")
        
        # Tentar criar logo
        logo = Logo.objects.create(
            knowledge_base=kb,
            name='test-logo',
            logo_type='principal',
            file_format='png',
            s3_key='org-9/logos/test.png',
            s3_url='https://iamkt-uploads.s3.amazonaws.com/org-9/logos/test.png',
            is_primary=False,
            uploaded_by=user
        )
        
        print(f"\n✅ Logo criado com sucesso! ID: {logo.id}")
        
        # Deletar logo de teste
        logo.delete()
        print("✅ Logo de teste deletado")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_create_logo()
