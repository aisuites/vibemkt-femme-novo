/**
 * S3 Uploader - Classe reutilizável para upload de arquivos usando Presigned URLs
 * 
 * Uso:
 *   const uploader = new S3Uploader('/knowledge/logo/upload-url/', '/knowledge/logo/create/');
 *   await uploader.upload(file, { name: 'Logo Principal', logoType: 'principal' });
 */

class S3Uploader {
    /**
     * @param {string} uploadUrlEndpoint - Endpoint para obter Presigned URL
     * @param {string} createRecordEndpoint - Endpoint para criar registro no banco
     * @param {Object} options - Opções adicionais
     */
    constructor(uploadUrlEndpoint, createRecordEndpoint, options = {}) {
        this.uploadUrlEndpoint = uploadUrlEndpoint;
        this.createRecordEndpoint = createRecordEndpoint;
        this.options = {
            onProgress: null,           // Callback(percent, message)
            onSuccess: null,            // Callback(data)
            onError: null,              // Callback(error)
            validateFile: null,         // Callback(file) -> {valid: bool, error: string}
            ...options
        };
    }
    
    /**
     * Faz upload completo do arquivo
     * 
     * @param {File} file - Arquivo a ser enviado
     * @param {Object} metadata - Metadados adicionais para o registro
     * @returns {Promise<Object>} Dados do registro criado
     */
    async upload(file, metadata = {}) {
        try {
            // Validação customizada
            if (this.options.validateFile) {
                const validation = this.options.validateFile(file);
                if (!validation.valid) {
                    throw new Error(validation.error);
                }
            }
            
            // Etapa 1: Obter Presigned URL
            this._updateProgress(10, 'Preparando upload...');
            const presignedData = await this._getPresignedUrl(file);
            
            // Etapa 2: Upload para S3
            this._updateProgress(30, 'Enviando arquivo...');
            await this._uploadToS3(presignedData.upload_url, file);
            
            // Etapa 3: Criar registro no banco
            this._updateProgress(70, 'Finalizando...');
            const record = await this._createRecord({
                s3Key: presignedData.s3_key,
                fileFormat: this._getFileExtension(file.type),
                ...metadata
            });
            
            this._updateProgress(100, 'Concluído!');
            
            if (this.options.onSuccess) {
                this.options.onSuccess(record);
            }
            
            return record;
            
        } catch (error) {
            if (this.options.onError) {
                this.options.onError(error);
            }
            throw error;
        }
    }
    
    /**
     * Obtém Presigned URL do backend
     * @private
     */
    async _getPresignedUrl(file) {
        const response = await fetch(this.uploadUrlEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this._getCookie('csrftoken')
            },
            body: new URLSearchParams({
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao obter URL de upload');
        }
        
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Erro ao obter URL de upload');
        }
        
        return result.data;
    }
    
    /**
     * Faz upload do arquivo para S3
     * @private
     */
    async _uploadToS3(url, file) {
        const response = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': file.type
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao enviar arquivo para S3');
        }
    }
    
    /**
     * Cria registro no banco de dados
     * @private
     */
    async _createRecord(data) {
        const response = await fetch(this.createRecordEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this._getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erro ao criar registro');
        }
        
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Erro ao criar registro');
        }
        
        return result.data;
    }
    
    /**
     * Atualiza progresso
     * @private
     */
    _updateProgress(percent, message) {
        if (this.options.onProgress) {
            this.options.onProgress(percent, message);
        }
    }
    
    /**
     * Obtém extensão do arquivo baseado no MIME type
     * @private
     */
    _getFileExtension(mimeType) {
        const extensions = {
            'image/png': 'png',
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/svg+xml': 'svg',
            'image/webp': 'webp',
            'font/ttf': 'ttf',
            'font/otf': 'otf',
            'application/pdf': 'pdf',
            'video/mp4': 'mp4',
            'video/webm': 'webm'
        };
        return extensions[mimeType] || 'bin';
    }
    
    /**
     * Obtém cookie CSRF
     * @private
     */
    _getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}


/**
 * Image Preview Loader - Carrega previews de imagens com lazy loading
 * 
 * Uso:
 *   const loader = new ImagePreviewLoader('/knowledge/logo/preview-url/');
 *   loader.observe(imageElement);
 */
class ImagePreviewLoader {
    /**
     * @param {string} previewUrlEndpoint - Endpoint para obter URL de preview
     * @param {Object} options - Opções do Intersection Observer
     */
    constructor(previewUrlEndpoint, options = {}) {
        this.previewUrlEndpoint = previewUrlEndpoint;
        this.cache = new Map(); // Cache de URLs
        
        this.observer = new IntersectionObserver(
            this._handleIntersection.bind(this),
            {
                rootMargin: '50px',
                threshold: 0.01,
                ...options
            }
        );
    }
    
    /**
     * Observa elemento de imagem para lazy loading
     * 
     * @param {HTMLImageElement} imageElement - Elemento <img> com data-s3-key
     */
    observe(imageElement) {
        if (!imageElement.dataset.s3Key && !imageElement.dataset.recordId) {
            console.warn('Elemento não tem data-s3-key ou data-record-id:', imageElement);
            return;
        }
        this.observer.observe(imageElement);
    }
    
    /**
     * Para de observar elemento
     */
    unobserve(imageElement) {
        this.observer.unobserve(imageElement);
    }
    
    /**
     * Desconecta observer
     */
    disconnect() {
        this.observer.disconnect();
        this.cache.clear();
    }
    
    /**
     * Handler do Intersection Observer
     * @private
     */
    async _handleIntersection(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                const img = entry.target;
                const recordId = img.dataset.recordId;
                const recordType = img.dataset.recordType; // 'logo' ou 'reference'
                
                try {
                    // Verificar cache
                    const cacheKey = `${recordType}-${recordId}`;
                    let url = this.cache.get(cacheKey);
                    
                    if (!url) {
                        // Obter URL do backend
                        url = await this._getPreviewUrl(recordId, recordType);
                        this.cache.set(cacheKey, url);
                    }
                    
                    // Carregar imagem
                    img.src = url;
                    img.classList.add('loaded');
                    
                    // Parar de observar
                    this.observer.unobserve(img);
                    
                } catch (error) {
                    console.error('Erro ao carregar preview:', error);
                    img.src = '/static/images/error-placeholder.png';
                    img.classList.add('error');
                    this.observer.unobserve(img);
                }
            }
        }
    }
    
    /**
     * Obtém URL de preview do backend
     * @private
     */
    async _getPreviewUrl(recordId, recordType) {
        const paramName = recordType === 'logo' ? 'logoId' : 'referenceId';
        
        const response = await fetch(this.previewUrlEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this._getCookie('csrftoken')
            },
            body: new URLSearchParams({
                [paramName]: recordId
            })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao obter URL de preview');
        }
        
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Erro ao obter URL de preview');
        }
        
        return result.data.preview_url;
    }
    
    /**
     * Obtém cookie CSRF
     * @private
     */
    _getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}


/**
 * Utilitários para validação de arquivos
 */
const FileValidators = {
    /**
     * Valida tamanho do arquivo
     */
    maxSize: (maxMB) => (file) => {
        const maxBytes = maxMB * 1024 * 1024;
        if (file.size > maxBytes) {
            return {
                valid: false,
                error: `Arquivo muito grande. Máximo: ${maxMB}MB`
            };
        }
        return { valid: true };
    },
    
    /**
     * Valida tipo do arquivo
     */
    allowedTypes: (types) => (file) => {
        if (!types.includes(file.type)) {
            return {
                valid: false,
                error: `Tipo de arquivo não permitido. Aceitos: ${types.join(', ')}`
            };
        }
        return { valid: true };
    },
    
    /**
     * Valida dimensões de imagem
     */
    imageDimensions: (minWidth, minHeight, maxWidth, maxHeight) => async (file) => {
        return new Promise((resolve) => {
            const img = new Image();
            const url = URL.createObjectURL(file);
            
            img.onload = () => {
                URL.revokeObjectURL(url);
                
                if (minWidth && img.width < minWidth) {
                    resolve({
                        valid: false,
                        error: `Largura mínima: ${minWidth}px`
                    });
                    return;
                }
                
                if (minHeight && img.height < minHeight) {
                    resolve({
                        valid: false,
                        error: `Altura mínima: ${minHeight}px`
                    });
                    return;
                }
                
                if (maxWidth && img.width > maxWidth) {
                    resolve({
                        valid: false,
                        error: `Largura máxima: ${maxWidth}px`
                    });
                    return;
                }
                
                if (maxHeight && img.height > maxHeight) {
                    resolve({
                        valid: false,
                        error: `Altura máxima: ${maxHeight}px`
                    });
                    return;
                }
                
                resolve({ valid: true, width: img.width, height: img.height });
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(url);
                resolve({
                    valid: false,
                    error: 'Erro ao carregar imagem'
                });
            };
            
            img.src = url;
        });
    },
    
    /**
     * Combina múltiplos validadores
     */
    combine: (...validators) => async (file) => {
        for (const validator of validators) {
            const result = await validator(file);
            if (!result.valid) {
                return result;
            }
        }
        return { valid: true };
    }
};
