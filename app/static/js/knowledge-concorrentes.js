/**
 * CONCORRENTES.JS - Gerenciamento de Concorrentes
 * Padrão igual a colors.js: linhas dinâmicas com inputs + botão remover
 */

let concorrenteIndex = 0;

/**
 * Adiciona uma nova linha de concorrente (padrão cores)
 */
function addConcorrenteLine(nome = '', url = '') {
  const container = document.getElementById('concorrentes-inputs-container');
  if (!container) return;
  
  const item = document.createElement('div');
  item.className = 'concorrente-item';
  item.dataset.index = concorrenteIndex;
  
  item.innerHTML = `
    <div class="concorrente-inputs-wrapper">
      <input type="text" 
             class="concorrente-nome-input" 
             name="concorrentes[${concorrenteIndex}][nome]"
             value="${escapeHtml(nome)}"
             placeholder="Nome do concorrente"
             required>
      <input type="url" 
             class="concorrente-url-input" 
             name="concorrentes[${concorrenteIndex}][url]"
             value="${escapeHtml(url)}"
             placeholder="https://site-concorrente.com.br (opcional)">
    </div>
    <button 
      type="button" 
      class="btn-remove-item" 
      onclick="removeConcorrenteLine(${concorrenteIndex})"
      title="Remover concorrente"
    >
      Remover
    </button>
  `;
  
  container.appendChild(item);
  concorrenteIndex++;
  syncConcorrentesToForm();
}

/**
 * Remove uma linha de concorrente
 */
function removeConcorrenteLine(index) {
  const item = document.querySelector(`.concorrente-item[data-index="${index}"]`);
  if (item) {
    item.classList.add('removing');
    setTimeout(() => {
      item.remove();
      syncConcorrentesToForm();
    }, 200);
  }
}

/**
 * Sincroniza concorrentes para o campo hidden (para salvamento)
 */
function syncConcorrentesToForm() {
  const container = document.getElementById('concorrentes-inputs-container');
  if (!container) {
    console.error('❌ Container concorrentes-inputs-container não encontrado');
    return;
  }
  
  const items = container.querySelectorAll('.concorrente-item');
  const concorrentes = [];
  
  console.log(`🔍 syncConcorrentesToForm: ${items.length} linhas encontradas`);
  
  // Atualizar índices dos campos
  items.forEach((item, newIndex) => {
    const nomeInput = item.querySelector('.concorrente-nome-input');
    const urlInput = item.querySelector('.concorrente-url-input');
    
    if (nomeInput) {
      nomeInput.name = `concorrentes[${newIndex}][nome]`;
      const nome = nomeInput.value.trim();
      const url = urlInput ? urlInput.value.trim() : '';
      
      console.log(`  Linha ${newIndex}: nome="${nome}", url="${url}"`);
      
      if (nome) {
        concorrentes.push({
          nome: nome,
          url: url
        });
      }
    }
  });
  
  // Atualizar campo hidden para compatibilidade com backend
  const hiddenField = document.getElementById('concorrentes_data');
  if (hiddenField) {
    hiddenField.value = JSON.stringify(concorrentes);
    console.log(`✅ Campo hidden atualizado: ${hiddenField.value}`);
  } else {
    console.error('❌ Campo hidden concorrentes_data não encontrado');
  }
  
  console.log(`📊 Total de concorrentes válidos: ${concorrentes.length}`);
}

/**
 * Inicializa concorrentes existentes
 */
function initConcorrentes() {
  const jsonScript = document.getElementById('concorrentes_json_data');
  
  if (jsonScript) {
    try {
      const data = JSON.parse(jsonScript.textContent);
      if (Array.isArray(data) && data.length > 0) {
        data.forEach(concorrente => {
          addConcorrenteLine(concorrente.nome || '', concorrente.url || '');
        });
      }
    } catch (e) {
      console.error('Erro ao parsear concorrentes:', e);
    }
  }
}

/**
 * Escapa HTML para prevenir XSS
 */
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Logs de debug (apenas desenvolvimento)
if (window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1')) {
  console.log('🔍 DEBUG knowledge-concorrentes.js carregado (padrão cores)');
  console.log('- addConcorrenteLine:', typeof addConcorrenteLine !== 'undefined' ? '✅' : '❌');
  console.log('- removeConcorrenteLine:', typeof removeConcorrenteLine !== 'undefined' ? '✅' : '❌');
  console.log('- syncConcorrentesToForm:', typeof syncConcorrentesToForm !== 'undefined' ? '✅' : '❌');
}

// Inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initConcorrentes);
} else {
  initConcorrentes();
}
