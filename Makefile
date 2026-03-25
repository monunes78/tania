.PHONY: dev prod deploy update logs stop restart build migrate seed help ps \
        shell-backend shell-frontend logs-backend logs-frontend logs-celery migrate-down

DC = docker compose

# ─── Desenvolvimento ──────────────────────────────────────────
dev:
	cp -n docker-compose.override.yml.example docker-compose.override.yml 2>/dev/null || true
	$(DC) up --build

# ─── Produção ────────────────────────────────────────────────
prod:
	$(DC) up --build -d

# ─── Deploy inicial (primeira instalação) ────────────────────
deploy:
	chmod +x deploy.sh && sudo ./deploy.sh

# ─── Atualização (usa update.sh) ─────────────────────────────
update:
	chmod +x update.sh && ./update.sh

update-force:
	chmod +x update.sh && ./update.sh --force-rebuild

# ─── Logs ────────────────────────────────────────────────────
logs:
	$(DC) logs -f

logs-backend:
	$(DC) logs -f backend

logs-frontend:
	$(DC) logs -f frontend

logs-celery:
	$(DC) logs -f celery

# ─── Controle ────────────────────────────────────────────────
stop:
	$(DC) down

restart:
	$(DC) restart

build:
	$(DC) build --no-cache

# ─── Banco ───────────────────────────────────────────────────
migrate:
	$(DC) exec backend alembic upgrade head

migrate-down:
	$(DC) exec backend alembic downgrade -1

seed:
	$(DC) exec backend python scripts/seed_departments.py

# ─── Utilitários ─────────────────────────────────────────────
shell-backend:
	$(DC) exec backend bash

shell-frontend:
	$(DC) exec frontend sh

ps:
	$(DC) ps

# ─── Ajuda ───────────────────────────────────────────────────
help:
	@echo ""
	@echo "TanIA — Comandos disponíveis:"
	@echo ""
	@echo "  make deploy        Primeira instalação completa (requer sudo)"
	@echo "  make update        Atualiza o sistema com as últimas mudanças do git"
	@echo "  make update-force  Força rebuild completo mesmo sem mudanças"
	@echo "  make dev           Inicia em modo desenvolvimento (hot reload)"
	@echo "  make prod          Inicia em modo produção"
	@echo "  make logs          Mostra logs de todos os serviços"
	@echo "  make stop          Para todos os containers"
	@echo "  make restart       Reinicia todos os containers"
	@echo "  make build         Rebuild sem cache"
	@echo "  make migrate       Executa migrations pendentes"
	@echo "  make seed          Popula departamentos iniciais"
	@echo "  make ps            Lista status dos containers"
	@echo ""
