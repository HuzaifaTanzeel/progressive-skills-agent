# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Repo layout expected by ADK + admin routes:
#   /app/backend  — package root (agents_dir)
#   /app/skills   — Agent Skills library
#   /app/evals    — eval sets + curated results for /api/admin/eval-summary
COPY backend/pyproject.toml backend/README.md ./backend/
COPY backend/adk_app ./backend/adk_app
COPY backend/harness ./backend/harness
COPY backend/server ./backend/server
COPY backend/tests ./backend/tests
COPY skills ./skills
COPY evals ./evals

WORKDIR /app/backend
RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
