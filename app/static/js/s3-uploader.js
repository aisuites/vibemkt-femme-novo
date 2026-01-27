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
            
            console.log('DEBUG S3Uploader - presignedData:', {
                upload_url: presignedData.upload_url,
                s3_key: presignedData.s3_key,
                signed_headers: presignedData.signed_headers,
                has_signed_headers: !!presignedData.signed_headers
            });
            
            // Etapa 2: Upload para S3
            this._updateProgress(30, 'Enviando arquivo...');
            await this._uploadToS3(presignedData.upload_url, file, presignedData.signed_headers || {});
            
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
    async _uploadToS3(url, file, signedHeaders = {}) {
        const headers = {
            'Content-Type': file.type,
            ...signedHeaders
        };
        
        console.log('DEBUG _uploadToS3:', {
            url: url,
            fileType: file.type,
            fileSize: file.size,
            signedHeaders: signedHeaders,
            finalHeaders: headers
        });
        
        const response = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: headers
        });
        
        console.log('DEBUG _uploadToS3 response:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
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
