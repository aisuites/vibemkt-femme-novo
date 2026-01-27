"""
Validadores de upload de arquivos
Segurança: MIME type, tamanho, extensão
"""

import mimetypes
from typing import Dict, List, Tuple


class FileUploadValidator:
    """
    Validador robusto para uploads de arquivos
    Valida MIME type, tamanho e extensão
    """
    
    # Limites de tamanho por tipo (em bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FONT_SIZE = 5 * 1024 * 1024    # 5MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024 # 100MB
    
    # MIME types permitidos
    ALLOWED_IMAGE_MIMES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml',
    }
    
    ALLOWED_FONT_MIMES = {
        'font/ttf',
        'font/otf',
        'application/x-font-ttf',
        'application/x-font-otf',
        'application/font-sfnt',
        'font/woff',
        'font/woff2',
    }
    
    ALLOWED_VIDEO_MIMES = {
        'video/mp4',
        'video/webm',
        'video/quicktime',
    }
    
    # Extensões permitidas
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    ALLOWED_FONT_EXTENSIONS = {'.ttf', '.otf', '.woff', '.woff2'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov'}
    
    @classmethod
    def validate_image(cls, file_name: str, file_type: str, file_size: int) -> Tuple[bool, str]:
        """
        Valida upload de imagem
        
        Args:
            file_name: Nome do arquivo
            file_type: MIME type
            file_size: Tamanho em bytes
            
        Returns:
            (is_valid, error_message)
        """
        # Validar extensão
        extension = cls._get_extension(file_name)
        if extension not in cls.ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Extensão não permitida. Permitidas: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
        
        # Validar MIME type
        if file_type not in cls.ALLOWED_IMAGE_MIMES:
            return False, f"Tipo de arquivo não permitido. Tipo recebido: {file_type}"
        
        # Validar tamanho
        if file_size > cls.MAX_IMAGE_SIZE:
            max_mb = cls.MAX_IMAGE_SIZE / (1024 * 1024)
            return False, f"Arquivo muito grande. Máximo: {max_mb}MB"
        
        if file_size == 0:
            return False, "Arquivo vazio"
        
        return True, ""
    
    @classmethod
    def validate_font(cls, file_name: str, file_type: str, file_size: int) -> Tuple[bool, str]:
        """
        Valida upload de fonte
        
        Args:
            file_name: Nome do arquivo
            file_type: MIME type
            file_size: Tamanho em bytes
            
        Returns:
            (is_valid, error_message)
        """
        # Validar extensão
        extension = cls._get_extension(file_name)
        if extension not in cls.ALLOWED_FONT_EXTENSIONS:
            return False, f"Extensão não permitida. Permitidas: {', '.join(cls.ALLOWED_FONT_EXTENSIONS)}"
        
        # Validar MIME type (mais flexível para fontes)
        if file_type not in cls.ALLOWED_FONT_MIMES:
            # Aceitar se extensão estiver correta (alguns browsers enviam MIME errado)
            if extension not in cls.ALLOWED_FONT_EXTENSIONS:
                return False, f"Tipo de arquivo não permitido. Tipo recebido: {file_type}"
        
        # Validar tamanho
        if file_size > cls.MAX_FONT_SIZE:
            max_mb = cls.MAX_FONT_SIZE / (1024 * 1024)
            return False, f"Arquivo muito grande. Máximo: {max_mb}MB"
        
        if file_size == 0:
            return False, "Arquivo vazio"
        
        return True, ""
    
    @classmethod
    def validate_video(cls, file_name: str, file_type: str, file_size: int) -> Tuple[bool, str]:
        """
        Valida upload de vídeo
        
        Args:
            file_name: Nome do arquivo
            file_type: MIME type
            file_size: Tamanho em bytes
            
        Returns:
            (is_valid, error_message)
        """
        # Validar extensão
        extension = cls._get_extension(file_name)
        if extension not in cls.ALLOWED_VIDEO_EXTENSIONS:
            return False, f"Extensão não permitida. Permitidas: {', '.join(cls.ALLOWED_VIDEO_EXTENSIONS)}"
        
        # Validar MIME type
        if file_type not in cls.ALLOWED_VIDEO_MIMES:
            return False, f"Tipo de arquivo não permitido. Tipo recebido: {file_type}"
        
        # Validar tamanho
        if file_size > cls.MAX_VIDEO_SIZE:
            max_mb = cls.MAX_VIDEO_SIZE / (1024 * 1024)
            return False, f"Arquivo muito grande. Máximo: {max_mb}MB"
        
        if file_size == 0:
            return False, "Arquivo vazio"
        
        return True, ""
    
    @staticmethod
    def _get_extension(file_name: str) -> str:
        """Extrai extensão do arquivo em lowercase"""
        if '.' not in file_name:
            return ''
        return '.' + file_name.rsplit('.', 1)[1].lower()
    
    @classmethod
    def get_file_category(cls, file_name: str) -> str:
        """
        Determina categoria do arquivo pela extensão
        
        Returns:
            'image', 'font', 'video' ou 'unknown'
        """
        extension = cls._get_extension(file_name)
        
        if extension in cls.ALLOWED_IMAGE_EXTENSIONS:
            return 'image'
        elif extension in cls.ALLOWED_FONT_EXTENSIONS:
            return 'font'
        elif extension in cls.ALLOWED_VIDEO_EXTENSIONS:
            return 'video'
        else:
            return 'unknown'
