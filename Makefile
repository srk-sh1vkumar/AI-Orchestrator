.PHONY: install run test lint format clean help

help:
	@echo "AI Orchestrator - Available Commands"
	@echo "====================================="
	@echo "install     - Install dependencies"
	@echo "run         - Run the orchestrator server"
	@echo "test        - Run tests"
	@echo "lint        - Run linters"
	@echo "format      - Format code"
	@echo "clean       - Clean build artifacts"
	@echo "docker-up   - Start services with Docker Compose"
	@echo "docker-down - Stop services"

install:
	poetry install

run:
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest tests/ -v --cov=src --cov-report=html

lint:
	poetry run ruff src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run ruff --fix src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
