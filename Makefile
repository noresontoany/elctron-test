.PHONY: init up dev down logs ps migrate seed check test test-backend test-frontend simulate simulate-bg simulate-stop simulate-logs
SIM_ARGS ?=
init:
	python scripts/init_env.py
up: init
	docker compose up -d --build --wait

dev: init
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

down:
	docker compose down
logs:
	docker compose logs -f --tail=100
ps:
	docker compose ps
migrate:
	docker compose exec api alembic upgrade head
seed:
	docker compose exec api python -m src.seed
check:
	uv run --project backend ruff check backend
	uv run --project backend ruff check simulate.py
	uv run --project backend ruff format --check backend
	cd frontend && npm run typecheck
	cd frontend && npm run format:check

test: test-backend test-frontend

test-backend:
	uv run --project backend pytest backend/tests -q

test-frontend:
	cd frontend && npm run test:unit && npm run test:e2e

simulate:
	uv run --project backend python simulate.py $(SIM_ARGS)

simulate-bg:
	uv run --project backend python simulate.py --background $(SIM_ARGS)

simulate-stop:
	uv run --project backend python simulate.py --stop

simulate-logs:
	tail -f .artifacts/simulator.log
