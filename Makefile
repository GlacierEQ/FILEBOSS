.PHONY: install test lint format check-types check-security clean help httpyac httpyac-env httpyac-test httpyac-docs

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
BLACK = black
ISORT = isort
MYPY = mypy
BANDIT = bandit
PYLINT = pylint
HTTPYAC = npx httpyac
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Default target
help:
	@echo "\n\033[1mDevelopment:\033[0m"
	@echo "  install           Install development dependencies"
	@echo "  format            Format code with Black and isort"
	@echo "  clean             Remove build artifacts and cache"
	@echo "\n\033[1mTesting & Quality:\033[0m"
	@echo "  test              Run tests with coverage"
	@echo "  lint              Run all linters"
	@echo "  check-types       Run type checking with mypy"
	@echo "  check-security    Run security checks with bandit"
	@echo "\n\033[1mAPI Development:\033[0m"
	@echo "  httpyac           Run HTTPYac CLI"
	@echo "  httpyac-env       Show HTTPYac environment"
	@echo "  httpyac-test      Run API tests with HTTPYac"
	@echo "  httpyac-docs      Generate API documentation"
	@echo "\n\033[1mDocker:\033[0m"
	@echo "  docker-build      Build Docker image"
	@echo "  docker-up         Start containers"
	@echo "  docker-down       Stop containers"

# Install dependencies
install:
	$(PIP) install -e ".[dev]"
	npm install -g @httpyac/cli
	pre-commit install

# Run tests
TEST_ARGS = -v --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html
test:
	$(PYTEST) $(TEST_ARGS) tests/

# Run linters
lint: check-format check-types check-security

# Format code
format:
	$(BLACK) app/ tests/
	$(ISORT) app/ tests/

# Check code formatting
check-format:
	$(BLACK) --check app/ tests/
	$(ISORT) --check-only app/ tests/

# Run type checking
check-types:
	$(MYPY) app/

# Run security checks
check-security:
	$(BANDIT) -r app/

# HTTPYac Commands
httpyac:
	$(HTTPYAC) --help

httpyac-env:
	$(HTTPYAC) --version
	$(HTTPYAC) --print-config

httpyac-test:
	$(HTTPYAC) test tests/api/*.http --all --json

httpyac-docs:
	$(HTTPYAC) docs --output docs/api --format html

# Docker Commands
docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

# Clean up
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} \;
	find . -type d -name '*.pyc' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} \;
	find . -type d -name '.httpyac' -exec rm -rf {} \;
	rm -rf .coverage coverage.xml htmlcov/ build/ dist/ *.egg-info/ docs/api/

# Pre-commit hooks
pre-commit-install:
	pre-commit install

# Run pre-commit on all files
pre-commit-all:
	pre-commit run --all-files
