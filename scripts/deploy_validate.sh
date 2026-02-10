#!/bin/bash
# =============================================================================
# IAMKT - SCRIPT DE VALIDAÇÃO PÓS-DEPLOY
# =============================================================================
# Este script valida se o deploy foi realizado com sucesso
# Uso: bash deploy_validate.sh
# Data: 09/02/2026

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

# Configurações
APP_DIR="/opt/iamkt"
DOMAIN="${1:-localhost}"

echo ""
echo "========================================================================="
echo "  IAMKT - VALIDAÇÃO PÓS-DEPLOY"
echo "========================================================================="
echo ""
log_info "Domínio: $DOMAIN"
log_info "Diretório: $APP_DIR"
echo ""

# =============================================================================
# 1. VERIFICAR CONTAINERS
# =============================================================================
echo "1. Verificando containers..."

if docker ps | grep -q iamkt_web; then
    log_success "Container iamkt_web está rodando"
else
    log_error "Container iamkt_web NÃO está rodando"
fi

if docker ps | grep -q iamkt_postgres; then
    log_success "Container iamkt_postgres está rodando"
else
    log_error "Container iamkt_postgres NÃO está rodando"
fi

if docker ps | grep -q iamkt_redis; then
    log_success "Container iamkt_redis está rodando"
else
    log_error "Container iamkt_redis NÃO está rodando"
fi

if docker ps | grep -q iamkt_celery; then
    log_success "Container iamkt_celery está rodando"
else
    log_error "Container iamkt_celery NÃO está rodando"
fi

# =============================================================================
# 2. VERIFICAR HEALTH CHECKS
# =============================================================================
echo ""
echo "2. Verificando health checks..."

WEB_HEALTH=$(docker inspect iamkt_web --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
if [ "$WEB_HEALTH" = "healthy" ]; then
    log_success "Health check iamkt_web: healthy"
elif [ "$WEB_HEALTH" = "none" ]; then
    log_warning "Health check iamkt_web: não configurado"
else
    log_error "Health check iamkt_web: $WEB_HEALTH"
fi

# =============================================================================
# 3. VERIFICAR CONECTIVIDADE DOS SERVIÇOS
# =============================================================================
echo ""
echo "3. Verificando conectividade..."

# PostgreSQL
if docker exec iamkt_postgres pg_isready -U iamkt_user &>/dev/null; then
    log_success "PostgreSQL está acessível"
else
    log_error "PostgreSQL NÃO está acessível"
fi

# Redis
if docker exec iamkt_redis redis-cli ping &>/dev/null; then
    log_success "Redis está acessível"
else
    log_error "Redis NÃO está acessível"
fi

# Django
if docker exec iamkt_web curl -sf http://localhost:8000/health/ &>/dev/null; then
    log_success "Django está respondendo"
else
    log_error "Django NÃO está respondendo"
fi

# =============================================================================
# 4. VERIFICAR MIGRATIONS
# =============================================================================
echo ""
echo "4. Verificando migrations..."

MIGRATIONS_OUTPUT=$(docker exec iamkt_web python manage.py showmigrations 2>&1)
if echo "$MIGRATIONS_OUTPUT" | grep -q "\[ \]"; then
    log_error "Existem migrations não aplicadas"
    echo "$MIGRATIONS_OUTPUT" | grep "\[ \]" | head -5
else
    log_success "Todas as migrations estão aplicadas"
fi

# =============================================================================
# 5. VERIFICAR VOLUMES
# =============================================================================
echo ""
echo "5. Verificando volumes..."

if docker volume ls | grep -q iamkt_postgres_data; then
    log_success "Volume iamkt_postgres_data existe"
else
    log_error "Volume iamkt_postgres_data NÃO existe"
fi

if docker volume ls | grep -q iamkt_redis_data; then
    log_success "Volume iamkt_redis_data existe"
else
    log_error "Volume iamkt_redis_data NÃO existe"
fi

if docker volume ls | grep -q iamkt_media; then
    log_success "Volume iamkt_media existe"
else
    log_error "Volume iamkt_media NÃO existe"
fi

if docker volume ls | grep -q iamkt_static; then
    log_success "Volume iamkt_static existe"
else
    log_error "Volume iamkt_static NÃO existe"
fi

# =============================================================================
# 6. VERIFICAR REDES
# =============================================================================
echo ""
echo "6. Verificando redes..."

if docker network ls | grep -q iamkt_internal; then
    log_success "Rede iamkt_internal existe"
else
    log_error "Rede iamkt_internal NÃO existe"
fi

if docker network ls | grep -q traefik_proxy; then
    log_success "Rede traefik_proxy existe"
else
    log_warning "Rede traefik_proxy NÃO existe (necessária para Traefik)"
fi

# =============================================================================
# 7. VERIFICAR ISOLAMENTO (PORTAS)
# =============================================================================
echo ""
echo "7. Verificando isolamento de portas..."

if netstat -tuln 2>/dev/null | grep -E ':(5432|6379)' | grep -q LISTEN; then
    log_error "PostgreSQL ou Redis estão expostos externamente (RISCO DE SEGURANÇA)"
    netstat -tuln | grep -E ':(5432|6379)'
else
    log_success "PostgreSQL e Redis NÃO estão expostos externamente"
fi

# =============================================================================
# 8. VERIFICAR LOGS (ERROS RECENTES)
# =============================================================================
echo ""
echo "8. Verificando logs recentes..."

WEB_ERRORS=$(docker logs iamkt_web --since 5m 2>&1 | grep -i error | wc -l)
if [ "$WEB_ERRORS" -eq 0 ]; then
    log_success "Nenhum erro nos logs do iamkt_web (últimos 5 min)"
else
    log_warning "$WEB_ERRORS erros encontrados nos logs do iamkt_web"
    docker logs iamkt_web --since 5m 2>&1 | grep -i error | tail -3
fi

CELERY_ERRORS=$(docker logs iamkt_celery --since 5m 2>&1 | grep -i error | wc -l)
if [ "$CELERY_ERRORS" -eq 0 ]; then
    log_success "Nenhum erro nos logs do iamkt_celery (últimos 5 min)"
else
    log_warning "$CELERY_ERRORS erros encontrados nos logs do iamkt_celery"
fi

# =============================================================================
# 9. VERIFICAR ARQUIVOS ESTÁTICOS
# =============================================================================
echo ""
echo "9. Verificando arquivos estáticos..."

if [ -d "$APP_DIR/app/staticfiles" ]; then
    STATIC_COUNT=$(find "$APP_DIR/app/staticfiles" -type f 2>/dev/null | wc -l)
    if [ "$STATIC_COUNT" -gt 0 ]; then
        log_success "Arquivos estáticos coletados ($STATIC_COUNT arquivos)"
    else
        log_warning "Diretório staticfiles vazio (execute collectstatic)"
    fi
else
    log_warning "Diretório staticfiles não existe"
fi

# =============================================================================
# 10. VERIFICAR ACESSO HTTP/HTTPS
# =============================================================================
echo ""
echo "10. Verificando acesso HTTP/HTTPS..."

# HTTP
if curl -sf -o /dev/null "http://$DOMAIN/health/" 2>/dev/null; then
    log_success "Endpoint HTTP acessível: http://$DOMAIN/health/"
else
    log_warning "Endpoint HTTP não acessível (pode ser normal se usar apenas HTTPS)"
fi

# HTTPS
if curl -sfk -o /dev/null "https://$DOMAIN/health/" 2>/dev/null; then
    log_success "Endpoint HTTPS acessível: https://$DOMAIN/health/"
else
    log_warning "Endpoint HTTPS não acessível"
fi

# =============================================================================
# 11. VERIFICAR BANCO DE DADOS
# =============================================================================
echo ""
echo "11. Verificando banco de dados..."

USER_COUNT=$(docker exec iamkt_postgres psql -U iamkt_user -d iamkt_db -t -c "SELECT COUNT(*) FROM auth_user;" 2>/dev/null | tr -d ' ')
if [ -n "$USER_COUNT" ] && [ "$USER_COUNT" -gt 0 ]; then
    log_success "Banco de dados contém $USER_COUNT usuários"
else
    log_warning "Banco de dados vazio ou erro ao consultar"
fi

# =============================================================================
# 12. VERIFICAR CELERY
# =============================================================================
echo ""
echo "12. Verificando Celery..."

if docker exec iamkt_celery celery -A sistema inspect ping 2>&1 | grep -q "pong"; then
    log_success "Celery worker está respondendo"
else
    log_error "Celery worker NÃO está respondendo"
fi

# =============================================================================
# 13. VERIFICAR ESPAÇO EM DISCO
# =============================================================================
echo ""
echo "13. Verificando espaço em disco..."

DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    log_success "Espaço em disco OK (${DISK_USAGE}% usado)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    log_warning "Espaço em disco alto (${DISK_USAGE}% usado)"
else
    log_error "Espaço em disco crítico (${DISK_USAGE}% usado)"
fi

# =============================================================================
# 14. VERIFICAR MEMÓRIA
# =============================================================================
echo ""
echo "14. Verificando memória..."

MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100}')
if [ "$MEM_USAGE" -lt 80 ]; then
    log_success "Uso de memória OK (${MEM_USAGE}%)"
elif [ "$MEM_USAGE" -lt 90 ]; then
    log_warning "Uso de memória alto (${MEM_USAGE}%)"
else
    log_error "Uso de memória crítico (${MEM_USAGE}%)"
fi

# =============================================================================
# RESUMO
# =============================================================================
echo ""
echo "========================================================================="
echo "  RESUMO DA VALIDAÇÃO"
echo "========================================================================="
echo ""
echo -e "${GREEN}Testes Passados:${NC} $PASSED"
echo -e "${YELLOW}Avisos:${NC} $WARNINGS"
echo -e "${RED}Falhas:${NC} $FAILED"
echo ""

if [ "$FAILED" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✓ DEPLOY VALIDADO COM SUCESSO!${NC}"
    echo ""
    exit 0
elif [ "$FAILED" -eq 0 ]; then
    echo -e "${YELLOW}⚠ DEPLOY OK COM AVISOS${NC}"
    echo ""
    echo "Revise os avisos acima e corrija se necessário."
    exit 0
else
    echo -e "${RED}✗ DEPLOY COM PROBLEMAS${NC}"
    echo ""
    echo "Corrija as falhas acima antes de prosseguir."
    echo ""
    echo "Comandos úteis:"
    echo "  - Ver logs: cd $APP_DIR && make logs"
    echo "  - Reiniciar: cd $APP_DIR && docker compose restart"
    echo "  - Recriar: cd $APP_DIR && make recreate"
    exit 1
fi
