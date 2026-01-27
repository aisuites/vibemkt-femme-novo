/**
 * UPLOADS-S3.JS - Gerenciamento de Uploads com S3 Presigned URLs
 * Versão 2.0 - Integração real com backend Django + AWS S3
 * 
 * Depende de:
 * - s3-uploader.js (classe S3Uploader)
 * - image-validator.js (classe ImageValidator)
 * - image-preview-loader.js (classe ImagePreviewLoader)
 */

// ============================================
// CONFIGURAÇÃO GLOBAL
// ============================================

const UploadS3Config = {
    endpoints: {
        logoUploadUrl: '/knowledge/logo/upload-url/',
        logoCreate: '/knowledge/logo/create/',
        logoDelete: '/knowledge/logo/{id}/delete/',
        referenceUploadUrl: '/knowledge/reference/upload-url/',
        referenceCreate: '/knowledge/reference/create/',
        referenceDelete: '/knowledge/reference/{id}/delete/',
        previewUrl: '/knowledge/preview-url/'
    },
    validators: {
        logos: null,  // Será inicializado no DOMContentLoaded
        references: null
    },
    previewLoader: null  // Será inicializado no DOMContentLoaded
};

// ============================================
// UPLOAD DE LOGOS
// ============================================

async function handleLogoUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const gallery = document.getElementById('logos-gallery');
    
    for (let file of files) {
        try {
            // 1. Validar arquivo com ImageValidator
            const validator = UploadS3Config.validators.logos;
            const validation = await validator.validate(file);
            
            if (!validation.valid) {
                toaster.error(`${file.name}: ${validation.errors.join(', ')}`);
                continue;
            }
            
            // 2. Gerar preview antes do upload
            const preview = await validator.generatePreview(file);
            
            // 3. Adicionar preview temporário na galeria
            const tempId = 'temp-' + Date.now();
            addLogoPreviewTemp(preview.dataUrl, file.name, tempId);
            
            // 4. Fazer upload usando S3Uploader
            const uploader = new S3Uploader(
                UploadS3Config.endpoints.logoUploadUrl,
                UploadS3Config.endpoints.logoCreate,
                {
                    category: 'logos',
                    onProgress: (percent) => {
                        updateLogoProgress(tempId, percent);
                    },
                    onSuccess: (data) => {
                        // Substituir preview temporário pelo definitivo
                        replaceLogoPreview(tempId, data.logoId, data.previewUrl, file.name);
                        toaster.success(`Logo "${file.name}" enviado com sucesso!`);
                    },
                    onError: (error) => {
                        removeLogoPreview(tempId);
                        toaster.error(`Erro ao enviar ${file.name}: ${error.message}`);
                    }
                }
            );
            
            await uploader.upload(file, {
                name: file.name.replace(/\.[^/.]+$/, ''),  // Nome sem extensão
                logoType: 'principal',
                fileFormat: file.type.split('/')[1]
            });
            
        } catch (error) {
            console.error('Erro no upload de logo:', error);
            toaster.error(`Erro ao processar ${file.name}`);
        }
    }
    
    // Limpar input
    event.target.value = '';
}

// Adicionar preview temporário (durante upload)
function addLogoPreviewTemp(previewUrl, name, tempId) {
    const gallery = document.getElementById('logos-gallery');
    if (!gallery) return;
    
    const logoItem = document.createElement('div');
    logoItem.className = 'logo-preview-item logo-uploading';
    logoItem.dataset.logoId = tempId;
    
    logoItem.innerHTML = `
        <img src="${previewUrl}" alt="${name}">
        <div class="logo-preview-info">
            <span class="logo-preview-name">${name}</span>
            <span class="logo-preview-type">Enviando...</span>
        </div>
        <div class="logo-upload-progress">
            <div class="logo-upload-progress-bar" style="width: 0%"></div>
        </div>
    `;
    
    gallery.appendChild(logoItem);
}

// Atualizar progresso do upload
function updateLogoProgress(tempId, percent) {
    const logoItem = document.querySelector(`.logo-preview-item[data-logo-id="${tempId}"]`);
    if (!logoItem) return;
    
    const progressBar = logoItem.querySelector('.logo-upload-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
}

// Substituir preview temporário pelo definitivo
function replaceLogoPreview(tempId, logoId, previewUrl, name) {
    const logoItem = document.querySelector(`.logo-preview-item[data-logo-id="${tempId}"]`);
    if (!logoItem) return;
    
    logoItem.dataset.logoId = logoId;
    logoItem.classList.remove('logo-uploading');
    
    logoItem.innerHTML = `
        <img src="${previewUrl}" alt="${name}" class="lazy-s3-image" data-s3-key="${previewUrl}">
        <div class="logo-preview-info">
            <span class="logo-preview-name">${name}</span>
            <span class="logo-preview-type">Principal</span>
        </div>
        <button type="button" class="btn-remove-logo" data-action="remove-logo" data-logo-id="${logoId}" title="Remover">
            ×
        </button>
    `;
}

// Remover preview de logo
function removeLogoPreview(logoId) {
    const logoItem = document.querySelector(`.logo-preview-item[data-logo-id="${logoId}"]`);
    if (logoItem) {
        logoItem.classList.add('removing');
        setTimeout(() => logoItem.remove(), 200);
    }
}

// Remover logo (com confirmação e delete no backend)
async function removeLogo(logoId) {
    const confirmed = await showConfirm(
        'Esta ação não pode ser desfeita. O logo será removido permanentemente.',
        'Remover logo?'
    );
    if (!confirmed) return;
    
    try {
        const response = await fetch(
            UploadS3Config.endpoints.logoDelete.replace('{id}', logoId),
            {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }
        );
        
        const data = await response.json();
        
        if (data.success) {
            removeLogoPreview(logoId);
            toaster.success('Logo removido com sucesso!');
        } else {
            toaster.error(data.error || 'Erro ao remover logo');
        }
    } catch (error) {
        console.error('Erro ao remover logo:', error);
        toaster.error('Erro ao remover logo');
    }
}

// ============================================
// UPLOAD DE IMAGENS DE REFERÊNCIA
// ============================================

async function handleReferenceUpload(event) {
    console.log('DEBUG handleReferenceUpload chamado', {
        filesCount: event.target.files?.length,
        timestamp: new Date().toISOString()
    });
    
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const gallery = document.getElementById('references-gallery');
    
    for (let file of files) {
        try {
            // 1. Validar arquivo
            const validator = UploadS3Config.validators.references;
            const validation = await validator.validate(file);
            
            if (!validation.valid) {
                toaster.error(`${file.name}: ${validation.errors.join(', ')}`);
                continue;
            }
            
            // 2. Gerar preview
            const preview = await validator.generatePreview(file);
            
            // 3. Adicionar preview temporário
            const tempId = 'temp-' + Date.now();
            addReferencePreviewTemp(preview.dataUrl, file.name, tempId);
            
            // 4. Upload usando S3Uploader
            const uploader = new S3Uploader(
                UploadS3Config.endpoints.referenceUploadUrl,
                UploadS3Config.endpoints.referenceCreate,
                {
                    category: 'references',
                    onProgress: (percent) => {
                        updateReferenceProgress(tempId, percent);
                    },
                    onSuccess: (data) => {
                        replaceReferencePreview(tempId, data.referenceId, data.previewUrl, file.name);
                        toaster.success(`Imagem "${file.name}" enviada com sucesso!`);
                    },
                    onError: (error) => {
                        removeReferencePreview(tempId);
                        toaster.error(`Erro ao enviar ${file.name}: ${error.message}`);
                    }
                }
            );
            
            await uploader.upload(file, {
                name: file.name.replace(/\.[^/.]+$/, ''),
                category: 'geral'
            });
            
        } catch (error) {
            console.error('Erro no upload de referência:', error);
            toaster.error(`Erro ao processar ${file.name}`);
        }
    }
    
    // Limpar input
    event.target.value = '';
}

// Adicionar preview temporário de referência
function addReferencePreviewTemp(previewUrl, title, tempId) {
    const gallery = document.getElementById('references-gallery');
    if (!gallery) return;
    
    const refItem = document.createElement('div');
    refItem.className = 'reference-preview-item reference-uploading';
    refItem.dataset.refId = tempId;
    
    refItem.innerHTML = `
        <img src="${previewUrl}" alt="${title}">
        <div class="reference-preview-overlay">
            <span class="reference-preview-title">${title}</span>
            <div class="reference-upload-progress">
                <div class="reference-upload-progress-bar" style="width: 0%"></div>
            </div>
        </div>
    `;
    
    gallery.appendChild(refItem);
}

// Atualizar progresso
function updateReferenceProgress(tempId, percent) {
    const refItem = document.querySelector(`.reference-preview-item[data-ref-id="${tempId}"]`);
    if (!refItem) return;
    
    const progressBar = refItem.querySelector('.reference-upload-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
}

// Substituir preview temporário
function replaceReferencePreview(tempId, refId, previewUrl, title) {
    const refItem = document.querySelector(`.reference-preview-item[data-ref-id="${tempId}"]`);
    if (!refItem) return;
    
    refItem.dataset.refId = refId;
    refItem.classList.remove('reference-uploading');
    
    refItem.innerHTML = `
        <img src="${previewUrl}" alt="${title}" class="lazy-s3-image" data-s3-key="${previewUrl}">
        <div class="reference-preview-overlay">
            <span class="reference-preview-title">${title}</span>
            <button type="button" class="btn-remove-reference" data-action="remove-reference" data-ref-id="${refId}" title="Remover">
                ×
            </button>
        </div>
    `;
}

// Remover preview de referência
function removeReferencePreview(refId) {
    const refItem = document.querySelector(`.reference-preview-item[data-ref-id="${refId}"]`);
    if (refItem) {
        refItem.classList.add('removing');
        setTimeout(() => refItem.remove(), 200);
    }
}

// Remover referência (com confirmação)
async function removeReference(refId) {
    const confirmed = await showConfirm(
        'Esta ação não pode ser desfeita. A imagem será removida permanentemente.',
        'Remover imagem?'
    );
    if (!confirmed) return;
    
    try {
        const response = await fetch(
            UploadS3Config.endpoints.referenceDelete.replace('{id}', refId),
            {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }
        );
        
        const data = await response.json();
        
        if (data.success) {
            removeReferencePreview(refId);
            toaster.success('Imagem removida com sucesso!');
        } else {
            toaster.error(data.error || 'Erro ao remover imagem');
        }
    } catch (error) {
        console.error('Erro ao remover referência:', error);
        toaster.error('Erro ao remover imagem');
    }
}

// ============================================
// DRAG & DROP
// ============================================

function setupDragAndDrop(area, inputId) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        area.addEventListener(eventName, () => {
            area.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, () => {
            area.classList.remove('drag-over');
        }, false);
    });
    
    area.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        const input = document.getElementById(inputId);
        if (input) {
            input.files = files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }, false);
}

// ============================================
// UTILITÁRIOS
// ============================================

function getCookie(name) {
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

// ============================================
// INICIALIZAÇÃO
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar validators
    UploadS3Config.validators.logos = new ImageValidator('logos');
    UploadS3Config.validators.references = new ImageValidator('references');
    
    // Inicializar lazy loader para previews
    UploadS3Config.previewLoader = new ImagePreviewLoader(UploadS3Config.endpoints.previewUrl);
    UploadS3Config.previewLoader.observeAll('.lazy-s3-image');
    
    // Setup drag & drop
    const logoUploadArea = document.getElementById('logo-upload-area');
    const referenceUploadArea = document.getElementById('reference-upload-area');
    
    if (logoUploadArea) {
        setupDragAndDrop(logoUploadArea, 'logo-upload-input');
    }
    
    if (referenceUploadArea) {
        setupDragAndDrop(referenceUploadArea, 'reference-upload-input');
    }
    
    // Event listeners para inputs de arquivo
    const logoInput = document.getElementById('logo-upload-input');
    if (logoInput) {
        logoInput.addEventListener('change', handleLogoUpload);
    }
    
    const referenceInput = document.getElementById('reference-upload-input');
    if (referenceInput) {
        referenceInput.addEventListener('change', handleReferenceUpload);
    }
    
    // Event listeners para botões de trigger
    document.addEventListener('click', function(e) {
        // Trigger upload de logo
        if (e.target.matches('[data-action="trigger-logo-upload"]') || e.target.closest('[data-action="trigger-logo-upload"]')) {
            e.preventDefault();
            e.stopPropagation();
            document.getElementById('logo-upload-input')?.click();
        }
        
        // Trigger upload de referência
        if (e.target.matches('[data-action="trigger-reference-upload"]') || e.target.closest('[data-action="trigger-reference-upload"]')) {
            e.preventDefault();
            e.stopPropagation();
            document.getElementById('reference-upload-input')?.click();
        }
    });
    
    // Event delegation para botões de remover
    document.addEventListener('click', function(e) {
        const target = e.target;
        
        // Remover logo
        if (target.matches('[data-action="remove-logo"]') || target.closest('[data-action="remove-logo"]')) {
            const btn = target.matches('[data-action="remove-logo"]') ? target : target.closest('[data-action="remove-logo"]');
            const logoId = btn.dataset.logoId;
            if (logoId) removeLogo(logoId);
        }
        
        // Remover referência
        if (target.matches('[data-action="remove-reference"]') || target.closest('[data-action="remove-reference"]')) {
            const btn = target.matches('[data-action="remove-reference"]') ? target : target.closest('[data-action="remove-reference"]');
            const refId = btn.dataset.refId;
            if (refId) removeReference(refId);
        }
    });
});

// Expor funções globalmente (para compatibilidade)
window.handleLogoUpload = handleLogoUpload;
window.removeLogo = removeLogo;
window.handleReferenceUpload = handleReferenceUpload;
window.removeReference = removeReference;
