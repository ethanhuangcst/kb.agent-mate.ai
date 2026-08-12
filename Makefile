.PHONY: help install install-web install-py up down dev up-deps start-apps stop-apps migrate test lint doctor up-docker status up-daemon down-apps

.DEFAULT_GOAL := help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT)/.venv
UV := uv
PYTHON := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
NPM_REG := https://registry.npmmirror.com
DATABASE_URL_DEFAULT := postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent
PIDS := $(ROOT)/.pids

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
	@mkdir -p $(ROOT)/data/blob $(ROOT)/data/raw $(PIDS)
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

up-deps: ## Start only Postgres + Qdrant (pulled images — no app build)
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	docker compose -f $(ROOT)/docker-compose.yml up -d postgres qdrant
	@echo "Waiting for Postgres..."
	@sleep 3

start-apps: ## Start kb-rag :8001 + kb-agent :8000 from .venv (hot reload)
	@test -x $(UVICORN) || (echo "Missing venv — run: make install-py" && exit 1)
	@mkdir -p $(ROOT)/data/blob $(ROOT)/data/raw $(PIDS)
	@$(MAKE) stop-apps
	@set -a; [ -f $(ROOT)/.env ] && . $(ROOT)/.env; set +a; \
	  cd $(ROOT)/services/kb-rag && \
	  nohup $(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8001 \
	    > $(PIDS)/kb-rag.log 2>&1 & echo $$! > $(PIDS)/kb-rag.pid
	@set -a; [ -f $(ROOT)/.env ] && . $(ROOT)/.env; set +a; \
	  cd $(ROOT)/services/kb-agent && \
	  nohup $(UVICORN) app.main:app --reload --host 127.0.0.1 --port 8000 \
	    > $(PIDS)/kb-agent.log 2>&1 & echo $$! > $(PIDS)/kb-agent.pid
	@sleep 2
	@curl -sf http://127.0.0.1:8001/healthz >/dev/null && echo "kb-rag  :8001 ok" || echo "kb-rag  :8001 starting… (see $(PIDS)/kb-rag.log)"
	@curl -sf http://127.0.0.1:8000/healthz >/dev/null && echo "kb-agent:8000 ok" || echo "kb-agent:8000 starting… (see $(PIDS)/kb-agent.log)"
	@echo "Note: if started from Cursor Agent, prefer: make up-daemon (survives agent shell abort)"

up-daemon: up-deps migrate ## Durable local apps (double-fork; survives Cursor agent-exec abort)
	@$(PYTHON) $(ROOT)/scripts/daemon_start_apps.py
	@sleep 2
	@$(MAKE) status
	@curl -sf -o /dev/null http://127.0.0.1:3000/ && echo "kb-web  :3000 ok" || echo "kb-web  :3000 starting… (see $(PIDS)/kb-web.log)"

down-apps: ## Stop only local uvicorn/next (via daemon script)
	@$(PYTHON) $(ROOT)/scripts/daemon_start_apps.py stop

stop-apps: ## Stop local uvicorn agent/rag
	@if [ -f $(PIDS)/kb-agent.pid ]; then kill `cat $(PIDS)/kb-agent.pid` 2>/dev/null || true; rm -f $(PIDS)/kb-agent.pid; fi
	@if [ -f $(PIDS)/kb-rag.pid ]; then kill `cat $(PIDS)/kb-rag.pid` 2>/dev/null || true; rm -f $(PIDS)/kb-rag.pid; fi
	@if [ -f $(PIDS)/kb-web.pid ]; then kill `cat $(PIDS)/kb-web.pid` 2>/dev/null || true; rm -f $(PIDS)/kb-web.pid; fi
	-@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	-@pkill -f "next dev" 2>/dev/null || true

up: up-deps migrate start-apps ## Local stack without building app images
	@echo ""
	@echo "Ready (no Docker app build):"
	@echo "  agent  http://127.0.0.1:8000   MCP http://127.0.0.1:8000/mcp/"
	@echo "  rag    http://127.0.0.1:8001"
	@echo "  web    cd apps/kb-web && npm run dev   # optional :3000"
	@echo "Logs: $(PIDS)/kb-agent.log  $(PIDS)/kb-rag.log"

dev: up ## Same as make up (local deps + venv apps)
	@true

up-docker: ## Full Docker stack including app image builds (slow — only when you need it)
	@test -f $(ROOT)/.env || cp $(ROOT)/.env.example $(ROOT)/.env
	@mkdir -p $(ROOT)/data/blob $(ROOT)/data/raw
	docker compose -f $(ROOT)/docker-compose.yml up -d postgres qdrant
	@sleep 5
	@$(MAKE) migrate
	docker compose -f $(ROOT)/docker-compose.yml up -d --build
	@echo "Docker stack up: web :3000 · agent :8000 · rag :8001"

down: stop-apps ## Stop local uvicorn + Postgres/Qdrant containers
	-docker compose -f $(ROOT)/docker-compose.yml stop postgres qdrant
	-@pkill -f "next dev" 2>/dev/null || true
	@echo "Stopped local apps and deps (containers stopped, not removed)."

status: ## Show health of deps + local apps
	@echo "Postgres/Qdrant:"; docker compose -f $(ROOT)/docker-compose.yml ps postgres qdrant 2>/dev/null || true
	@echo -n "kb-agent :8000 "; curl -sf http://127.0.0.1:8000/healthz && echo || echo down
	@echo -n "kb-rag   :8001 "; curl -sf http://127.0.0.1:8001/healthz && echo || echo down

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
