/**
 * PERFIL-SOCIAL.JS - Gerenciamento de Redes Sociais no Perfil
 * Captura edições nos campos de redes sociais e adiciona ao editedFields
 */

document.addEventListener('DOMContentLoaded', function() {
    // Campos de redes sociais editáveis
    const socialFields = document.querySelectorAll('.social-network-field input[type="text"]');
    
    socialFields.forEach(field => {
        const fieldName = field.name; // ex: social_instagram_domain
        const originalValue = field.dataset.original || '';
        
        field.addEventListener('input', function() {
            const currentValue = this.value.trim();
            
            // Verificar se houve mudança
            if (currentValue !== originalValue) {
                window.editedFields[fieldName] = currentValue;
                this.classList.add('edited');
            } else {
                delete window.editedFields[fieldName];
                this.classList.remove('edited');
            }
            
            if (window.updateCounter) {
                window.updateCounter();
            }
        });
        
        field.addEventListener('blur', function() {
            const currentValue = this.value.trim();
            if (currentValue !== originalValue) {
                console.log(`Campo ${fieldName} editado: "${originalValue}" → "${currentValue}"`);
            }
        });
    });
});
