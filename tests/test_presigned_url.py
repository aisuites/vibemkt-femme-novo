#!/usr/bin/env python3
"""
Script de teste para verificar Presigned URLs do S3
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/opt/iamkt/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings.development')
django.setup()

from apps.core.services import S3Service

def test_presigned_url():
    """Testa geração de Presigned URL"""
    
    print("=" * 60)
    print("TESTE: Geração de Presigned URL")
    print("=" * 60)
    
    try:
        # Simular upload de logo
        result = S3Service.generate_presigned_upload_url(
            file_name='test-logo.png',
            file_type='image/png',
            file_size=50000,  # 50KB
            category='logos',
            organization_id=9,
            custom_data={'logo_type': 'principal'}
        )
        
        print("\n✅ Presigned URL gerada com sucesso!")
        print(f"\nS3 Key: {result['s3_key']}")
        print(f"Expires in: {result['expires_in']} segundos")
        print(f"\nURL (primeiros 200 chars):")
        print(result['upload_url'][:200] + "...")
        
        # Extrair headers da URL
        url = result['upload_url']
        if 'X-Amz-SignedHeaders=' in url:
            start = url.find('X-Amz-SignedHeaders=') + len('X-Amz-SignedHeaders=')
            end = url.find('&', start)
            signed_headers = url[start:end if end != -1 else None]
            print(f"\n📋 Headers assinados na URL:")
            for header in signed_headers.split('%3B'):
                print(f"  - {header}")
        
        print("\n" + "=" * 60)
        print("HEADERS QUE DEVEM SER ENVIADOS NO PUT:")
        print("=" * 60)
        print("Content-Type: image/png")
        print("x-amz-server-side-encryption: AES256")
        print("x-amz-storage-class: INTELLIGENT_TIERING")
        print("x-amz-meta-original-name: test-logo.png")
        print("x-amz-meta-organization-id: 9")
        print("x-amz-meta-category: logos")
        print("x-amz-meta-upload-timestamp: <timestamp>")
        
        print("\n" + "=" * 60)
        print("COMANDO CURL PARA TESTAR:")
        print("=" * 60)
        print(f"""
curl -X PUT \\
  '{result['upload_url']}' \\
  -H 'Content-Type: image/png' \\
  -H 'x-amz-server-side-encryption: AES256' \\
  -H 'x-amz-storage-class: INTELLIGENT_TIERING' \\
  -H 'x-amz-meta-original-name: test-logo.png' \\
  -H 'x-amz-meta-organization-id: 9' \\
  -H 'x-amz-meta-category: logos' \\
  -H 'x-amz-meta-upload-timestamp: 1706356800' \\
  --data-binary '@/tmp/test.png' \\
  -v
        """)
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_presigned_url()
