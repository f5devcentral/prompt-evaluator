# Makefile for Prompt Evaluator - Simplified Core Testing

.PHONY: help install install-test test test-core test-simple test-converter test-reader test-integration lint format type-check security clean setup-dev

# Default target
help:
	@echo "Prompt Evaluator - Core Functionality Testing"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install production dependencies"
	@echo "  install-test     Install testing dependencies"
	@echo "  setup-dev        Setup development environment"
	@echo ""
	@echo "Core Testing:"
	@echo "  test             Run all tests (legacy)"
	@echo "  test-core        Run all core functionality tests"
	@echo "  test-simple      Run core functionality tests only"
	@echo "  test-converter   Run dataset converter tests only"
	@echo "  test-reader      Run enhanced reader tests only"
	@echo "  test-integration Run integration tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security         Run security scans"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up generated files"
	@echo "  validate         Validate setup and dependencies"

# Installation
install:
	pip install -r requirements.txt

install-test:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

setup-dev: install-test
	@echo "Setting up development environment..."
	@echo "Creating .env file if it doesn't exist..."
	@if [ ! -f .env ]; then \
		echo "CALYPSOAI_URL=https://calypsoai.app" > .env; \
		echo "CALYPSOAI_TOKEN=your_api_token_here" >> .env; \
		echo "Created .env file with template values"; \
	fi
	@echo "Development environment ready!"

# Testing
test:
	python -m pytest tests/ -v

test-core:
	python tests/test_runner_simple.py --all

test-simple:
	python tests/test_runner_simple.py --core

test-converter:
	python tests/test_runner_simple.py --converter

test-reader:
	python tests/test_runner_simple.py --reader

test-integration:
	python tests/test_runner_simple.py --integration

# Legacy test commands (kept for compatibility)
test-unit:
	python -m pytest tests/test_dataset_converter.py tests/test_enhanced_reader.py -v

test-format:
	python -m pytest tests/test_core_functionality.py -v

test-migration:
	@echo "Migration tests removed - use test-core instead"

test-performance:
	python -m pytest tests/test_core_functionality.py::TestCoreIntegration::test_performance_with_large_dataset -v

test-coverage:
	python -m pytest tests/test_core_functionality.py tests/test_dataset_converter.py tests/test_enhanced_reader.py tests/test_integration.py --cov=. --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black . --check --diff

format-fix:
	black .

type-check:
	mypy . --ignore-missing-imports --no-error-summary

security:
	bandit -r . -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Utilities
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf safety-report.json
	rm -rf .pytest_cache/

validate:
	python validate_setup.py

# Pre-commit checks
pre-commit: lint format type-check test-core
	@echo "Pre-commit checks completed!"

# GitLab CI/CD simulation
ci-test: install-test lint format type-check test-core security
	@echo "GitLab CI/CD simulation completed!"

# Development workflow
dev-test: test-simple test-converter
	@echo "Development tests completed!"

# Release preparation
release-check: clean install-test lint format type-check test-core security
	@echo "Release checks completed!"
	@echo "Ready for release!"

# Quick test for development
quick-test:
	python tests/test_runner_simple.py --core

# Documentation testing
test-docs:
	@echo "Testing documentation examples..."
	python tools/demo_improved_formats.py
	python tools/example_improved_formats.py
	@echo "Documentation tests completed!"
