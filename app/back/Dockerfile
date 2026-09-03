FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_CACHE=/var/lib/rag_platform/hf-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app/back/src app/back/src
COPY app/back/docker app/back/docker

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install .[embeddings] \
    && chmod +x /app/app/back/docker/api-entrypoint.sh /app/app/back/docker/worker-entrypoint.sh

EXPOSE 8780

CMD ["/app/app/back/docker/api-entrypoint.sh"]
