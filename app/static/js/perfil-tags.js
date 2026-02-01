/**
 * PERFIL-TAGS.JS - Tags para Página Perfil da Empresa
 * Integra sistema de tags com salvamento de sugestões do Perfil
 */

document.addEventListener('DOMContentLoaded', function() {
    initializePerfilTags();
});

function initializePerfilTags() {
    // Inicializar tags para recommended_words e words_to_avoid
    const tagsFields = ['recommended_words', 'words_to_avoid'];
    
    tagsFields.forEach(fieldName => {
        const container = document.getElementById(`tags-${fieldName}`);
        if (container) {
            const tagsData = container.dataset.tags;
            if (tagsData) {
                const tags = parseTagsJSON(tagsData);
                renderPerfilTags(fieldName, tags);
            }
        }
    });
    
    // Event listeners para inputs de tags
    document.querySelectorAll('.tag-input').forEach(input => {
        input.addEventListener('keydown', handlePerfilTagInput);
    });
}

function parseTagsJSON(value) {
    if (!value || value.trim() === '' || value === '[]') return [];
    
    try {
        // Tentar parsear como JSON
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) {
            return parsed;
        }
        return [];
    } catch (e) {
        // Se falhar, tentar parsear como texto com bullets
        const lines = value.split('\n').map(line => line.trim());
        const tags = lines
            .filter(line => line.startsWith('•'))
            .map(line => line.replace(/^•\s*/, '').trim())
            .filter(tag => tag.length > 0);
        
        return tags.length > 0 ? tags : [];
    }
}

function renderPerfilTags(fieldName, tags) {
    const container = document.getElementById(`tags-${fieldName}`);
    if (!container) return;
    
    container.innerHTML = '';
    
    tags.forEach(tag => {
        const tagElement = createPerfilTagElement(tag, fieldName);
        container.appendChild(tagElement);
    });
}

function createPerfilTagElement(text, fieldName) {
    const tag = document.createElement('div');
    tag.className = 'tag-item';
    tag.innerHTML = `
        <span>${escapeHtml(text)}</span>
        <button type="button" class="tag-remove" onclick="removePerfilTag(this, '${fieldName}')">×</button>
    `;
    return tag;
}

function handlePerfilTagInput(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        
        const input = e.target;
        const value = input.value.trim();
        
        if (value === '') return;
        
        const targetId = input.dataset.target;
        const fieldName = targetId.replace('tags-', '');
        
        addPerfilTag(value, fieldName);
        input.value = '';
    }
}

function addPerfilTag(text, fieldName) {
    const container = document.getElementById(`tags-${fieldName}`);
    if (!container) return;
    
    // Obter tags atuais
    const currentTags = getPerfilTags(fieldName);
    
    // Evitar duplicatas
    if (currentTags.includes(text)) {
        console.log(`Tag "${text}" já existe`);
        return;
    }
    
    // Adicionar nova tag
    const tagElement = createPerfilTagElement(text, fieldName);
    container.appendChild(tagElement);
    
    // Marcar campo como editado
    markFieldAsEdited(fieldName);
    
    console.log(`✅ Tag adicionada: ${text} em ${fieldName}`);
}

function removePerfilTag(button, fieldName) {
    const tagElement = button.closest('.tag-item');
    tagElement.classList.add('removing');
    
    setTimeout(() => {
        tagElement.remove();
        markFieldAsEdited(fieldName);
        console.log(`❌ Tag removida de ${fieldName}`);
    }, 150);
}

function getPerfilTags(fieldName) {
    const container = document.getElementById(`tags-${fieldName}`);
    if (!container) return [];
    
    const tags = [];
    container.querySelectorAll('.tag-item span').forEach(span => {
        tags.push(span.textContent);
    });
    return tags;
}

function markFieldAsEdited(fieldName) {
    // Integrar com sistema de edições do perfil.js
    if (window.editedFields) {
        const tags = getPerfilTags(fieldName);
        const tagsFormatted = tags.map(t => `• ${t}`).join('\n');
        window.editedFields[fieldName] = tagsFormatted;
        
        // Atualizar contador
        if (window.updateCounter) {
            window.updateCounter();
        }
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Expor funções globalmente
window.removePerfilTag = removePerfilTag;
window.getPerfilTags = getPerfilTags;
