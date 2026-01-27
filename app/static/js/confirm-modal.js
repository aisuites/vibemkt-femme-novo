/**
 * CONFIRM-MODAL.JS - Modal de Confirmação Profissional
 * Substitui window.confirm() por modal customizado
 */

class ConfirmModal {
    constructor() {
        this.modal = null;
        this.resolveCallback = null;
        this.init();
    }

    init() {
        // Criar estrutura do modal
        const modalHTML = `
            <div id="confirm-modal" class="confirm-modal-overlay" style="display: none;">
                <div class="confirm-modal">
                    <div class="confirm-modal-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                    </div>
                    <h3 class="confirm-modal-title">Confirmar ação</h3>
                    <p class="confirm-modal-message">Tem certeza que deseja continuar?</p>
                    <div class="confirm-modal-actions">
                        <button type="button" class="confirm-modal-btn confirm-modal-btn-cancel">Cancelar</button>
                        <button type="button" class="confirm-modal-btn confirm-modal-btn-confirm">Confirmar</button>
                    </div>
                </div>
            </div>
        `;

        // Adicionar ao body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('confirm-modal');

        // Event listeners
        const cancelBtn = this.modal.querySelector('.confirm-modal-btn-cancel');
        const confirmBtn = this.modal.querySelector('.confirm-modal-btn-confirm');
        const overlay = this.modal;

        cancelBtn.addEventListener('click', () => this.close(false));
        confirmBtn.addEventListener('click', () => this.close(true));
        
        // Fechar ao clicar no overlay
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.close(false);
            }
        });

        // Fechar com ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display !== 'none') {
                this.close(false);
            }
        });
    }

    show(message, title = 'Confirmar ação') {
        return new Promise((resolve) => {
            this.resolveCallback = resolve;
            
            // Atualizar conteúdo
            this.modal.querySelector('.confirm-modal-title').textContent = title;
            this.modal.querySelector('.confirm-modal-message').textContent = message;
            
            // Mostrar modal
            this.modal.style.display = 'flex';
            
            // Focus no botão de confirmar
            setTimeout(() => {
                this.modal.querySelector('.confirm-modal-btn-confirm').focus();
            }, 100);
        });
    }

    close(result) {
        this.modal.style.display = 'none';
        if (this.resolveCallback) {
            this.resolveCallback(result);
            this.resolveCallback = null;
        }
    }
}

// Instância global
window.confirmModal = new ConfirmModal();

// Helper para uso fácil
window.showConfirm = (message, title) => window.confirmModal.show(message, title);
