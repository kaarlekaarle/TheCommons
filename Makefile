.PHONY: help install test lint format clean setup-db run-dev run-prod docker-build docker-run

# Variables
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
ISORT := $(VENV)/bin/isort

help:  ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "  %-20s %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

install:  ## Install development dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PIP) install pre-commit
	pre-commit install

test:  ## Run tests
	$(PYTEST) tests/ -v --cov=backend --cov-report=term-missing

lint:  ## Run linters
	$(FLAKE8) backend/ tests/
	$(MYPY) backend/ tests/
	$(ISORT) --check-only backend/ tests/

format:  ## Format code
	$(BLACK) backend/ tests/
	$(ISORT) backend/ tests/

clean:  ## Clean up build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

setup-db:  ## Set up the database
	alembic upgrade head

run-dev:  ## Run development server with monitoring
	./scripts/start_server.sh

run-prod:  ## Run production server
	./scripts/start_server.sh

stop-server:  ## Stop the server gracefully
	./scripts/stop_server.sh

monitor:  ## Start server with automatic monitoring and restart
	./scripts/server_monitor.sh

health-check:  ## Check server health
	curl -s http://localhost:8000/health/comprehensive | jq .

server-logs:  ## View server logs
	tail -f logs/server.log

docker-build:  ## Build Docker image
	docker-compose build

docker-run:  ## Run Docker containers
	docker-compose up

docker-stop:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f

docker-clean:  ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

migrate:  ## Create and run database migrations
	alembic revision --autogenerate -m "$(message)"
	alembic upgrade head

seed-db:  ## Seed the database with test data
	$(PYTHON) scripts/seed_database.py

backfill-decisions:  ## Backfill decision_type and direction_choice fields
	cd backend && $(PYTHON) scripts/backfill_decision_type.py

check-security:  ## Run security checks
	bandit -r backend/
	safety check

update-deps:  ## Update dependencies
	$(PIP) install --upgrade pip-tools
	pip-compile --upgrade requirements.in
	pip-compile --upgrade requirements-dev.in

docs:  ## Generate documentation
	cd docs && make html

serve-docs:  ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8001 