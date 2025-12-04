# PlayerGold Development Makefile

.PHONY: help install dev-install test lint format clean run

# Default target
help:
	@echo "PlayerGold Development Commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run test suite"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean build artifacts"
	@echo "  run          - Run PlayerGold application"
	@echo "  setup        - Initial project setup"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/ config/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run the application
run:
	python -m src.main

# Initial project setup
setup:
	@echo "Setting up PlayerGold development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	@mkdir -p data logs models wallets
	@echo "Created necessary directories"
	@echo "Setup complete! Run 'make dev-install' to install dependencies"

# Development server with auto-reload
dev:
	python -m src.main --debug

# Check project structure
check-structure:
	@echo "Project structure:"
	@tree -I '__pycache__|*.pyc|.git' .