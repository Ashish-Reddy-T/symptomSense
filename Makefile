.PHONY: dev run ingest fmt lint type test build warm

VENVPY ?= python

setup:
	cd backend && pip install uv && uv pip install -e .[dev] --system

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

run:
	cd infra && docker compose up --build

ingest:
	python scripts/ingest_data.py

warm:
	python scripts/warm_start.py

fmt:
	ruff check backend --fix
	black backend

lint:
	ruff check backend

type:
	mypy backend

test:
	pytest backend -q

build:
	docker build -f docker/Dockerfile -t agentic-med-assistant .
