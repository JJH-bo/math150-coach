FROM node:24-bookworm-slim AS node-runtime

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PYTHONPATH=/app/backend \
    APP_PROFILE=mixed \
    CLASSROOM_DATA_ROOT=/var/data \
    MODEL_PREVIEW_NODE=/usr/local/bin/node \
    MODEL_PREVIEW_BROWSER=/usr/bin/chromium \
    MANIM_PYTHON=/usr/local/bin/python \
    NODE_PATH=/app/node_modules \
    PYTHON_EXECUTABLE=/usr/local/bin/python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        build-essential \
        chromium \
        fonts-dejavu-core \
        fonts-noto-cjk \
        libcairo2-dev \
        libpango1.0-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node-runtime /usr/local /usr/local
RUN corepack enable pnpm \
    && corepack prepare pnpm@11.9.0 --activate

WORKDIR /app

COPY requirements.txt package.json pnpm-lock.yaml ./
RUN pip install --requirement requirements.txt \
    && pnpm install --frozen-lockfile --prod

COPY backend ./backend
COPY frontend ./frontend
COPY tools ./tools

RUN mkdir -p /var/data

EXPOSE 8000

CMD ["sh", "-c", "python tools/bootstrap_ai_classroom.py --data-root \"$CLASSROOM_DATA_ROOT\" && exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
