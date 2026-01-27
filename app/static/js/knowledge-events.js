/**
 * Knowledge Base - Event Listeners
 * Remove inline JavaScript (onclick, onchange) seguindo padrões do projeto
 */

document.addEventListener('DOMContentLoaded', () => {
    initSegmentEvents();
    initColorEvents();
    initFontEvents();
    initUploadEvents();
    initModalEvents();
    initTemplateEvents();
});

/**
 * SEGMENTOS INTERNOS
 */
function initSegmentEvents() {
    // Botão novo segmento
    const newSegmentBtn = document.querySelector('[data-action="new-segment"]');
    if (newSegmentBtn) {
        newSegmentBtn.addEventListener('click', () => {
            if (typeof openSegmentModal === 'function') {
                openSegmentModal();
            }
        });
    }

    // Toggle segments (checkbox)
    document.querySelectorAll('[data-action="toggle-segment"]').forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            const segmentId = parseInt(e.target.dataset.segmentId);
            const isActive = e.target.checked;
            if (typeof toggleSegment === 'function') {
                toggleSegment(segmentId, isActive);
            }
        });
    });

    // Editar segmento
    document.querySelectorAll('[data-action="edit-segment"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const segmentId = parseInt(e.currentTarget.dataset.segmentId);
            if (typeof editSegment === 'function') {
                editSegment(segmentId);
            }
        });
    });
}

/**
 * CORES
 */
function initColorEvents() {
    // Botão adicionar cor
    const addColorBtn = document.querySelector('[data-action="add-color"]');
    if (addColorBtn) {
        addColorBtn.addEventListener('click', () => {
            if (typeof addColor === 'function') {
                addColor();
            }
        });
    }

    // Remover cor (delegação de eventos)
    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="remove-color"]')) {
            const btn = e.target.closest('[data-action="remove-color"]');
            if (typeof removeColor === 'function') {
                removeColor(btn);
            }
        }
    });
}

/**
 * FONTES
 */
function initFontEvents() {
    // Botão adicionar fonte
    const addFonteBtn = document.querySelector('[data-action="add-fonte"]');
    if (addFonteBtn) {
        addFonteBtn.addEventListener('click', () => {
            if (typeof addFonte === 'function') {
                addFonte();
            }
        });
    }

    // Remover fonte (delegação de eventos)
    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="remove-fonte"]')) {
            const btn = e.target.closest('[data-action="remove-fonte"]');
            if (typeof removeFonte === 'function') {
                removeFonte(btn);
            }
        }
    });
}

/**
 * UPLOADS
 */
function initUploadEvents() {
    // Event listener para remover logo
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="remove-logo"]') || e.target.closest('[data-action="remove-logo"]')) {
            const btn = e.target.matches('[data-action="remove-logo"]') ? e.target : e.target.closest('[data-action="remove-logo"]');
            const logoId = btn.dataset.logoId;
            if (logoId && typeof removeLogo === 'function') {
                removeLogo(logoId);
            }
        }
        
        // Event listener para remover referência
        if (e.target.matches('[data-action="remove-reference"]') || e.target.closest('[data-action="remove-reference"]')) {
            const btn = e.target.matches('[data-action="remove-reference"]') ? e.target : e.target.closest('[data-action="remove-reference"]');
            const refId = btn.dataset.refId;
            if (refId && typeof removeReference === 'function') {
                removeReference(refId);
            }
        }
    });
}

/**
 * MODAL
 */
function initModalEvents() {
    // Fechar modal (overlay)
    const modalOverlay = document.querySelector('.modal-overlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', () => {
            if (typeof closeSegmentModal === 'function') {
                closeSegmentModal();
            }
        });
    }

    // Fechar modal (botão X)
    const modalCloseBtn = document.querySelector('.modal-close');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            if (typeof closeSegmentModal === 'function') {
                closeSegmentModal();
            }
        });
    }
    
    // Botão cancelar no modal
    const cancelBtn = document.querySelector('[data-action="cancel-segment"]');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            if (typeof closeSegmentModal === 'function') {
                closeSegmentModal();
            }
        });
    }
    
    // Botão salvar no modal
    const saveBtn = document.querySelector('[data-action="save-segment"]');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            if (typeof saveSegment === 'function') {
                saveSegment();
            }
        });
    }
}

/**
 * TEMPLATES
 */
function initTemplateEvents() {
    // Link templates (em desenvolvimento)
    const templateLink = document.querySelector('[data-action="open-templates"]');
    if (templateLink) {
        templateLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.toaster) {
                toaster.info('Página de templates em desenvolvimento');
            }
        });
    }
}

/**
 * Função helper para mostrar notificações
 */
function showNotification(message, type = 'info') {
    if (window.toaster) {
        toaster[type](message);
    } else {
        console[type === 'error' ? 'error' : 'log'](message);
    }
}

// Exportar para uso global se necessário
window.showNotification = showNotification;
