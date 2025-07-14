.PHONY: install test lint docs clean docker-build docker-up docker-down

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -e .

# Testing
test:
	python -m pytest

test-cov:
	python -m pytest --cov=egen --cov-report=term --cov-report=html

# Linting
lint:
	flake8 egen tests
	black --check egen tests

# Formatting
format:
	black egen tests
	isort egen tests

# Documentation
docs:
	sphinx-build -b html docs/source docs/build

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf docs/build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete