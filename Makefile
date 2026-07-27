.PHONY: help dev dev-detached up down down-dev logs logs-dev status test test-backend test-frontend lint lint-backend lint-frontend build clean

SHELL := /bin/bash

.DEFAULT_GOAL := help

help: ## Exibe a lista de comandos disponíveis
	@echo "======================================================="
	@echo "  CAESI - Comandos de Automação (Makefile)"
	@echo "======================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

## === 🚀 DESENVOLVIMENTO ===

dev: ## Inicia o ambiente de desenvolvimento completo via Docker Compose (hot-reload)
	docker compose -f docker-compose.dev.yml up --build

dev-detached: ## Inicia o ambiente de desenvolvimento em segundo plano
	docker compose -f docker-compose.dev.yml up -d --build

up: ## Inicia os serviços da aplicação via Docker Compose
	docker compose up -d --build

down: ## Para os containers da aplicação
	docker compose down

down-dev: ## Para o ambiente de desenvolvimento Docker Compose
	docker compose -f docker-compose.dev.yml down

logs: ## Exibe os logs dos containers em tempo real
	docker compose logs -f

logs-dev: ## Exibe os logs do ambiente de desenvolvimento em tempo real
	docker compose -f docker-compose.dev.yml logs -f

status: ## Mostra o status dos containers em execução
	docker compose ps

## === 🧪 TESTES E QUALIDADE DE CÓDIGO ===

test: test-backend test-frontend ## Executa todos os testes unitários (Backend e Frontend)

test-backend: ## Executa os testes do backend com pytest
	cd backend && .venv/bin/pytest tests

test-frontend: ## Executa os testes do frontend com Vitest
	cd frontend && mkdir -p .tmp && TMPDIR=$$(pwd)/.tmp npx vitest run

lint: lint-backend lint-frontend ## Executa linters e verificações de tipo (Backend e Frontend)

lint-backend: ## Executa o linter ruff no backend
	cd backend && .venv/bin/ruff check src tests

lint-frontend: ## Executa eslint e checagem de tipos vue-tsc no frontend
	cd frontend && npm run lint && npx vue-tsc --noEmit

## === 🛠️ BUILD E LIMPEZA ===

build: ## Constrói as imagens de produção
	docker compose build

clean: ## Limpa containers, volumes dev e diretórios temporários
	docker compose -f docker-compose.dev.yml down -v
	rm -rf frontend/.tmp backend/.pytest_cache backend/.ruff_cache
