.PHONY: help install test lint format clean run docker-up docker-down

.DEFAULT_GOAL := help

help:
	@echo "TweetPulse - Available Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-mock

install-dev: ## Install with development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src/tweetpulse --cov-report=html --cov-report=term

test-watch: ## Run tests on file changes
	pytest-watch tests/ -v

lint: ## Check code style
	ruff check src/
	black --check src/ tests/
	isort --check-only src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage dist/ build/

run: ## Run the API server
	python -m tweetpulse.main

run-worker: ## Run worker
	python -m tweetpulse.worker_runner

docker-up: ## Start all services with docker-compose
	docker-compose -f docker-compose-dev.yml up -d

docker-down: ## Stop all services
	docker-compose -f docker-compose-dev.yml down

docker-logs: ## View docker logs
	docker-compose -f docker-compose-dev.yml logs -f

shell: ## Open Python shell with context
	python -i -c "from tweetpulse.core.container import get_container; container = get_container(); print('Container loaded')"

ci: clean lint test-cov ## Run CI pipeline
	@echo "CI completed"

migrate: ## Run database migrations
	alembic upgrade head

db-reset: ## Reset database
	alembic downgrade base
	alembic upgrade head
