.PHONY: dev-api dev-web test lint compose ingest

dev-api:
	cd backend && uvicorn app.main:app --reload

dev-web:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app

compose:
	docker compose -f infra/docker-compose.yml up --build

ingest:
	cd backend && python -m app.ingest "$(Q)"
