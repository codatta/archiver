FROM python:3.13-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv

RUN pip install --no-cache-dir uv==0.5.*

WORKDIR /app

COPY packages/api/pyproject.toml packages/api/uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY packages/api/app ./app

RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/app /app/app
COPY --chown=app:app templates /app/templates

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    TEMPLATES_DIR=/app/templates

USER app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
