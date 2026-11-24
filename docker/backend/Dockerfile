FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app PYTHONUNBUFFERED=1
CMD ["sh", "-c", "alembic upgrade head && python -m src.seed && exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]
