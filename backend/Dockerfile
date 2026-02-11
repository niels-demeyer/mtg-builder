FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run python migrations/run_migrations.py && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
