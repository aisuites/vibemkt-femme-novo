"""
S3 Service - Upload seguro de arquivos usando Presigned URLs
Reutilizável para logos, imagens, fontes, vídeos, PDFs, etc.
"""

import boto3
import secrets
import time
import re
from typing import Tuple, Optional, Dict, Any
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings


class S3Service:
    """
    Service centralizado para operações S3 com Presigned URLs
    
    Features:
    - Nomenclatura personalizável por tipo de arquivo
    - Validação flexível de tamanho por tipo
    - Suporte a múltiplos formatos
    - Bucket por organização
    - URLs temporárias seguras
    """
    
    # ============================================
    # CONFIGURAÇÕES POR TIPO DE ARQUIVO
    # ============================================
    
    FILE_CONFIGS = {
        'logo': {
            'folder': 'logos',
            'max_size_mb': 10,
            'allowed_types': {
                'image/png': 'png',
                'image/svg+xml': 'svg',
                'image/jpeg': 'jpg',
                'image/webp': 'webp',
            },
            'filename_pattern': 'org_{org_id}_logo_{timestamp}_{random}.{ext}',
            # Exemplo: org_1_logo_1706356800000_abc123.png
        },
        'reference': {
            'folder': 'references',
            'max_size_mb': 10,
            'allowed_types': {
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/webp': 'webp',
            },
            'filename_pattern': 'org_{org_id}_ref_{timestamp}_{random}.{ext}',
            # Exemplo: org_1_ref_1706356800000_abc123.jpg
        },
        'font': {
            'folder': 'fonts',
            'max_size_mb': 5,
            'allowed_types': {
                'font/ttf': 'ttf',
                'font/otf': 'otf',
                'application/x-font-ttf': 'ttf',
                'application/x-font-otf': 'otf',
            },
            'filename_pattern': 'org_{org_id}_fonte_{name}.{ext}',
            # Exemplo: org_1_fonte_Roboto.ttf
        },
        'video': {
            'folder': 'videos',
            'max_size_mb': 25,
            'allowed_types': {
                'video/mp4': 'mp4',
                'video/webm': 'webm',
                'video/quicktime': 'mov',
            },
            'filename_pattern': 'org_{org_id}_video_{timestamp}_{random}.{ext}',
            # Exemplo: org_1_video_1706356800000_abc123.mp4
        },
        'pdf': {
            'folder': 'documents',
            'max_size_mb': 15,
            'allowed_types': {
                'application/pdf': 'pdf',
            },
            'filename_pattern': 'org_{org_id}_doc_{timestamp}_{random}.{ext}',
            # Exemplo: org_1_doc_1706356800000_abc123.pdf
        },
        'post_image': {
            'folder': 'posts',
            'max_size_mb': 10,
            'allowed_types': {
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/webp': 'webp',
            },
            'filename_pattern': 'org_{org_id}_post_{date}_{random}.{ext}',
            # Exemplo: org_1_post_20260127_abc123.png
        },
    }
    
    # Tempo de expiração das URLs (segundos)
    PRESIGNED_URL_EXPIRATION = {
        'upload': 300,      # 5 minutos para completar upload
        'download': 3600,   # 1 hora para download
        'preview': 3600,    # 1 hora para preview
    }
    
    # ============================================
    # MÉTODOS PRINCIPAIS
    # ============================================
    
    @classmethod
    def _get_s3_client(cls):
        """Retorna cliente S3 configurado"""
        config = Config(
            region_name=settings.AWS_REGION,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=config
        )
    
    @classmethod
    def _get_bucket_name(cls, organization_id: int) -> str:
        """
        Retorna nome do bucket para a organização
        
        Args:
            organization_id: ID da organização
            
        Returns:
            Nome do bucket (ex: iamkt-org-1)
        """
        template = getattr(settings, 'AWS_BUCKET_NAME_TEMPLATE', 'iamkt-org-{org_id}')
        return template.format(org_id=organization_id)
    
    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """
        Sanitiza nome de arquivo removendo caracteres perigosos
        
        Args:
            filename: Nome original do arquivo
            
        Returns:
            Nome sanitizado
        """
        # Remove extensão se existir
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Remove caracteres especiais, mantém apenas alfanuméricos, underscore e hífen
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name_without_ext)
        
        # Remove underscores/hífens duplicados
        sanitized = re.sub(r'[_-]+', '_', sanitized)
        
        # Limita tamanho
        return sanitized[:50]
    
    @classmethod
    def generate_filename(
        cls,
        file_type: str,
        original_name: str,
        mime_type: str,
        organization_id: int,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Gera nome de arquivo baseado no padrão configurado
        
        Args:
            file_type: Tipo do arquivo (logo, reference, font, etc)
            original_name: Nome original do arquivo
            mime_type: MIME type do arquivo
            organization_id: ID da organização
            custom_data: Dados customizados para o padrão (ex: {name: 'Roboto', date: '20260127'})
            
        Returns:
            Nome completo do arquivo com path (ex: logos/org_1_logo_123.png)
            
        Raises:
            ValueError: Se tipo de arquivo não configurado
        """
        if file_type not in cls.FILE_CONFIGS:
            raise ValueError(f"Tipo de arquivo '{file_type}' não configurado")
        
        config = cls.FILE_CONFIGS[file_type]
        
        # Obter extensão
        extension = config['allowed_types'].get(mime_type)
        if not extension:
            raise ValueError(f"MIME type '{mime_type}' não permitido para tipo '{file_type}'")
        
        # Preparar dados para o padrão
        pattern_data = {
            'org_id': organization_id,
            'timestamp': int(time.time() * 1000),  # Milissegundos
            'random': secrets.token_hex(8),  # 16 caracteres hex
            'ext': extension,
            'name': cls._sanitize_filename(original_name),
            'date': time.strftime('%Y%m%d'),
        }
        
        # Adicionar dados customizados
        if custom_data:
            pattern_data.update(custom_data)
        
        # Gerar nome do arquivo usando o padrão
        filename = config['filename_pattern'].format(**pattern_data)
        
        # Retornar com folder
        folder = config['folder']
        return f"{folder}/{filename}"
    
    @classmethod
    def validate_file(
        cls,
        file_type: str,
        mime_type: str,
        file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida tipo e tamanho do arquivo
        
        Args:
            file_type: Tipo do arquivo (logo, reference, font, etc)
            mime_type: MIME type do arquivo
            file_size: Tamanho em bytes
            
        Returns:
            Tuple (is_valid, error_message)
        """
        # Verificar se tipo existe
        if file_type not in cls.FILE_CONFIGS:
            return False, f"Tipo de arquivo '{file_type}' não suportado"
        
        config = cls.FILE_CONFIGS[file_type]
        
        # Validar MIME type
        if mime_type not in config['allowed_types']:
            allowed = ', '.join(config['allowed_types'].keys())
            return False, f"Tipo de arquivo não permitido. Aceitos: {allowed}"
        
        # Validar tamanho
        max_bytes = config['max_size_mb'] * 1024 * 1024
        if file_size > max_bytes:
            return False, f"Arquivo muito grande. Máximo: {config['max_size_mb']}MB"
        
        if file_size <= 0:
            return False, "Arquivo vazio"
        
        return True, None
    
    @classmethod
    def generate_presigned_upload_url(
        cls,
        file_type: str,
        file_name: str,
        mime_type: str,
        file_size: int,
        organization_id: int,
        custom_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Gera Presigned URL para upload de arquivo
        
        Args:
            file_type: Tipo do arquivo (logo, reference, font, etc)
            file_name: Nome original do arquivo
            mime_type: MIME type do arquivo
            file_size: Tamanho em bytes
            organization_id: ID da organização
            custom_data: Dados customizados para nomenclatura
            metadata: Metadados adicionais para o S3
            
        Returns:
            {
                'upload_url': str,      # URL para fazer PUT
                's3_key': str,          # Chave do arquivo no S3
                'bucket': str,          # Nome do bucket
                'expires_in': int,      # Segundos até expirar
            }
            
        Raises:
            ValueError: Se validação falhar
            Exception: Se erro ao gerar URL
        """
        # Validar arquivo
        is_valid, error_msg = cls.validate_file(file_type, mime_type, file_size)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Gerar nome do arquivo
        s3_key = cls.generate_filename(
            file_type=file_type,
            original_name=file_name,
            mime_type=mime_type,
            organization_id=organization_id,
            custom_data=custom_data
        )
        
        # Obter bucket
        bucket_name = cls._get_bucket_name(organization_id)
        
        # Preparar metadados
        s3_metadata = {
            'original-name': file_name,
            'organization-id': str(organization_id),
            'file-type': file_type,
            'upload-timestamp': str(int(time.time())),
        }
        if metadata:
            s3_metadata.update(metadata)
        
        # Gerar Presigned URL
        s3_client = cls._get_s3_client()
        
        try:
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key,
                    'ContentType': mime_type,
                    'ServerSideEncryption': 'AES256',
                    'Metadata': s3_metadata,
                },
                ExpiresIn=cls.PRESIGNED_URL_EXPIRATION['upload'],
                HttpMethod='PUT'
            )
            
            return {
                'upload_url': presigned_url,
                's3_key': s3_key,
                'bucket': bucket_name,
                'expires_in': cls.PRESIGNED_URL_EXPIRATION['upload'],
            }
            
        except ClientError as e:
            raise Exception(f"Erro ao gerar URL de upload: {str(e)}")
    
    @classmethod
    def generate_presigned_download_url(
        cls,
        s3_key: str,
        organization_id: int,
        url_type: str = 'download',
        expires_in: Optional[int] = None
    ) -> str:
        """
        Gera Presigned URL para download/preview de arquivo
        
        Args:
            s3_key: Chave do arquivo no S3
            organization_id: ID da organização
            url_type: Tipo de URL ('download' ou 'preview')
            expires_in: Tempo customizado de expiração (segundos)
            
        Returns:
            URL temporária para acesso ao arquivo
            
        Raises:
            ValueError: Se s3_key inválida
            Exception: Se erro ao gerar URL
        """
        # Validar s3_key (prevenir path traversal)
        if '..' in s3_key or '//' in s3_key:
            raise ValueError("Chave de arquivo contém caracteres suspeitos")
        
        # Obter bucket
        bucket_name = cls._get_bucket_name(organization_id)
        
        # Determinar tempo de expiração
        if expires_in is None:
            expires_in = cls.PRESIGNED_URL_EXPIRATION.get(url_type, 3600)
        
        # Gerar Presigned URL
        s3_client = cls._get_s3_client()
        
        try:
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key,
                },
                ExpiresIn=expires_in,
                HttpMethod='GET'
            )
            
            return presigned_url
            
        except ClientError as e:
            raise Exception(f"Erro ao gerar URL de {url_type}: {str(e)}")
    
    @classmethod
    def delete_file(
        cls,
        s3_key: str,
        organization_id: int
    ) -> bool:
        """
        Deleta arquivo do S3
        
        Args:
            s3_key: Chave do arquivo no S3
            organization_id: ID da organização
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        # Validar s3_key
        if '..' in s3_key or '//' in s3_key:
            return False
        
        # Obter bucket
        bucket_name = cls._get_bucket_name(organization_id)
        
        # Deletar arquivo
        s3_client = cls._get_s3_client()
        
        try:
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError:
            return False
    
    @classmethod
    def get_file_url(
        cls,
        s3_key: str,
        organization_id: int
    ) -> str:
        """
        Retorna URL pública do arquivo (se bucket for público)
        Caso contrário, use generate_presigned_download_url()
        
        Args:
            s3_key: Chave do arquivo no S3
            organization_id: ID da organização
            
        Returns:
            URL do arquivo
        """
        bucket_name = cls._get_bucket_name(organization_id)
        region = settings.AWS_REGION
        
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
    
    @classmethod
    def list_file_types(cls) -> Dict[str, Dict[str, Any]]:
        """
        Retorna configurações de todos os tipos de arquivo suportados
        
        Returns:
            Dicionário com configurações por tipo
        """
        return cls.FILE_CONFIGS.copy()
