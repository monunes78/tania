.PHONY: dev prod deploy logs stop restart build migrate seed help

# ─── Desenvolvimento ──────────────────────────────────────────
dev:
	cp -n docker-compose.override.yml.example docker-compose.override.yml 2>/dev/null || true
	docker-compose up --build

# ─── Produção ────────────────────────────────────────────────
prod:
	docker-compose up --build -d

# ─── Deploy (rodar na VM) ────────────────────────────────────
deploy:
	chmod +x deploy.sh && ./deploy.sh

# ─── Logs ────────────────────────────────────────────────────
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-celery:
	docker-compose logs -f celery

# ─── Controle ────────────────────────────────────────────────
stop:
	docker-compose down

restart:
	docker-compose restart

build:
	docker-compose build --no-cache

# ─── Banco ───────────────────────────────────────────────────
migrate:
	docker-compose exec backend alembic upgrade head

migrate-down:
	docker-compose exec backend alembic downgrade -1

seed:
	docker-compose exec backend python scripts/seed_departments.py

# ─── Utilitários ─────────────────────────────────────────────
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

ps:
	docker-compose ps

# ─── Ajuda ───────────────────────────────────────────────────
help:
	@echo ""
	@echo "TanIA — Comandos disponíveis:"
	@echo ""
	@echo "  make dev          Inicia em modo desenvolvimento (hot reload)"
	@echo "  make prod         Inicia em modo produção"
	@echo "  make deploy       Executa deploy completo (git pull + build + migrate)"
	@echo "  make logs         Mostra logs de todos os serviços"
	@echo "  make stop         Para todos os containers"
	@echo "  make restart      Reinicia todos os containers"
	@echo "  make migrate      Executa migrations pendentes"
	@echo "  make seed         Popula departamentos iniciais"
	@echo "  make ps           Lista status dos containers"
	@echo ""
