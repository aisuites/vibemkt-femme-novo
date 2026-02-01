/**
 * Perfil Visualização - JavaScript
 * Lazy loading de imagens e interações
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Lazy Loading de Imagens
    const lazyImages = document.querySelectorAll('.lazy-load');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Se já tem src, apenas adicionar classe loaded
                    if (img.src) {
                        img.classList.add('loaded');
                        observer.unobserve(img);
                        return;
                    }
                    
                    // Se tem data-src, carregar imagem
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.addEventListener('load', () => {
                            img.classList.add('loaded');
                        });
                        observer.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback para navegadores sem suporte
        lazyImages.forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
            }
            img.classList.add('loaded');
        });
    }
    
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Log para debug
    console.log('✅ Perfil Visualização carregado');
    console.log(`📊 ${lazyImages.length} imagens com lazy loading`);
});
