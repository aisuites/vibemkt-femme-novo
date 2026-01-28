#!/usr/bin/env python
"""
Script de teste para validar salvamento de concorrentes
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/opt/iamkt/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.knowledge.models import KnowledgeBase
from apps.core.models import Organization
import json

def test_concorrentes_save():
    """Testa salvamento de concorrentes"""
    print("=" * 60)
    print("TESTE: Salvamento de Concorrentes")
    print("=" * 60)
    
    # 1. Buscar primeira organization
    org = Organization.objects.first()
    if not org:
        print("❌ ERRO: Nenhuma organization encontrada")
        return False
    
    print(f"✅ Organization encontrada: {org.name} (id={org.id})")
    
    # 2. Buscar ou criar KnowledgeBase
    kb, created = KnowledgeBase.objects.get_or_create(organization=org)
    print(f"✅ KnowledgeBase: {'criada' if created else 'existente'} (id={kb.id})")
    
    # 3. Verificar estado atual
    print(f"\n📊 Estado ANTES do teste:")
    print(f"   concorrentes atual: {kb.concorrentes}")
    print(f"   tipo: {type(kb.concorrentes)}")
    
    # 4. Preparar dados de teste
    test_data = [
        {"nome": "Concorrente Teste 1", "url": "https://teste1.com"},
        {"nome": "Concorrente Teste 2", "url": "https://teste2.com"},
        {"nome": "Concorrente Teste 3", "url": ""}
    ]
    
    print(f"\n🔄 Salvando dados de teste:")
    print(f"   {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    # 5. Salvar
    try:
        kb.concorrentes = test_data
        kb.save(update_fields=['concorrentes'])
        print("✅ save() executado sem erros")
    except Exception as e:
        print(f"❌ ERRO ao salvar: {e}")
        return False
    
    # 6. Recarregar do banco
    kb.refresh_from_db()
    print(f"\n📊 Estado DEPOIS do save (refresh_from_db):")
    print(f"   concorrentes: {kb.concorrentes}")
    print(f"   tipo: {type(kb.concorrentes)}")
    
    # 7. Validar
    if kb.concorrentes == test_data:
        print("\n✅ SUCESSO: Dados salvos e recuperados corretamente!")
        return True
    else:
        print("\n❌ FALHA: Dados não correspondem!")
        print(f"   Esperado: {test_data}")
        print(f"   Obtido: {kb.concorrentes}")
        return False

def test_field_exists():
    """Verifica se o campo concorrentes existe no modelo"""
    print("\n" + "=" * 60)
    print("TESTE: Verificação do Campo")
    print("=" * 60)
    
    from django.db import connection
    
    # Verificar se coluna existe na tabela
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'knowledge_knowledgebase' 
            AND column_name = 'concorrentes'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Campo 'concorrentes' existe na tabela")
            print(f"   Tipo: {result[1]}")
            return True
        else:
            print("❌ Campo 'concorrentes' NÃO existe na tabela!")
            print("   Execute: python manage.py migrate")
            return False

def test_form_field():
    """Verifica se o campo está no formulário"""
    print("\n" + "=" * 60)
    print("TESTE: Verificação do Formulário")
    print("=" * 60)
    
    from apps.knowledge.forms import KnowledgeBaseBlock6Form
    
    form = KnowledgeBaseBlock6Form()
    
    if 'concorrentes' in form.fields:
        print("✅ Campo 'concorrentes' está no formulário Block6")
    else:
        print("❌ Campo 'concorrentes' NÃO está no formulário Block6")
        print(f"   Campos disponíveis: {list(form.fields.keys())}")

if __name__ == '__main__':
    print("\n🧪 INICIANDO TESTES DE VALIDAÇÃO\n")
    
    # Teste 1: Campo existe?
    field_ok = test_field_exists()
    
    # Teste 2: Formulário tem o campo?
    test_form_field()
    
    # Teste 3: Salvamento funciona?
    if field_ok:
        save_ok = test_concorrentes_save()
        
        if save_ok:
            print("\n" + "=" * 60)
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTE DE SALVAMENTO FALHOU")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("❌ CAMPO NÃO EXISTE - EXECUTE MIGRATIONS")
        print("=" * 60)
        sys.exit(1)
