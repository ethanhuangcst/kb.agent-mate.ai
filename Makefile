.PHONY: help install install-web install-py up down dev up-deps migrate test lint doctor

.DEFAULT_GOAL := help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT)/.venv
UV := uv
PYTHON := $(VENV)/bin/python
NPM_REG := https://registry.npmmirror.com
DATABASE_URL_DEFAULT := postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf " %-14s %s\n", $$1, $$2}'

doctor: ## Check toolchain (node, uv, docker)
	@node -v
	@npm -v
	@$(UV) --version
	@docker --version
	@docker compose version

install: install-py install-web ## Install Python + Node dependencies
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	@mkdir -p $(ROOT)/data/blob $(ROOT)/data/raw $(ROOT)/.pids
	@echo "Deps installed. Copy secrets into .env if needed (see specs/keys.md)."

install-py: ## Create .venv (Python 3.12) and install packages
	@$(UV) python install 3.12
	@test -d $(VENV) || $(UV) venv $(VENV) --python 3.12
	@UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple UV_HTTP_TIMEOUT=120 \
	  $(UV) pip install --python $(PYTHON) -e "$(ROOT)/packages/kb_schema[dev]"
	@UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple UV_HTTP_TIMEOUT=120 \
	  $(UV) pip install --python $(PYTHON) -r "$(ROOT)/services/kb-rag/requirements.txt"
	@UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple UV_HTTP_TIMEOUT=120 \
	  $(UV) pip install --python $(PYTHON) -r "$(ROOT)/services/kb-agent/requirements.txt"
	@echo "Python venv ready: $(VENV)"

install-web: ## Install kb-web npm deps via npmmirror
	@cd $(ROOT)/apps/kb-web && npm install --registry=$(NPM_REG)
	@echo "kb-web node_modules ready"

up-deps: ## Start only Postgres + Qdrant
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	docker compose -f $(ROOT)/docker-compose.yml up -d postgres qdrant

up: ## Start local stack (Postgres + Qdrant + services) in background
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	@mkdir -p $(ROOT)/data/blob $(ROOT)/data/raw
	docker compose -f $(ROOT)/docker-compose.yml up -d postgres qdrant
	@echo "Waiting for Postgres..."
	@sleep 5
	@$(MAKE) migrate
	docker compose -f $(ROOT)/docker-compose.yml up -d --build
	@echo "Stack up: web :3000 · agent :8000 · rag :8001 · postgres :5434 · qdrant :6333"

down: ## Stop local stack
	-docker compose -f $(ROOT)/docker-compose.yml down
	-@pkill -f "next dev" 2>/dev/null || true
	-@pkill -f "uvicorn app.main:app" 2>/dev/null || true

dev: ## Print how to run apps in foreground (deps: make up-deps)
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	@echo "1) make up-deps && make migrate"
	@echo "2) terminals:"
	@echo "   cd apps/kb-web && npm run dev"
	@echo "   cd services/kb-agent && $(VENV)/bin/uvicorn app.main:app --reload --port 8000"
	@echo "   cd services/kb-rag && $(VENV)/bin/uvicorn app.main:app --reload --port 8001"

migrate: ## Run Alembic migrations
	@cd $(ROOT)/packages/kb_schema && \
	  DATABASE_URL=$${DATABASE_URL:-$(DATABASE_URL_DEFAULT)} \
	  $(ROOT)/.venv/bin/alembic upgrade head
	@echo "Migrations applied."

test: ## Run unit/integration tests (Python + kb-web vitest)
	@cd $(ROOT)/packages/kb_schema && $(VENV)/bin/pytest tests -q
	@cd $(ROOT)/services/kb-rag && PYTHONPATH=. $(VENV)/bin/pytest tests -q
	@cd $(ROOT)/services/kb-agent && PYTHONPATH=. $(VENV)/bin/pytest tests -q
	@cd $(ROOT)/apps/kb-web && npm test

lint: ## Lint web + Python (basic)
	@cd $(ROOT)/apps/kb-web && npm run lint || true
	@$(VENV)/bin/python -m compileall -q $(ROOT)/packages/kb_schema/src $(ROOT)/services/kb-rag/app $(ROOT)/services/kb-agent/app
