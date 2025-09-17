.PHONY: help install lint format test clean dev-deps check

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev-deps    Install development dependencies"
	@echo "  format      Format code with black and isort"
	@echo "  lint        Run linting checks"
	@echo "  test        Run tests with coverage"
	@echo "  check       Run all checks (format, lint, test)"
	@echo "  clean       Clean cache files"
	@echo "  pre-commit  Setup pre-commit hooks"

install:
	poetry install

dev-deps:
	poetry install --extras dev

format:
	poetry run black securnote tests
	poetry run isort securnote tests

lint:
	poetry run flake8 securnote tests
	poetry run mypy securnote

test:
	poetry run pytest

check: format lint test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

pre-commit:
	poetry run pre-commit install
