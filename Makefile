.PHONY: init up dev down logs ps migrate seed check test test-backend test-frontend simulate simulate-bg simulate-stop simulate-logs bench bench-tabs local-ca metrics
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
	uv run --project backend ruff check simulate.py scripts/benchmark.py
	uv run --project backend ruff format --check backend scripts/benchmark.py
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

BENCH_ARGS ?=
bench:
	uv run scripts/benchmark.py $(BENCH_ARGS)

bench-tabs:
	cd frontend && npm run bench:tabs -- $(BENCH_ARGS)

local-ca:
	mkdir -p .artifacts
	docker compose exec -T caddy cat /data/caddy/pki/authorities/local/root.crt > .artifacts/caddy-root.crt

metrics:
	docker compose exec -T api python -c 'import urllib.request; print(urllib.request.urlopen("http://localhost:8000/internal/metrics").read().decode())'
