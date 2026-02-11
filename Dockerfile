FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Use the system Python (not uv-managed) so venv symlinks work in final stage
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install dependencies (without the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-group lint

# --- Final stage: runtime only ---
FROM python:3.13-slim

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY ./app ./app

ENV PORT=8080
EXPOSE ${PORT}
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
