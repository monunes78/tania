#!/bin/bash
# ─────────────────────────────────────────────────────────────
# TanIA — Deploy Script
# Uso: ./deploy.sh [branch]
# Padrão: branch main
# ─────────────────────────────────────────────────────────────

set -euo pipefail

BRANCH=${1:-main}
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/logs/deploy.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$APP_DIR/logs"

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════"
log "Iniciando deploy TanIA — branch: $BRANCH"
log "═══════════════════════════════════════════"

# ─── 1. Pull do GitHub ───────────────────────────────────────
log "▸ Atualizando código..."
cd "$APP_DIR"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
log "✓ Código atualizado"

# ─── 2. Converter certificado se necessário ──────────────────
if [ -f "$APP_DIR/cert/TanacWildcard2025.pfx" ]; then
    if [ ! -f "$APP_DIR/nginx/ssl/cert.pem" ] || \
       [ "$APP_DIR/cert/TanacWildcard2025.pfx" -nt "$APP_DIR/nginx/ssl/cert.pem" ]; then
        log "▸ Convertendo certificado .pfx → PEM..."
        mkdir -p "$APP_DIR/nginx/ssl"
        openssl pkcs12 -in "$APP_DIR/cert/TanacWildcard2025.pfx" \
            -nokeys -out "$APP_DIR/nginx/ssl/cert.pem" -passin pass: 2>/dev/null || \
        openssl pkcs12 -in "$APP_DIR/cert/TanacWildcard2025.pfx" \
            -nokeys -out "$APP_DIR/nginx/ssl/cert.pem"
        openssl pkcs12 -in "$APP_DIR/cert/TanacWildcard2025.pfx" \
            -nocerts -nodes -out "$APP_DIR/nginx/ssl/key.pem" -passin pass: 2>/dev/null || \
        openssl pkcs12 -in "$APP_DIR/cert/TanacWildcard2025.pfx" \
            -nocerts -nodes -out "$APP_DIR/nginx/ssl/key.pem"
        log "✓ Certificado convertido"
    fi
fi

# ─── 3. Build e restart dos containers ───────────────────────
log "▸ Construindo e reiniciando containers..."
docker-compose pull --ignore-pull-failures 2>/dev/null || true
docker-compose up --build -d
log "✓ Containers atualizados"

# ─── 4. Migrations do banco ──────────────────────────────────
log "▸ Executando migrations..."
sleep 5  # aguarda backend subir
docker-compose exec -T backend alembic upgrade head
log "✓ Migrations executadas"

# ─── 5. Health check ─────────────────────────────────────────
log "▸ Verificando saúde dos serviços..."
sleep 3
if curl -sf http://localhost/api/health > /dev/null 2>&1; then
    log "✓ API respondendo"
else
    log "⚠ API não respondeu ao health check — verifique os logs"
fi

# ─── 6. Limpar imagens antigas ───────────────────────────────
log "▸ Limpando imagens Docker não utilizadas..."
docker image prune -f > /dev/null 2>&1 || true
log "✓ Limpeza concluída"

log "═══════════════════════════════════════════"
log "✅ Deploy concluído com sucesso!"
log "   URL: https://tania.tanac.com.br"
log "═══════════════════════════════════════════"
