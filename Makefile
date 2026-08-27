.PHONY: dev test lint typecheck imports eval up down data docs docs-assets frontend-dev frontend-build frontend-types

dev:
	uv run uvicorn sentinel.api.main:app --reload --port 8000

test:
	uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

imports:
	PYTHONPATH=src uv run lint-imports

check: lint typecheck imports test

eval:
	uv run python -m evals.run

up:
	docker compose up --build

down:
	docker compose down

data:
	uv run python -m data.build_policy_kb
	uv run python -m data.build_accounts

docs:
	uv run mkdocs serve

docs-assets:
	PYTHONPATH=. uv run python docs/generate_plots.py

frontend-dev:
	cd frontend && npm install && npm run dev

frontend-build:
	cd frontend && npm install && npm run build
