.PHONY: dev run ingest warm build

VENVPY ?= python

setup:
	cd backend && pip install uv && uv pip install -e . --system

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

run:
	cd infra && docker compose up --build

ingest:
	$(VENVPY) scripts/ingest_data.py

warm:
	$(VENVPY) scripts/warm_start.py

build:
	docker build -f docker/Dockerfile -t agentic-med-assistant .
