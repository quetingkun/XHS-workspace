# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
 || pip install -r requirements.txt

COPY core_svc ./core_svc
COPY server.py .
COPY configs /app/configs
COPY skills /app/skills

COPY deploy/codex-bin/codex-linux /opt/codex-bin/codex-linux
RUN if [ -s /opt/codex-bin/codex-linux ]; then \
      cp /opt/codex-bin/codex-linux /usr/local/bin/codex && chmod 0755 /usr/local/bin/codex; \
    fi

RUN mkdir -p /data/state /workspace /var/lib/ai-workspace/codex-home \
    && useradd -r -u 10001 -m app \
    && chown -R app:app /app /data /workspace /var/lib/ai-workspace

USER app
EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8081/health || exit 1

ENTRYPOINT ["python", "/app/server.py"]
CMD ["--addr", ":8081", "--config", "/app/configs/docker.aiw.toml"]
