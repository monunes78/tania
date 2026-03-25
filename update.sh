#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  TanIA — Atualização Automática
#  Uso: ./update.sh [--force-rebuild] [--branch nome]
#
#  O que este script faz:
#   1. Verifica modificações locais (git status)
#   2. Faz git pull da branch configurada
#   3. Detecta o que mudou (backend, frontend, infra, migrations)
#   4. Reconstrói apenas os serviços afetados
#   5. Executa novas migrations
#   6. Recarrega nginx se configuração mudou
#   7. Verifica saúde após atualização
#   8. Limpa imagens antigas
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Cores ───────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$APP_DIR/logs/update.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$APP_DIR/logs"

# ── Parâmetros ──────────────────────────────────────────────────
FORCE_REBUILD=false
BRANCH=""

for arg in "$@"; do
    case $arg in
        --force-rebuild) FORCE_REBUILD=true ;;
        --branch) shift; BRANCH="$1" ;;
        --branch=*) BRANCH="${arg#*=}" ;;
    esac
done

# ── Funções de log ──────────────────────────────────────────────
log()   { echo -e "${GREEN}[✓]${RESET} $1" | tee -a "$LOG_FILE"; }
info()  { echo -e "${BLUE}[▸]${RESET} $1" | tee -a "$LOG_FILE"; }
warn()  { echo -e "${YELLOW}[!]${RESET} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[✗]${RESET} $1" | tee -a "$LOG_FILE"; }
header(){ echo -e "\n${BOLD}${BLUE}══ $1 ══${RESET}" | tee -a "$LOG_FILE"; }

echo "" | tee -a "$LOG_FILE"
echo -e "${BOLD}${BLUE}" | tee -a "$LOG_FILE"
echo "╔═══════════════════════════════════════════╗" | tee -a "$LOG_FILE"
echo "║        TanIA — Atualização                ║" | tee -a "$LOG_FILE"
echo "║        $TIMESTAMP          ║" | tee -a "$LOG_FILE"
echo "╚═══════════════════════════════════════════╝" | tee -a "$LOG_FILE"
echo -e "${RESET}" | tee -a "$LOG_FILE"

# ──────────────────────────────────────────────────────────────
# 1. PRÉ-REQUISITOS
# ──────────────────────────────────────────────────────────────
header "Verificações iniciais"

# Deve estar no diretório do projeto
if [[ ! -f "$APP_DIR/docker-compose.yml" ]]; then
    error "docker-compose.yml não encontrado em $APP_DIR"
    error "Execute este script a partir do diretório /opt/tania"
    exit 1
fi

# Docker deve estar disponível
if ! docker info > /dev/null 2>&1; then
    error "Docker não está acessível. Verifique:"
    error "  1. Docker está rodando: sudo systemctl status docker"
    error "  2. Seu usuário está no grupo docker: id"
    error "  3. Se acabou de ser adicionado ao grupo: newgrp docker"
    exit 1
fi

# Git deve estar configurado
if ! git -C "$APP_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    error "Diretório não é um repositório git: $APP_DIR"
    exit 1
fi

log "Pré-requisitos OK."

# ──────────────────────────────────────────────────────────────
# 2. VERIFICAR MODIFICAÇÕES LOCAIS
# ──────────────────────────────────────────────────────────────
header "Status do repositório"

cd "$APP_DIR"

# Guardar HEAD atual antes do pull
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "none")

# Verificar branch atual
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
TARGET_BRANCH="${BRANCH:-$CURRENT_BRANCH}"

info "Branch atual: $CURRENT_BRANCH"

# Verificar modificações locais nos arquivos de aplicação (excluindo .env e logs)
LOCAL_CHANGES=$(git diff --name-only HEAD 2>/dev/null | grep -v "^\.env" | grep -v "^logs/" || true)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | grep -v "^\.env" | grep -v "^logs/" || true)

if [[ -n "$LOCAL_CHANGES" ]]; then
    warn "Modificações locais detectadas:"
    echo "$LOCAL_CHANGES" | while read -r f; do warn "  ~ $f"; done
    echo ""
    echo -e "${YELLOW}Opções:${RESET}"
    echo "  1) Descartar modificações locais e atualizar (git stash)"
    echo "  2) Manter modificações e cancelar atualização"
    echo -n "Escolha [1/2]: "
    read -r CHOICE
    if [[ "$CHOICE" == "1" ]]; then
        git stash push -m "auto-stash antes do update $TIMESTAMP"
        log "Modificações locais guardadas com git stash."
        warn "Para restaurar depois: git stash pop"
    else
        error "Atualização cancelada. Resolva os conflitos manualmente."
        exit 1
    fi
fi

# ──────────────────────────────────────────────────────────────
# 3. GIT PULL
# ──────────────────────────────────────────────────────────────
header "Atualizando código"

info "Fazendo git fetch..."
if ! git fetch origin 2>&1 | tee -a "$LOG_FILE"; then
    error "Falha no git fetch. Verifique a conexão com o GitHub."
    exit 1
fi

# Verificar se há atualizações disponíveis
BEHIND=$(git rev-list HEAD...origin/"$TARGET_BRANCH" --count 2>/dev/null || echo "0")

if [[ "$BEHIND" == "0" ]] && [[ "$FORCE_REBUILD" != "true" ]]; then
    log "Sistema já está na versão mais recente (branch $TARGET_BRANCH)."
    echo ""
    echo "Use --force-rebuild para forçar rebuild mesmo sem mudanças."
    echo "Use --branch nome para atualizar de uma branch específica."

    # Ainda verifica saúde dos serviços
    echo ""
    header "Verificação de saúde"
    docker compose ps 2>/dev/null | tee -a "$LOG_FILE"
    exit 0
fi

info "Fazendo git pull origin $TARGET_BRANCH..."
if ! git pull origin "$TARGET_BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
    error "Falha no git pull. Possíveis causas:"
    error "  — Conflito de merge: resolva manualmente"
    error "  — Branch não existe: verifique o nome"
    exit 1
fi

NEW_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "none")
log "Código atualizado: ${OLD_HEAD:0:8} → ${NEW_HEAD:0:8}"

# ──────────────────────────────────────────────────────────────
# 4. DETECTAR O QUE MUDOU
# ──────────────────────────────────────────────────────────────
header "Análise de mudanças"

CHANGED=""
if [[ "$OLD_HEAD" != "none" ]] && [[ "$OLD_HEAD" != "$NEW_HEAD" ]]; then
    CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" 2>/dev/null || echo "")
fi

if [[ "$FORCE_REBUILD" == "true" ]]; then
    info "Rebuild forçado — reconstruindo tudo."
    REBUILD_BACKEND=true
    REBUILD_FRONTEND=true
    RUN_MIGRATIONS=true
else
    REBUILD_BACKEND=false
    REBUILD_FRONTEND=false
    REBUILD_ALL=false
    RELOAD_NGINX=false
    RESTART_LITELLM=false
    RUN_MIGRATIONS=false

    if [[ -n "$CHANGED" ]]; then
        info "Arquivos alterados:"
        echo "$CHANGED" | while read -r f; do info "  → $f"; done

        # docker-compose.yml ou qualquer Dockerfile → rebuild completo
        if echo "$CHANGED" | grep -qE "^docker-compose\.yml|Dockerfile$"; then
            REBUILD_ALL=true
            info "Detectado: docker-compose ou Dockerfile alterado → rebuild completo"
        fi

        # Arquivos Python do backend ou suas dependências
        if echo "$CHANGED" | grep -qE "^backend/|^scripts/"; then
            REBUILD_BACKEND=true
        fi

        # Arquivos do frontend
        if echo "$CHANGED" | grep -qE "^frontend/"; then
            REBUILD_FRONTEND=true
        fi

        # Novas migrations
        if echo "$CHANGED" | grep -qE "^backend/alembic/versions/"; then
            RUN_MIGRATIONS=true
        fi

        # nginx.conf alterado
        if echo "$CHANGED" | grep -qE "^nginx/nginx\.conf"; then
            RELOAD_NGINX=true
        fi

        # litellm config alterado
        if echo "$CHANGED" | grep -qE "^litellm-proxy/"; then
            RESTART_LITELLM=true
        fi

        # Dependências Python alteradas → forçar rebuild backend
        if echo "$CHANGED" | grep -qE "pyproject\.toml|requirements.*\.txt"; then
            REBUILD_BACKEND=true
            info "Detectado: dependências Python alteradas → rebuild backend"
        fi

        # Dependências Node alteradas → forçar rebuild frontend
        if echo "$CHANGED" | grep -qE "package\.json|package-lock\.json"; then
            REBUILD_FRONTEND=true
            info "Detectado: package.json alterado → rebuild frontend"
        fi
    else
        # Sem mudanças detectadas no git, mas FORCE_REBUILD é false e estamos aqui
        # Pode acontecer em primeiro run ou mudança sem commit
        warn "Nenhuma mudança detectada no git diff. Use --force-rebuild se necessário."
    fi

    if [[ "$REBUILD_ALL" == "true" ]]; then
        REBUILD_BACKEND=true
        REBUILD_FRONTEND=true
    fi
fi

# Sempre verifica migrations ao atualizar (alembic é idempotente)
RUN_MIGRATIONS=true

# Resumo do plano
echo ""
info "Plano de atualização:"
[[ "$REBUILD_BACKEND" == "true" ]]  && info "  [+] Rebuild: backend, celery, celery-beat"
[[ "$REBUILD_FRONTEND" == "true" ]] && info "  [+] Rebuild: frontend"
[[ "$RUN_MIGRATIONS" == "true" ]]   && info "  [+] Executar migrations"
[[ "$RELOAD_NGINX" == "true" ]]     && info "  [+] Reload nginx"
[[ "$RESTART_LITELLM" == "true" ]]  && info "  [+] Restart litellm"
[[ "$REBUILD_BACKEND" != "true" ]] && [[ "$REBUILD_FRONTEND" != "true" ]] && \
    info "  [~] Sem rebuild necessário"

# ──────────────────────────────────────────────────────────────
# 5. REBUILD DOS SERVIÇOS AFETADOS
# ──────────────────────────────────────────────────────────────
header "Rebuild e restart"

if [[ "$REBUILD_BACKEND" == "true" ]]; then
    info "Reconstruindo imagem do backend..."
    docker compose build backend 2>&1 | tee -a "$LOG_FILE"

    info "Reiniciando backend, celery e celery-beat..."
    docker compose up -d --no-deps backend celery celery-beat 2>&1 | tee -a "$LOG_FILE"
    log "Backend reiniciado."
fi

if [[ "$REBUILD_FRONTEND" == "true" ]]; then
    info "Reconstruindo imagem do frontend..."
    docker compose build frontend 2>&1 | tee -a "$LOG_FILE"

    info "Reiniciando frontend..."
    docker compose up -d --no-deps frontend 2>&1 | tee -a "$LOG_FILE"
    log "Frontend reiniciado."
fi

if [[ "$RESTART_LITELLM" == "true" ]]; then
    info "Reiniciando litellm..."
    docker compose restart litellm 2>&1 | tee -a "$LOG_FILE"
    log "LiteLLM reiniciado."
fi

if [[ "$RELOAD_NGINX" == "true" ]]; then
    info "Recarregando configuração do nginx..."
    if docker compose exec -T nginx nginx -t 2>/dev/null; then
        docker compose exec -T nginx nginx -s reload 2>&1 | tee -a "$LOG_FILE"
        log "Nginx recarregado."
    else
        warn "nginx -t falhou — mantendo configuração atual."
        docker compose logs nginx | tail -10 | tee -a "$LOG_FILE"
    fi
fi

# ──────────────────────────────────────────────────────────────
# 6. MIGRATIONS
# ──────────────────────────────────────────────────────────────
header "Migrations do banco"

info "Aguardando backend ficar pronto..."
MAX_WAIT=60
ELAPSED=0
until docker compose exec -T backend python -c "from src.db.session import engine; engine.connect()" 2>/dev/null; do
    if [[ $ELAPSED -ge $MAX_WAIT ]]; then
        warn "Backend demorou para responder. Tentando migrations mesmo assim..."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo -n "." >&2
done
echo "" >&2

info "Executando alembic upgrade head..."
MIGRATION_OUTPUT=$(docker compose exec -T backend alembic upgrade head 2>&1)
echo "$MIGRATION_OUTPUT" | tee -a "$LOG_FILE"

if echo "$MIGRATION_OUTPUT" | grep -qi "error\|traceback\|exception"; then
    error "Erro durante as migrations. Sistema pode estar inconsistente."
    error "Para diagnóstico: docker compose logs backend"
    error "Para rollback da última migration: docker compose exec backend alembic downgrade -1"
    exit 1
fi

log "Migrations OK."

# ──────────────────────────────────────────────────────────────
# 7. HEALTH CHECK
# ──────────────────────────────────────────────────────────────
header "Verificação de saúde"

sleep 5

ALL_HEALTHY=true

check_service() {
    local service=$1
    local status
    status=$(docker compose ps --format "{{.State}}" "$service" 2>/dev/null || echo "unknown")
    if [[ "$status" == "running" ]]; then
        log "$service: rodando"
    else
        warn "$service: estado = $status"
        ALL_HEALTHY=false
    fi
}

for svc in supabase-db backend celery frontend nginx; do
    check_service "$svc"
done

# Teste de endpoint
API_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" \
    --max-time 10 "http://localhost/api/health" 2>/dev/null || echo "000")

if [[ "$API_STATUS" =~ ^(200|404)$ ]]; then
    log "API respondendo (HTTP $API_STATUS)"
elif [[ "$API_STATUS" == "000" ]]; then
    warn "API não respondeu — pode estar ainda reiniciando."
else
    warn "API retornou HTTP $API_STATUS"
fi

# ──────────────────────────────────────────────────────────────
# 8. LIMPEZA
# ──────────────────────────────────────────────────────────────
header "Limpeza"

info "Removendo imagens Docker não utilizadas..."
docker image prune -f > /dev/null 2>&1 || true
log "Limpeza concluída."

# ──────────────────────────────────────────────────────────────
# 9. RESUMO
# ──────────────────────────────────────────────────────────────
echo "" | tee -a "$LOG_FILE"
echo -e "${BOLD}${GREEN}" | tee -a "$LOG_FILE"
echo "╔═══════════════════════════════════════════════╗" | tee -a "$LOG_FILE"
if [[ "$ALL_HEALTHY" == "true" ]]; then
echo "║     Atualização concluída com sucesso! ✓      ║" | tee -a "$LOG_FILE"
else
echo "║     Atualização concluída com avisos! ⚠       ║" | tee -a "$LOG_FILE"
fi
echo "╠═══════════════════════════════════════════════╣" | tee -a "$LOG_FILE"
printf "║  %-45s║\n" "Commit anterior: ${OLD_HEAD:0:8}" | tee -a "$LOG_FILE"
printf "║  %-45s║\n" "Commit atual:    ${NEW_HEAD:0:8}" | tee -a "$LOG_FILE"
printf "║  %-45s║\n" "Log completo: logs/update.log" | tee -a "$LOG_FILE"
echo "╠═══════════════════════════════════════════════╣" | tee -a "$LOG_FILE"
echo "║  Comandos úteis:                              ║" | tee -a "$LOG_FILE"
echo "║  docker compose ps          → status         ║" | tee -a "$LOG_FILE"
echo "║  docker compose logs -f     → logs em tempo  ║" | tee -a "$LOG_FILE"
echo "║  docker compose restart     → reiniciar tudo ║" | tee -a "$LOG_FILE"
echo "╚═══════════════════════════════════════════════╝" | tee -a "$LOG_FILE"
echo -e "${RESET}" | tee -a "$LOG_FILE"

# Retornar erro se algum serviço não está saudável
if [[ "$ALL_HEALTHY" != "true" ]]; then
    warn "Algum serviço não está no estado esperado."
    warn "Verifique: docker compose ps && docker compose logs"
    exit 1
fi

exit 0
