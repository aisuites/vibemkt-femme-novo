/**
 * PERFIL-COLORS.JS - Gerenciamento de cores no Perfil
 * Layout minimalista: círculo + HEX + X + botão adicionar
 */

let perfilColorModal = null;
let currentColorPicker = null;

document.addEventListener('DOMContentLoaded', function() {
    initPerfilColorModal();
});

function initPerfilColorModal() {
    // Criar modal de adicionar cor
    const modalHTML = `
        <div id="perfil-color-modal" class="perfil-color-modal">
            <div class="perfil-color-modal-content">
                <h3 class="perfil-color-modal-header">Adicionar cor</h3>
                <div class="perfil-color-picker-wrapper">
                    <input type="color" 
                           id="perfil-color-picker" 
                           class="perfil-color-picker" 
                           value="#7A3D8A">
                    <input type="text" 
                           id="perfil-color-hex-input" 
                           class="perfil-color-hex-input" 
                           value="#7A3D8A" 
                           maxlength="7"
                           placeholder="#7A3D8A">
                </div>
                <div class="perfil-color-modal-actions">
                    <button type="button" class="btn-cancel" onclick="closePerfilColorModal()">Cancelar</button>
                    <button type="button" class="btn-confirm" onclick="confirmPerfilColor()">Adicionar</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    perfilColorModal = document.getElementById('perfil-color-modal');
    currentColorPicker = document.getElementById('perfil-color-picker');
    const hexInput = document.getElementById('perfil-color-hex-input');
    
    // Sincronizar color picker com input HEX
    if (currentColorPicker && hexInput) {
        currentColorPicker.addEventListener('input', function() {
            hexInput.value = this.value.toUpperCase();
        });
        
        hexInput.addEventListener('input', function() {
            const hex = this.value.trim();
            if (/^#[0-9A-F]{6}$/i.test(hex)) {
                currentColorPicker.value = hex;
            }
        });
    }
    
    // Fechar modal ao clicar fora
    perfilColorModal.addEventListener('click', function(e) {
        if (e.target === perfilColorModal) {
            closePerfilColorModal();
        }
    });
}

function addPerfilColor() {
    if (perfilColorModal) {
        perfilColorModal.classList.add('show');
        // Reset para cor padrão
        currentColorPicker.value = '#7A3D8A';
        document.getElementById('perfil-color-hex-input').value = '#7A3D8A';
    }
}

function closePerfilColorModal() {
    if (perfilColorModal) {
        perfilColorModal.classList.remove('show');
    }
}

async function confirmPerfilColor() {
    const hexValue = document.getElementById('perfil-color-hex-input').value.trim();
    
    // Validar HEX
    if (!/^#[0-9A-F]{6}$/i.test(hexValue)) {
        if (window.toaster) {
            toaster.error('Código HEX inválido. Use o formato #RRGGBB');
        } else {
            alert('Código HEX inválido. Use o formato #RRGGBB');
        }
        return;
    }
    
    try {
        // Salvar cor no backend
        const response = await fetch('/knowledge/perfil/add-color/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                hex_code: hexValue.toUpperCase()
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erro ao adicionar cor');
        }
        
        const data = await response.json();
        
        // Adicionar cor na lista
        const colorList = document.getElementById('perfil-color-list');
        if (colorList) {
            const colorItem = document.createElement('div');
            colorItem.className = 'perfil-color-item';
            colorItem.dataset.colorId = data.color_id;
            colorItem.innerHTML = `
                <div class="perfil-color-preview" style="background-color: ${hexValue};"></div>
                <span class="perfil-color-hex">${hexValue}</span>
                <button type="button" 
                        class="perfil-color-remove" 
                        onclick="removePerfilColor(${data.color_id})"
                        title="Remover cor">×</button>
            `;
            colorList.appendChild(colorItem);
        }
        
        closePerfilColorModal();
        
        if (window.toaster) {
            toaster.success('Cor adicionada com sucesso!');
        }
        
    } catch (error) {
        console.error('Erro ao adicionar cor:', error);
        if (window.toaster) {
            toaster.error(error.message || 'Erro ao adicionar cor');
        } else {
            alert(error.message || 'Erro ao adicionar cor');
        }
    }
}

async function removePerfilColor(colorId) {
    // Confirmar remoção
    const confirmed = window.confirmModal 
        ? await window.confirmModal.show('Tem certeza que deseja remover esta cor?', 'Remover cor')
        : confirm('Tem certeza que deseja remover esta cor?');
    
    if (!confirmed) return;
    
    try {
        // Remover cor no backend
        const response = await fetch('/knowledge/perfil/remove-color/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                color_id: colorId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erro ao remover cor');
        }
        
        // Remover cor da lista
        const colorItem = document.querySelector(`.perfil-color-item[data-color-id="${colorId}"]`);
        if (colorItem) {
            colorItem.style.opacity = '0';
            colorItem.style.transform = 'scale(0.8)';
            setTimeout(() => colorItem.remove(), 200);
        }
        
        if (window.toaster) {
            toaster.success('Cor removida com sucesso!');
        }
        
    } catch (error) {
        console.error('Erro ao remover cor:', error);
        if (window.toaster) {
            toaster.error(error.message || 'Erro ao remover cor');
        } else {
            alert(error.message || 'Erro ao remover cor');
        }
    }
}

function getCsrfToken() {
    const name = 'csrftoken';
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

// Expor funções globalmente
window.addPerfilColor = addPerfilColor;
window.removePerfilColor = removePerfilColor;
window.closePerfilColorModal = closePerfilColorModal;
window.confirmPerfilColor = confirmPerfilColor;
