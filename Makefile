.PHONY: help dev build up down restart logs logs-worker test lint clean

# ── Default ───────────────────────────────────────────────────
help: ## Show this help message
	@echo.
	@echo   Document Intelligence API - Available Commands
	@echo   ══════════════════════════════════════════════════
	@echo.
	@echo   make dev          Start all services (build + up)
	@echo   make up           Start services without rebuild
	@echo   make down         Stop all services
	@echo   make restart      Restart all services
	@echo   make build        Build Docker images
	@echo   make logs         Follow API logs
	@echo   make logs-worker  Follow Worker logs
	@echo   make test         Run test suite inside container
	@echo   make lint         Run linter (ruff)
	@echo   make clean        Remove containers, volumes, cache
	@echo.

# ── Development ───────────────────────────────────────────────
dev: ## Build and start all services
	docker-compose up -d --build

build: ## Build Docker images
	docker-compose build

up: ## Start services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

# ── Logs ──────────────────────────────────────────────────────
logs: ## Follow API logs
	docker-compose logs -f api

logs-worker: ## Follow worker logs
	docker-compose logs -f worker

logs-all: ## Follow all service logs
	docker-compose logs -f

# ── Testing ───────────────────────────────────────────────────
test: ## Run tests inside the API container
	docker-compose exec api pytest -v --tb=short

# ── Code Quality ──────────────────────────────────────────────
lint: ## Run ruff linter
	docker-compose exec api ruff check app/ tests/

# ── Cleanup ───────────────────────────────────────────────────
clean: ## Remove containers, volumes, and cache
	docker-compose down -v --remove-orphans
	@echo Cleaned up all containers and volumes.
