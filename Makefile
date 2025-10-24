# Makefile for Tweet Pulse - Test and Development Commands

.PHONY: help test test-integration test-unit test-cov test-fast test-verbose clean install-test lint format

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Tweet Pulse - Available Commands"
	@echo "==================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =====================================
# Installation
# =====================================

install: ## Install production dependencies
	pip install -r requirements.txt

install-test: ## Install test dependencies
	pip install -r requirements-test.txt

install-dev: install install-test ## Install all dependencies (prod + test)

# =====================================
# Testes
# =====================================

test-basic: ## Execute basic test
	python3 scripts/basic_test.py

test: ## Execute all tests
	python3 -m pytest tests/test_integration/test_storage_integration.py tests/test_integration/test_enrichment_integration.py tests/test_integration/test_deduplication_integration.py -v --tb=short -p no:warnings

test-simple: ## Execute tests without problematic plugins
	python3 scripts/simple_test_runner.py

test-integration: ## Execute only integration tests
	python3 -m pytest tests/test_integration/ -v -m integration --tb=short -p no:warnings

test-unit: ## Execute only unit tests
	python3 -m pytest tests/ -v -m "not integration" --tb=short -p no:warnings

test-fast: ## Execute tests in parallel (faster)
	python3 -m pytest tests/test_integration/ -n auto -v --tb=short -p no:warnings

test-verbose: ## Execute tests with verbose output
	python3 -m pytest tests/test_integration/ -vv -s --tb=short -p no:warnings

test-cov: ## Execute tests with code coverage
	python3 -m pytest tests/test_integration/ \
		--cov=tweetpulse.ingestion \
		--cov-report=html \
		--cov-report=term-missing \
		-v --tb=short -p no:warnings

test-cov-report: test-cov ## Generate and open coverage report
	@echo "Abrindo relatório de cobertura..."
	xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Abra htmlcov/index.html manualmente"

test-storage: ## Execute only storage tests
	python3 -m pytest tests/test_integration/test_storage_integration.py -vv --tb=short -p no:warnings

test-enrichment: ## Execute only enrichment tests
	python3 -m pytest tests/test_integration/test_enrichment_integration.py -vv --tb=short -p no:warnings

test-deduplication: ## Execute only deduplication tests
	python3 -m pytest tests/test_integration/test_deduplication_integration.py -vv --tb=short -p no:warnings

test-pipeline: ## Execute only pipeline tests
	python3 -m pytest tests/test_integration/test_pipeline_integration.py -vv --tb=short -p no:warnings

test-consumer: ## Execute only consumer tests
	python3 -m pytest tests/test_integration/test_consumer_integration.py -vv --tb=short -p no:warnings

test-batch-writer: ## Execute only batch writer tests
	python3 -m pytest tests/test_integration/test_batch_writer_integration.py -vv --tb=short -p no:warnings

test-watch: ## Run tests continuously (requires pytest-watch)
	pytest-watch tests/test_integration/ -v

test-debug: ## Execute tests with debugger
	python3 -m pytest tests/test_integration/ -vv -s --pdb

test-failfast: ## Stop at first failed test
	pytest tests/test_integration/ -v -x

test-last-failed: ## Re-run only failed tests
	pytest tests/test_integration/ -v --lf

# =====================================
# Code Quality
# =====================================

lint: ## Check code with ruff
	ruff check src/tweetpulse/

lint-fix: ## Fix automatic lint problems
	ruff check --fix src/tweetpulse/

format: ## Format code with black
	black src/tweetpulse/ tests/
	isort src/tweetpulse/ tests/

format-check: ## Check formatting without modifying
	black --check src/tweetpulse/ tests/
	isort --check-only src/tweetpulse/ tests/

typecheck: ## Check types with mypy
	mypy src/tweetpulse/

# =====================================
# Clean
# =====================================

clean: ## Remove arquivos temporários e cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	@echo "✓ Limpeza concluída"

clean-logs: ## Remove logs de teste
	rm -f tests/test_run.log
	@echo "✓ Logs removidos"

# =====================================
# CI/CD
# =====================================

ci: clean install-test lint format-check typecheck test-cov ## Run full CI pipeline
	@echo "✓ CI pipeline completed successfully"

pre-commit: format lint test ## Run checks before commit
	@echo "✓ Ready to commit"

# =====================================
# Development
# =====================================

dev-setup: install-dev ## Setup development environment
	@echo "✓ Development environment configured"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure your environment variables (.env)"
	@echo "  2. Execute: make test"
	@echo "  3. Start developing!"

shell: ## Open Python shell with environment loaded
	python -i -c "from tweetpulse.core.config import get_settings; settings = get_settings(); print('Settings loaded. Use: settings')"

# =====================================
# Documentation
# =====================================

docs: ## Show test documentation
	@cat tests/test_integration/README.md

test-help: ## Show help on how to run tests
	@./scripts/run_tests.sh --help

# =====================================
# Métricas
# =====================================

test-stats: ## Mostra estatísticas dos testes
	@echo "Estatísticas de Testes"
	@echo "====================="
	@echo ""
	@echo "Total de arquivos de teste:"
	@find tests/test_integration -name "test_*.py" | wc -l
	@echo ""
	@echo "Total de testes:"
	@pytest tests/test_integration/ --collect-only -q | tail -n 1
	@echo ""
	@echo "Testes por arquivo:"
	@for file in tests/test_integration/test_*.py; do \
		count=$$(pytest $$file --collect-only -q 2>/dev/null | tail -n 1 | grep -o '[0-9]*' | head -n 1); \
		echo "  $$(basename $$file): $$count testes"; \
	done
