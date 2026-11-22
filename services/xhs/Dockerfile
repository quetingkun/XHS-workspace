# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    XHS_HOST=0.0.0.0 \
    XHS_PORT=8097 \
    AGENT_CORE_URL=http://agent-core:8081 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /workspace

# Playwright：driver 的 node 需要 libatomic1；Chromium 依赖由 install --with-deps 拉齐
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates wget tzdata libatomic1 \
    && rm -rf /var/lib/apt/lists/*

COPY services/xhs/requirements.txt /tmp/xhs-requirements.txt
RUN pip install -r /tmp/xhs-requirements.txt \
    && python -m playwright install --with-deps chromium

COPY services/xhs /workspace/services/xhs
COPY apps/web /workspace/apps/web

RUN mkdir -p /workspace/data/xhs \
    && useradd -r -u 10002 -m app \
    && chown -R app:app /workspace /ms-playwright

USER app
EXPOSE 8097

HEALTHCHECK --interval=20s --timeout=5s --start-period=25s --retries=5 \
    CMD wget -qO- http://127.0.0.1:8097/health || exit 1

CMD ["python", "/workspace/services/xhs/server.py"]