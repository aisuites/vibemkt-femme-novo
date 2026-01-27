"""
Image Processor - Geração de thumbnails e compressão de imagens
"""

from PIL import Image
from io import BytesIO
from typing import Tuple, Optional
import os


class ImageProcessor:
    """
    Processador de imagens para otimização e geração de thumbnails
    
    Features:
    - Geração de thumbnails mantendo aspect ratio
    - Compressão inteligente por formato
    - Preservação de qualidade visual
    - Suporte a PNG, JPG, WebP
    """
    
    # Configurações de thumbnail
    THUMBNAIL_MAX_SIZE = (800, 800)  # Largura x Altura máxima
    
    # Configurações de compressão por formato
    COMPRESSION_SETTINGS = {
        'JPEG': {
            'quality': 85,
            'optimize': True,
            'progressive': True,
        },
        'PNG': {
            'optimize': True,
            'compress_level': 6,  # 0-9, onde 9 é máxima compressão
        },
        'WEBP': {
            'quality': 85,
            'method': 6,  # 0-6, onde 6 é melhor qualidade
        },
    }
    
    @classmethod
    def create_thumbnail(
        cls,
        image_data: bytes,
        max_size: Optional[Tuple[int, int]] = None
    ) -> bytes:
        """
        Cria thumbnail da imagem mantendo aspect ratio
        
        Args:
            image_data: Bytes da imagem original
            max_size: Tamanho máximo (width, height). Default: (800, 800)
            
        Returns:
            Bytes da imagem thumbnail
            
        Raises:
            Exception: Se erro ao processar imagem
        """
        if max_size is None:
            max_size = cls.THUMBNAIL_MAX_SIZE
        
        try:
            # Abrir imagem
            img = Image.open(BytesIO(image_data))
            
            # Converter RGBA para RGB se necessário (para JPEG)
            if img.mode == 'RGBA' and img.format != 'PNG':
                # Criar fundo branco
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Alpha channel como mask
                img = background
            
            # Criar thumbnail mantendo aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Salvar em buffer
            output = BytesIO()
            format_name = img.format or 'JPEG'
            
            # Aplicar configurações de compressão
            save_kwargs = cls.COMPRESSION_SETTINGS.get(format_name, {})
            img.save(output, format=format_name, **save_kwargs)
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao criar thumbnail: {str(e)}")
    
    @classmethod
    def compress_image(
        cls,
        image_data: bytes,
        format_override: Optional[str] = None
    ) -> bytes:
        """
        Comprime imagem sem redimensionar
        
        Args:
            image_data: Bytes da imagem original
            format_override: Forçar formato específico (JPEG, PNG, WEBP)
            
        Returns:
            Bytes da imagem comprimida
            
        Raises:
            Exception: Se erro ao processar imagem
        """
        try:
            # Abrir imagem
            img = Image.open(BytesIO(image_data))
            
            # Determinar formato
            format_name = format_override or img.format or 'JPEG'
            
            # Converter RGBA para RGB se necessário (para JPEG)
            if format_name == 'JPEG' and img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            # Salvar com compressão
            output = BytesIO()
            save_kwargs = cls.COMPRESSION_SETTINGS.get(format_name, {})
            img.save(output, format=format_name, **save_kwargs)
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao comprimir imagem: {str(e)}")
    
    @classmethod
    def get_image_info(cls, image_data: bytes) -> dict:
        """
        Obtém informações da imagem
        
        Args:
            image_data: Bytes da imagem
            
        Returns:
            {
                'width': int,
                'height': int,
                'format': str,
                'mode': str,
                'size_bytes': int
            }
        """
        try:
            img = Image.open(BytesIO(image_data))
            
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': len(image_data),
            }
            
        except Exception as e:
            raise Exception(f"Erro ao obter informações da imagem: {str(e)}")
    
    @classmethod
    def process_for_upload(
        cls,
        image_data: bytes,
        create_thumbnail: bool = True,
        compress: bool = True
    ) -> dict:
        """
        Processa imagem para upload (thumbnail + compressão)
        
        Args:
            image_data: Bytes da imagem original
            create_thumbnail: Se deve criar thumbnail
            compress: Se deve comprimir original
            
        Returns:
            {
                'original': bytes,          # Original (comprimido se compress=True)
                'thumbnail': bytes,         # Thumbnail (se create_thumbnail=True)
                'info': dict,               # Informações da imagem
            }
        """
        result = {
            'original': image_data,
            'thumbnail': None,
            'info': cls.get_image_info(image_data),
        }
        
        # Comprimir original
        if compress:
            result['original'] = cls.compress_image(image_data)
        
        # Criar thumbnail
        if create_thumbnail:
            result['thumbnail'] = cls.create_thumbnail(image_data)
        
        return result
