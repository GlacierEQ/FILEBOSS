# Makefile — FILEBOSS DevStack

PY?=python3
PIP?=pip3

help:
	@echo 'Targets: bootstrap, precommit, fmt, lint, test, migrate, up, down, logs'

bootstrap:
	$(PY) -m venv .venv || true
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt || true
	. .venv/bin/activate && pip install -r requirements-dev.txt || true
	pre-commit install || true

precommit:
	pre-commit run --all-files || true

fmt:
	ruff format || true
	black . || true
	isort . || true

lint:
	ruff check . || true
	mypy . || true

Test:
	pytest -q

MIGRATE?=alembic upgrade head
migrate:
	$(MIGRATE)

up:
	docker compose up -d

Down:
	docker compose down

logs:
	docker compose logs -f --tail=200
