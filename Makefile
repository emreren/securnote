.PHONY: help install clean

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  clean       Clean cache files"

install:
	poetry install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
