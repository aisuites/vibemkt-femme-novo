#!/bin/bash
# =============================================================================
# IAMKT - SCRIPT DE MIGRAÇÃO DE DADOS
# =============================================================================
# Este script automatiza a migração de dados do servidor antigo para o novo
# Uso: bash deploy_migrate.sh
# Data: 09/02/2026

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Configurações
BACKUP_DIR="/opt/backups/iamkt"
APP_DIR="/opt/iamkt"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# =============================================================================
# VERIFICAÇÕES INICIAIS
# =============================================================================
log_info "Verificando ambiente..."

if [ ! -d "$APP_DIR" ]; then
    log_error "Diretório da aplicação não encontrado: $APP_DIR"
    exit 1
fi

if ! docker ps | grep -q iamkt_postgres; then
    log_error "Container iamkt_postgres não está rodando"
    log_info "Execute: cd $APP_DIR && make up"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
log_success "Ambiente verificado"

# =============================================================================
# MENU DE OPÇÕES
# =============================================================================
echo ""
echo "========================================================================="
echo "  IAMKT - MIGRAÇÃO DE DADOS"
echo "========================================================================="
echo ""
echo "Escolha uma opção:"
echo ""
echo "  1) Criar backup do servidor atual"
echo "  2) Restaurar backup de arquivo local"
echo "  3) Restaurar backup de servidor remoto (via SCP)"
echo "  4) Migração completa (backup + transferência + restore)"
echo "  5) Sair"
echo ""
read -p "Opção: " OPTION

case $OPTION in
    1)
        # =============================================================================
        # OPÇÃO 1: CRIAR BACKUP
        # =============================================================================
        log_info "Criando backup do banco de dados..."
        
        cd "$APP_DIR"
        
        # Backup PostgreSQL
        docker exec -t iamkt_postgres pg_dump -U iamkt_user -Fc iamkt_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.dump"
        log_success "Backup do banco criado: $BACKUP_DIR/db_backup_$TIMESTAMP.dump"
        
        # Backup de mídia
        log_info "Criando backup de arquivos de mídia..."
        tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C app media/ 2>/dev/null || log_warning "Diretório media vazio ou não encontrado"
        log_success "Backup de mídia criado: $BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz"
        
        # Backup de arquivos estáticos
        log_info "Criando backup de arquivos estáticos..."
        tar -czf "$BACKUP_DIR/static_backup_$TIMESTAMP.tar.gz" -C app staticfiles/ 2>/dev/null || log_warning "Diretório staticfiles vazio ou não encontrado"
        log_success "Backup de estáticos criado: $BACKUP_DIR/static_backup_$TIMESTAMP.tar.gz"
        
        # Resumo
        echo ""
        log_success "BACKUP CONCLUÍDO!"
        echo ""
        echo "Arquivos criados em $BACKUP_DIR:"
        ls -lh "$BACKUP_DIR"/*_$TIMESTAMP.*
        echo ""
        ;;
        
    2)
        # =============================================================================
        # OPÇÃO 2: RESTAURAR DE ARQUIVO LOCAL
        # =============================================================================
        log_info "Restaurando backup de arquivo local..."
        
        echo ""
        echo "Arquivos disponíveis em $BACKUP_DIR:"
        ls -lh "$BACKUP_DIR"/*.dump 2>/dev/null || log_warning "Nenhum arquivo .dump encontrado"
        echo ""
        
        read -p "Digite o caminho completo do arquivo .dump: " DUMP_FILE
        
        if [ ! -f "$DUMP_FILE" ]; then
            log_error "Arquivo não encontrado: $DUMP_FILE"
            exit 1
        fi
        
        log_warning "ATENÇÃO: Esta operação irá SOBRESCREVER o banco de dados atual!"
        read -p "Deseja continuar? [s/N]: " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            log_info "Operação cancelada"
            exit 0
        fi
        
        log_info "Restaurando banco de dados..."
        cat "$DUMP_FILE" | docker exec -i iamkt_postgres pg_restore -U iamkt_user -d iamkt_db --clean --if-exists
        log_success "Banco de dados restaurado"
        
        # Restaurar mídia
        read -p "Deseja restaurar arquivos de mídia? [s/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            read -p "Digite o caminho do arquivo media_backup_*.tar.gz: " MEDIA_FILE
            if [ -f "$MEDIA_FILE" ]; then
                log_info "Restaurando arquivos de mídia..."
                tar -xzf "$MEDIA_FILE" -C "$APP_DIR/app/"
                sudo chown -R 1000:1000 "$APP_DIR/app/media/"
                log_success "Arquivos de mídia restaurados"
            else
                log_warning "Arquivo não encontrado: $MEDIA_FILE"
            fi
        fi
        
        # Reiniciar aplicação
        log_info "Reiniciando aplicação..."
        cd "$APP_DIR"
        docker compose restart iamkt_web
        log_success "Aplicação reiniciada"
        
        echo ""
        log_success "RESTAURAÇÃO CONCLUÍDA!"
        ;;
        
    3)
        # =============================================================================
        # OPÇÃO 3: RESTAURAR DE SERVIDOR REMOTO
        # =============================================================================
        log_info "Restaurando backup de servidor remoto..."
        
        read -p "Digite o usuário do servidor remoto: " REMOTE_USER
        read -p "Digite o IP/hostname do servidor remoto: " REMOTE_HOST
        read -p "Digite o caminho do backup no servidor remoto: " REMOTE_PATH
        
        log_info "Transferindo arquivo via SCP..."
        scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH" "$BACKUP_DIR/remote_backup_$TIMESTAMP.dump"
        log_success "Arquivo transferido"
        
        log_warning "ATENÇÃO: Esta operação irá SOBRESCREVER o banco de dados atual!"
        read -p "Deseja continuar? [s/N]: " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            log_info "Operação cancelada"
            exit 0
        fi
        
        log_info "Restaurando banco de dados..."
        cat "$BACKUP_DIR/remote_backup_$TIMESTAMP.dump" | docker exec -i iamkt_postgres pg_restore -U iamkt_user -d iamkt_db --clean --if-exists
        log_success "Banco de dados restaurado"
        
        # Reiniciar aplicação
        log_info "Reiniciando aplicação..."
        cd "$APP_DIR"
        docker compose restart iamkt_web
        log_success "Aplicação reiniciada"
        
        echo ""
        log_success "RESTAURAÇÃO CONCLUÍDA!"
        ;;
        
    4)
        # =============================================================================
        # OPÇÃO 4: MIGRAÇÃO COMPLETA
        # =============================================================================
        log_info "Iniciando migração completa..."
        
        echo ""
        log_warning "Esta opção irá:"
        echo "  1. Conectar ao servidor antigo via SSH"
        echo "  2. Criar backup no servidor antigo"
        echo "  3. Transferir backup para este servidor"
        echo "  4. Restaurar backup neste servidor"
        echo ""
        
        read -p "Digite o usuário do servidor ANTIGO: " OLD_USER
        read -p "Digite o IP/hostname do servidor ANTIGO: " OLD_HOST
        read -p "Digite o caminho da aplicação no servidor ANTIGO (ex: /opt/iamkt): " OLD_APP_PATH
        
        log_info "Conectando ao servidor antigo e criando backup..."
        
        # Executar backup no servidor remoto
        ssh "$OLD_USER@$OLD_HOST" "cd $OLD_APP_PATH && docker exec -t iamkt_postgres pg_dump -U iamkt_user -Fc iamkt_db > /tmp/iamkt_migration_$TIMESTAMP.dump"
        log_success "Backup criado no servidor antigo"
        
        # Transferir backup
        log_info "Transferindo backup..."
        scp "$OLD_USER@$OLD_HOST:/tmp/iamkt_migration_$TIMESTAMP.dump" "$BACKUP_DIR/"
        log_success "Backup transferido"
        
        # Transferir mídia
        read -p "Deseja transferir arquivos de mídia? [S/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            log_info "Criando backup de mídia no servidor antigo..."
            ssh "$OLD_USER@$OLD_HOST" "cd $OLD_APP_PATH && tar -czf /tmp/iamkt_media_$TIMESTAMP.tar.gz -C app media/"
            
            log_info "Transferindo mídia..."
            scp "$OLD_USER@$OLD_HOST:/tmp/iamkt_media_$TIMESTAMP.tar.gz" "$BACKUP_DIR/"
            log_success "Mídia transferida"
        fi
        
        # Restaurar
        log_warning "ATENÇÃO: Restauração irá SOBRESCREVER dados atuais!"
        read -p "Deseja continuar com a restauração? [s/N]: " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            log_info "Backup transferido mas não restaurado"
            log_info "Para restaurar manualmente: bash $0 e escolha opção 2"
            exit 0
        fi
        
        log_info "Restaurando banco de dados..."
        cat "$BACKUP_DIR/iamkt_migration_$TIMESTAMP.dump" | docker exec -i iamkt_postgres pg_restore -U iamkt_user -d iamkt_db --clean --if-exists
        log_success "Banco de dados restaurado"
        
        if [ -f "$BACKUP_DIR/iamkt_media_$TIMESTAMP.tar.gz" ]; then
            log_info "Restaurando mídia..."
            tar -xzf "$BACKUP_DIR/iamkt_media_$TIMESTAMP.tar.gz" -C "$APP_DIR/app/"
            sudo chown -R 1000:1000 "$APP_DIR/app/media/"
            log_success "Mídia restaurada"
        fi
        
        # Limpar arquivos temporários no servidor antigo
        log_info "Limpando arquivos temporários no servidor antigo..."
        ssh "$OLD_USER@$OLD_HOST" "rm -f /tmp/iamkt_migration_$TIMESTAMP.dump /tmp/iamkt_media_$TIMESTAMP.tar.gz"
        
        # Reiniciar aplicação
        log_info "Reiniciando aplicação..."
        cd "$APP_DIR"
        docker compose restart iamkt_web
        log_success "Aplicação reiniciada"
        
        echo ""
        log_success "MIGRAÇÃO COMPLETA CONCLUÍDA!"
        echo ""
        echo "Backups salvos em: $BACKUP_DIR"
        ;;
        
    5)
        log_info "Saindo..."
        exit 0
        ;;
        
    *)
        log_error "Opção inválida"
        exit 1
        ;;
esac

echo ""
echo "========================================================================="
log_success "OPERAÇÃO CONCLUÍDA!"
echo "========================================================================="
echo ""
