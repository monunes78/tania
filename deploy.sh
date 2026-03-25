#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  TanIA — Deploy Completo (primeira instalação e reinstalação)
#  Uso: sudo ./deploy.sh
#
#  O que este script faz:
#   1. Instala Docker e dependências do sistema
#   2. Configura variáveis de ambiente (.env) com geração automática
#      de segredos seguros
#   3. Converte ou gera certificado SSL
#   4. Constrói e sobe todos os containers
#   5. Executa migrations do banco de dados
#   6. Popula departamentos iniciais
#   7. Cria bucket MinIO
#   8. Verifica saúde de todos os serviços
# ══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Cores e formatação ──────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$APP_DIR/logs/deploy.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REAL_USER="${SUDO_USER:-$USER}"

mkdir -p "$APP_DIR/logs"

# ── Funções de log ──────────────────────────────────────────────
log()     { echo -e "${GREEN}[✓]${RESET} $1" | tee -a "$LOG_FILE"; }
info()    { echo -e "${BLUE}[▸]${RESET} $1" | tee -a "$LOG_FILE"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1" | tee -a "$LOG_FILE"; }
error()   { echo -e "${RED}[✗]${RESET} $1" | tee -a "$LOG_FILE"; }
header()  { echo -e "\n${BOLD}${BLUE}══ $1 ══${RESET}" | tee -a "$LOG_FILE"; }
prompt()  { echo -e "${YELLOW}[?]${RESET} $1"; }

echo "" | tee -a "$LOG_FILE"
echo -e "${BOLD}${BLUE}" | tee -a "$LOG_FILE"
echo "╔═══════════════════════════════════════════╗" | tee -a "$LOG_FILE"
echo "║        TanIA — Deploy Automático          ║" | tee -a "$LOG_FILE"
echo "║        $TIMESTAMP          ║" | tee -a "$LOG_FILE"
echo "╚═══════════════════════════════════════════╝" | tee -a "$LOG_FILE"
echo -e "${RESET}" | tee -a "$LOG_FILE"

# ──────────────────────────────────────────────────────────────
# 1. PRÉ-REQUISITOS
# ──────────────────────────────────────────────────────────────
header "Verificações iniciais"

# Deve rodar como root
if [[ $EUID -ne 0 ]]; then
    error "Este script precisa ser executado como root."
    echo "       Use: sudo ./deploy.sh"
    exit 1
fi

# Sistema operacional
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        warn "Sistema operacional não é Ubuntu ($ID). Pode haver incompatibilidades."
    elif [[ "$VERSION_ID" < "22.04" ]]; then
        warn "Ubuntu $VERSION_ID detectado. Recomendado: 24.04 LTS."
    else
        log "Ubuntu $VERSION_ID detectado."
    fi
fi

# Memória RAM (mínimo 8 GB recomendado)
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
if [[ $TOTAL_RAM_GB -lt 8 ]]; then
    warn "RAM disponível: ${TOTAL_RAM_GB}GB (mínimo recomendado: 8GB). Pode haver instabilidade."
else
    log "RAM: ${TOTAL_RAM_GB}GB"
fi

# Espaço em disco (mínimo 20 GB)
FREE_DISK_GB=$(df -BG "$APP_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
if [[ ${FREE_DISK_GB:-0} -lt 20 ]]; then
    warn "Espaço livre em disco: ${FREE_DISK_GB}GB (mínimo recomendado: 20GB)."
else
    log "Disco livre: ${FREE_DISK_GB}GB"
fi

# ──────────────────────────────────────────────────────────────
# 2. INSTALAR DEPENDÊNCIAS DO SISTEMA
# ──────────────────────────────────────────────────────────────
header "Dependências do sistema"

info "Atualizando lista de pacotes..."
apt-get update -qq

info "Instalando pacotes essenciais..."
apt-get install -y -qq \
    curl wget git nano unzip \
    ca-certificates gnupg lsb-release \
    openssl apt-transport-https \
    software-properties-common 2>&1 | tee -a "$LOG_FILE"

# Fuso horário
CURRENT_TZ=$(timedatectl show --property=Timezone --value 2>/dev/null || echo "")
if [[ "$CURRENT_TZ" != "America/Sao_Paulo" ]]; then
    info "Configurando fuso horário para America/Sao_Paulo..."
    timedatectl set-timezone America/Sao_Paulo
fi
log "Fuso horário: $(timedatectl show --property=Timezone --value)"

# ──────────────────────────────────────────────────────────────
# 3. INSTALAR DOCKER
# ──────────────────────────────────────────────────────────────
header "Docker"

if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    log "Docker já instalado: $DOCKER_VER"
else
    info "Instalando Docker Engine..."

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc 2>/dev/null
    chmod a+r /etc/apt/keyrings/docker.asc

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin \
        2>&1 | tee -a "$LOG_FILE"

    systemctl enable docker
    systemctl start docker
    log "Docker instalado com sucesso."
fi

# Garantir que docker compose v2 está disponível
if ! docker compose version &>/dev/null; then
    info "Instalando Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin 2>&1 | tee -a "$LOG_FILE"
fi
log "Docker Compose: $(docker compose version --short 2>/dev/null || echo 'OK')"

# Adicionar usuário real ao grupo docker (evita sudo para uso diário)
if [[ -n "$REAL_USER" ]] && [[ "$REAL_USER" != "root" ]]; then
    if ! id -nG "$REAL_USER" | grep -qw docker; then
        usermod -aG docker "$REAL_USER"
        log "Usuário '$REAL_USER' adicionado ao grupo docker."
        warn "Faça logout e login novamente para usar docker sem sudo."
    fi
fi

# ──────────────────────────────────────────────────────────────
# 4. CONFIGURAÇÃO DO .env
# ──────────────────────────────────────────────────────────────
header "Configuração de variáveis de ambiente"

cd "$APP_DIR"

# Copiar .env.example se .env não existir
if [[ ! -f .env ]]; then
    cp .env.example .env
    info ".env criado a partir do .env.example"
fi

# ── Funções auxiliares para .env ────────────────────────────
env_get() { grep "^${1}=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo ""; }
env_set() { sed -i "s|^${1}=.*|${1}=${2}|g" .env; }

is_placeholder() {
    local val="$1"
    [[ -z "$val" ]] && return 0
    echo "$val" | grep -qiE "(mude|your-super-secret|^sk-or-$|placeholder|changeme|change.me)" && return 0
    return 1
}

# ── Gerar JWT Supabase (HS256) ───────────────────────────────
generate_supabase_jwt() {
    local secret="$1" role="$2" exp=1983812996
    local hdr; hdr=$(printf '{"alg":"HS256","typ":"JWT"}' | openssl base64 -A | tr '+/' '-_' | tr -d '=')
    local pay; pay=$(printf '{"iss":"supabase-demo","role":"%s","exp":%s}' "$role" "$exp" | openssl base64 -A | tr '+/' '-_' | tr -d '=')
    local sig; sig=$(printf '%s.%s' "$hdr" "$pay" | openssl dgst -sha256 -hmac "$secret" -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
    printf '%s.%s.%s' "$hdr" "$pay" "$sig"
}

# ── Auto-geração de segredos ─────────────────────────────────
info "Verificando segredos no .env..."

# POSTGRES_PASSWORD
PG_PASS=$(env_get POSTGRES_PASSWORD)
if is_placeholder "$PG_PASS"; then
    NEW_PASS=$(openssl rand -hex 16)
    env_set POSTGRES_PASSWORD "$NEW_PASS"
    log "POSTGRES_PASSWORD gerado automaticamente."
fi

# SUPABASE_JWT_SECRET
SUPA_JWT=$(env_get SUPABASE_JWT_SECRET)
if is_placeholder "$SUPA_JWT"; then
    NEW_SUPA_JWT=$(openssl rand -hex 32)
    env_set SUPABASE_JWT_SECRET "$NEW_SUPA_JWT"
    SUPA_JWT="$NEW_SUPA_JWT"
    # Regenerar ANON e SERVICE keys
    ANON_KEY=$(generate_supabase_jwt "$NEW_SUPA_JWT" "anon")
    SERVICE_KEY=$(generate_supabase_jwt "$NEW_SUPA_JWT" "service_role")
    env_set SUPABASE_ANON_KEY "$ANON_KEY"
    env_set SUPABASE_SERVICE_KEY "$SERVICE_KEY"
    log "SUPABASE_JWT_SECRET + ANON_KEY + SERVICE_KEY gerados automaticamente."
fi

# JWT_SECRET
JWT_SEC=$(env_get JWT_SECRET)
if is_placeholder "$JWT_SEC"; then
    env_set JWT_SECRET "$(openssl rand -base64 32)"
    log "JWT_SECRET gerado automaticamente."
fi

# ENCRYPTION_KEY (AES-256 base64)
ENC_KEY=$(env_get ENCRYPTION_KEY)
if is_placeholder "$ENC_KEY"; then
    env_set ENCRYPTION_KEY "$(openssl rand -base64 32)"
    log "ENCRYPTION_KEY gerado automaticamente."
fi

# MINIO_SECRET_KEY
MINIO_KEY=$(env_get MINIO_SECRET_KEY)
if is_placeholder "$MINIO_KEY"; then
    env_set MINIO_SECRET_KEY "$(openssl rand -hex 16)"
    log "MINIO_SECRET_KEY gerado automaticamente."
fi

# LITELLM_MASTER_KEY
LITELLM_KEY=$(env_get LITELLM_MASTER_KEY)
if is_placeholder "$LITELLM_KEY"; then
    env_set LITELLM_MASTER_KEY "sk-master-$(openssl rand -hex 12)"
    log "LITELLM_MASTER_KEY gerado automaticamente."
fi

# NEXTAUTH_SECRET
NEXTAUTH_SEC=$(env_get NEXTAUTH_SECRET)
if is_placeholder "$NEXTAUTH_SEC"; then
    env_set NEXTAUTH_SECRET "$(openssl rand -base64 32)"
    log "NEXTAUTH_SECRET gerado automaticamente."
fi

# ── Campos que requerem entrada humana ───────────────────────
echo ""

# NEXTAUTH_URL (URL pública do sistema)
CURRENT_URL=$(env_get NEXTAUTH_URL)
prompt "URL pública do TanIA (ex: https://tania.tanac.com.br)"
prompt "Atual: ${CURRENT_URL:-não configurado} — Enter para manter, ou digite nova URL:"
read -r NEW_URL
if [[ -n "$NEW_URL" ]]; then
    env_set NEXTAUTH_URL "$NEW_URL"
    env_set NEXT_PUBLIC_API_URL "$NEW_URL"
    CURRENT_URL="$NEW_URL"
    log "NEXTAUTH_URL atualizado para: $CURRENT_URL"
fi

# LDAP_BIND_PASSWORD
LDAP_PASS=$(env_get LDAP_BIND_PASSWORD)
if [[ -z "$LDAP_PASS" ]]; then
    prompt "Senha do serviço LDAP (svc_tania@tanac.com.br):"
    read -rs LDAP_PASS_INPUT
    echo ""
    if [[ -n "$LDAP_PASS_INPUT" ]]; then
        env_set LDAP_BIND_PASSWORD "$LDAP_PASS_INPUT"
        log "LDAP_BIND_PASSWORD configurado."
    else
        warn "LDAP_BIND_PASSWORD não configurado — autenticação AD não funcionará."
    fi
fi

# OPENROUTER_API_KEY (opcional para testes)
OR_KEY=$(env_get OPENROUTER_API_KEY)
if [[ "$OR_KEY" == "sk-or-" ]] || [[ -z "$OR_KEY" ]]; then
    prompt "OpenRouter API Key (opcional, Enter para pular):"
    read -r OR_KEY_INPUT
    if [[ -n "$OR_KEY_INPUT" ]]; then
        env_set OPENROUTER_API_KEY "$OR_KEY_INPUT"
        log "OPENROUTER_API_KEY configurado."
    else
        warn "OPENROUTER_API_KEY não configurado — configure um LLM no Admin Panel após o deploy."
    fi
fi

log "Configuração do .env concluída."

# ──────────────────────────────────────────────────────────────
# 5. CERTIFICADO SSL
# ──────────────────────────────────────────────────────────────
header "Certificado SSL"

mkdir -p "$APP_DIR/nginx/ssl" "$APP_DIR/cert"

# Extrair hostname da URL
TLS_DOMAIN=$(env_get NEXTAUTH_URL | sed -E 's|https?://||' | sed 's|/.*||' | sed 's|:.*||')
TLS_DOMAIN="${TLS_DOMAIN:-tania.tanac.com.br}"

# 1. Verificar se cert.pem já existe e é válido
if [[ -f "$APP_DIR/nginx/ssl/cert.pem" ]] && [[ -f "$APP_DIR/nginx/ssl/key.pem" ]]; then
    if openssl x509 -in "$APP_DIR/nginx/ssl/cert.pem" -noout -checkend 0 2>/dev/null; then
        CERT_EXPIRY=$(openssl x509 -in "$APP_DIR/nginx/ssl/cert.pem" -noout -enddate 2>/dev/null | cut -d= -f2)
        log "Certificado SSL existente válido até: $CERT_EXPIRY"
        SSL_OK=true
    else
        warn "Certificado SSL expirado — regenerando..."
        SSL_OK=false
    fi
else
    SSL_OK=false
fi

# 2. Tentar converter .pfx se existir
if [[ "$SSL_OK" != "true" ]]; then
    PFX_FILE=$(find "$APP_DIR/cert" -name "*.pfx" 2>/dev/null | head -1)

    if [[ -n "$PFX_FILE" ]]; then
        info "Certificado .pfx encontrado: $(basename "$PFX_FILE")"
        info "Tentando converter com senha vazia..."

        if openssl pkcs12 -in "$PFX_FILE" -nokeys -out "$APP_DIR/nginx/ssl/cert.pem" \
                -passin pass: -legacy 2>/dev/null && \
           openssl pkcs12 -in "$PFX_FILE" -nocerts -nodes -out "$APP_DIR/nginx/ssl/key.pem" \
                -passin pass: -legacy 2>/dev/null; then
            log "Certificado convertido com sucesso (sem senha)."
        else
            prompt "Digite a senha do certificado .pfx:"
            read -rs PFX_PASS
            echo ""
            if openssl pkcs12 -in "$PFX_FILE" -nokeys -out "$APP_DIR/nginx/ssl/cert.pem" \
                    -passin "pass:$PFX_PASS" -legacy 2>/dev/null && \
               openssl pkcs12 -in "$PFX_FILE" -nocerts -nodes -out "$APP_DIR/nginx/ssl/key.pem" \
                    -passin "pass:$PFX_PASS" -legacy 2>/dev/null; then
                log "Certificado convertido com sucesso."
            else
                error "Falha ao converter .pfx. Gerando certificado auto-assinado..."
                SSL_OK=false
                PFX_FILE=""
            fi
        fi
        [[ -n "$PFX_FILE" ]] && SSL_OK=true
    fi

    # 3. Gerar auto-assinado se não há .pfx
    if [[ "$SSL_OK" != "true" ]]; then
        warn "Nenhum certificado .pfx encontrado em $APP_DIR/cert/"
        warn "Gerando certificado auto-assinado para: $TLS_DOMAIN"
        warn "ATENÇÃO: Browsers exibirão aviso de segurança. Substitua por um certificado real."

        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$APP_DIR/nginx/ssl/key.pem" \
            -out "$APP_DIR/nginx/ssl/cert.pem" \
            -subj "/C=BR/ST=SP/O=TANAC/CN=${TLS_DOMAIN}" \
            -addext "subjectAltName=DNS:${TLS_DOMAIN},DNS:localhost" 2>/dev/null

        log "Certificado auto-assinado gerado para: $TLS_DOMAIN"
    fi
fi

# Permissões seguras nos certificados
chmod 600 "$APP_DIR/nginx/ssl/key.pem" 2>/dev/null || true
chmod 644 "$APP_DIR/nginx/ssl/cert.pem" 2>/dev/null || true

# ──────────────────────────────────────────────────────────────
# 6. CONFIGURAR NGINX (server_name dinâmico)
# ──────────────────────────────────────────────────────────────
header "Configuração Nginx"

if [[ -f "$APP_DIR/nginx/nginx.conf" ]]; then
    sed -i "s|server_name .*;|server_name $TLS_DOMAIN;|g" "$APP_DIR/nginx/nginx.conf"
    log "nginx.conf atualizado com server_name: $TLS_DOMAIN"
fi

# ──────────────────────────────────────────────────────────────
# 7. VERIFICAR ARQUIVOS NECESSÁRIOS
# ──────────────────────────────────────────────────────────────
header "Verificação de arquivos de configuração"

MISSING_FILES=()
[[ ! -f "$APP_DIR/nginx/nginx.conf" ]]           && MISSING_FILES+=("nginx/nginx.conf")
[[ ! -f "$APP_DIR/litellm-proxy/config.yaml" ]]  && MISSING_FILES+=("litellm-proxy/config.yaml")
[[ ! -f "$APP_DIR/supabase/init/00_init.sh" ]] && [[ ! -f "$APP_DIR/supabase/init/00_init.sql" ]] && MISSING_FILES+=("supabase/init/00_init.sh")
[[ ! -f "$APP_DIR/docker-compose.yml" ]]         && MISSING_FILES+=("docker-compose.yml")

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    error "Arquivos obrigatórios não encontrados:"
    for f in "${MISSING_FILES[@]}"; do
        error "  — $f"
    done
    error "Verifique se o clone do repositório foi completo."
    exit 1
fi

log "Todos os arquivos de configuração presentes."

# ──────────────────────────────────────────────────────────────
# 8. VERIFICAR PORTAS
# ──────────────────────────────────────────────────────────────
header "Verificação de portas"

check_port() {
    local port=$1 name=$2
    if ss -tlnp "sport = :$port" 2>/dev/null | grep -q ":$port" && \
       ! docker compose ps --services 2>/dev/null | xargs -I{} docker compose ps {} 2>/dev/null | grep -q "Up"; then
        warn "Porta $port ($name) pode estar em uso por outro processo."
    fi
}

check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8082 "Supabase Studio"

# ──────────────────────────────────────────────────────────────
# 9. BUILD E START DOS CONTAINERS
# ──────────────────────────────────────────────────────────────
header "Build e inicialização dos containers"

cd "$APP_DIR"

info "Fazendo pull das imagens base..."
docker compose pull --ignore-pull-failures 2>&1 | tee -a "$LOG_FILE" || true

info "Construindo imagens da aplicação..."
docker compose build --no-cache 2>&1 | tee -a "$LOG_FILE"

info "Iniciando todos os serviços..."
docker compose up -d 2>&1 | tee -a "$LOG_FILE"

log "Containers iniciados."

# ──────────────────────────────────────────────────────────────
# 10. AGUARDAR BANCO DE DADOS
# ──────────────────────────────────────────────────────────────
header "Aguardando banco de dados"

info "Aguardando supabase-db ficar saudável..."
MAX_WAIT=120
ELAPSED=0
until docker compose exec -T supabase-db pg_isready -U postgres -d postgres -q 2>/dev/null; do
    if [[ $ELAPSED -ge $MAX_WAIT ]]; then
        error "Timeout aguardando o banco de dados ($MAX_WAIT segundos)."
        error "Verifique os logs: docker compose logs supabase-db"
        exit 1
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo -n "." >&2
done
echo "" >&2

log "Banco de dados pronto. (${ELAPSED}s)"

# Aguardar mais 5s para o backend inicializar completamente
info "Aguardando backend inicializar..."
sleep 8

# ──────────────────────────────────────────────────────────────
# 11. MIGRATIONS DO BANCO DE DADOS
# ──────────────────────────────────────────────────────────────
header "Migrations do banco de dados"

info "Executando alembic upgrade head..."
MIGRATION_OUTPUT=$(docker compose exec -T backend alembic upgrade head 2>&1)
echo "$MIGRATION_OUTPUT" | tee -a "$LOG_FILE"

if echo "$MIGRATION_OUTPUT" | grep -qi "error\|traceback\|exception"; then
    error "Erro durante as migrations."
    error "Verifique: docker compose logs backend"
    exit 1
fi

log "Migrations executadas com sucesso."

# ──────────────────────────────────────────────────────────────
# 12. SEED DE DEPARTAMENTOS
# ──────────────────────────────────────────────────────────────
header "Dados iniciais"

info "Populando departamentos iniciais..."
SEED_OUTPUT=$(docker compose exec -T backend python scripts/seed_departments.py 2>&1)
echo "$SEED_OUTPUT" | tee -a "$LOG_FILE"

if echo "$SEED_OUTPUT" | grep -qi "Erro\|Error\|Traceback"; then
    warn "Possível problema no seed — verifique os logs acima."
else
    log "Seed concluído."
fi

# ──────────────────────────────────────────────────────────────
# 13. MINIO — CRIAR BUCKET
# ──────────────────────────────────────────────────────────────
header "MinIO"

info "Criando bucket de documentos..."
MINIO_OUTPUT=$(docker compose exec -T backend python -c "
from src.core.storage.minio_client import minio_client
from src.config import settings
minio_client.ensure_bucket(settings.MINIO_BUCKET)
print('Bucket criado/verificado:', settings.MINIO_BUCKET)
" 2>&1)
echo "$MINIO_OUTPUT" | tee -a "$LOG_FILE"

if echo "$MINIO_OUTPUT" | grep -qi "error\|traceback"; then
    warn "Possível problema ao criar bucket MinIO — pode não afetar o funcionamento imediato."
else
    log "Bucket MinIO configurado."
fi

# ──────────────────────────────────────────────────────────────
# 14. HEALTH CHECKS
# ──────────────────────────────────────────────────────────────
header "Verificação de saúde dos serviços"

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

for svc in supabase-db supabase-rest supabase-meta supabase-studio \
           backend celery celery-beat frontend litellm redis minio nginx; do
    check_service "$svc"
done

# Verificar endpoint da API
info "Testando endpoint da API..."
sleep 3
API_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" \
    --max-time 10 "http://localhost/api/health" 2>/dev/null || echo "000")

if [[ "$API_STATUS" =~ ^(200|404)$ ]]; then
    log "API respondendo (HTTP $API_STATUS)"
elif [[ "$API_STATUS" == "000" ]]; then
    warn "API não respondeu — pode ainda estar inicializando. Aguarde alguns segundos."
else
    warn "API retornou HTTP $API_STATUS — verifique: docker compose logs backend"
fi

# ──────────────────────────────────────────────────────────────
# 15. PERMISSÕES E LIMPEZA
# ──────────────────────────────────────────────────────────────
header "Finalizando"

# Ajustar ownership do diretório para o usuário real
if [[ -n "$REAL_USER" ]] && [[ "$REAL_USER" != "root" ]]; then
    chown -R "$REAL_USER:$REAL_USER" "$APP_DIR/logs" 2>/dev/null || true
fi

# Tornar update.sh executável
chmod +x "$APP_DIR/update.sh" 2>/dev/null || true

# Limpar imagens intermediárias de build
docker image prune -f > /dev/null 2>&1 || true

# ──────────────────────────────────────────────────────────────
# 16. RESUMO FINAL
# ──────────────────────────────────────────────────────────────
FINAL_URL=$(env_get NEXTAUTH_URL)
VM_IP=$(hostname -I | awk '{print $1}')

echo "" | tee -a "$LOG_FILE"
echo -e "${BOLD}${GREEN}" | tee -a "$LOG_FILE"
echo "╔═══════════════════════════════════════════════════╗" | tee -a "$LOG_FILE"
echo "║           Deploy concluído com sucesso!           ║" | tee -a "$LOG_FILE"
echo "╠═══════════════════════════════════════════════════╣" | tee -a "$LOG_FILE"
printf "║  %-49s║\n" "Aplicação:     $FINAL_URL"      | tee -a "$LOG_FILE"
printf "║  %-49s║\n" "Supabase UI:   http://$VM_IP:8082"  | tee -a "$LOG_FILE"
printf "║  %-49s║\n" "MinIO Console: http://$VM_IP:9001"  | tee -a "$LOG_FILE"
printf "║  %-49s║\n" "API Docs:      http://$VM_IP:8000/api/docs" | tee -a "$LOG_FILE"
echo "╠═══════════════════════════════════════════════════╣" | tee -a "$LOG_FILE"
echo "║  Próximos passos:                                 ║" | tee -a "$LOG_FILE"
echo "║  1. Acesse o Admin Panel e configure um LLM       ║" | tee -a "$LOG_FILE"
echo "║  2. Crie um agente para um departamento           ║" | tee -a "$LOG_FILE"
echo "║  3. Faça upload de um documento de teste          ║" | tee -a "$LOG_FILE"
echo "║  4. Teste o chat com o agente                     ║" | tee -a "$LOG_FILE"
echo "╠═══════════════════════════════════════════════════╣" | tee -a "$LOG_FILE"
echo "║  Atualizações futuras: ./update.sh                ║" | tee -a "$LOG_FILE"
echo "║  Logs do deploy: logs/deploy.log                  ║" | tee -a "$LOG_FILE"
echo "╚═══════════════════════════════════════════════════╝" | tee -a "$LOG_FILE"
echo -e "${RESET}" | tee -a "$LOG_FILE"

if [[ "$ALL_HEALTHY" != "true" ]]; then
    warn "Um ou mais serviços não estão no estado esperado."
    warn "Verifique: docker compose ps && docker compose logs"
fi

exit 0
