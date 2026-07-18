FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PYTHONPATH=/app/backend \
    APP_PROFILE=mixed \
    CLASSROOM_DATA_ROOT=/var/data \
    MODEL_PREVIEW_NODE=/usr/bin/node \
    MODEL_PREVIEW_BROWSER=/usr/bin/chromium \
    NODE_PATH=/app/node_modules \
    PYTHON_EXECUTABLE=/usr/local/bin/python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        chromium \
        fonts-dejavu-core \
        fonts-noto-cjk \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt package.json package-lock.json ./
RUN pip install --requirement requirements.txt \
    && npm ci --omit=dev

COPY backend ./backend
COPY frontend ./frontend
COPY tools ./tools

RUN mkdir -p /var/data

EXPOSE 8000

CMD ["sh", "-c", "python tools/bootstrap_ai_classroom.py --data-root \"$CLASSROOM_DATA_ROOT\" && exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
