# Codex sidecar 不可变层。官方二进制由构建上下文提供，拉起前校验 digest。
# 构建：将 release 二进制放到 deploy/codex-bin/codex，并传入 CODEX_SHA256。
# syntax=docker/dockerfile:1

ARG CODEX_VERSION=unspecified
ARG CODEX_SHA256=""

FROM alpine:3.21

ARG CODEX_VERSION
ARG CODEX_SHA256
LABEL aiw.codex.version="${CODEX_VERSION}"

RUN apk add --no-cache ca-certificates tzdata coreutils \
    && addgroup -g 60000 -S codex \
    && adduser -S -D -H -u 60000 -G codex -s /sbin/nologin -g "codex domain 0" codex

COPY deploy/codex-bin/ /tmp/codex-bin/

RUN if [ -f /tmp/codex-bin/codex ]; then \
      if [ -z "${CODEX_SHA256}" ]; then echo "CODEX_SHA256 is required when binary is present" >&2; exit 1; fi; \
      echo "${CODEX_SHA256}  /tmp/codex-bin/codex" | sha256sum -c -; \
      install -o root -g root -m 0755 /tmp/codex-bin/codex /usr/local/bin/codex; \
    else \
      echo "Codex binary absent; image is isolation-only" >&2; \
    fi \
    && rm -rf /tmp/codex-bin \
    && mkdir -p /var/lib/ai-workspace/codex-home /var/lib/ai-workspace/workspaces /tmp/codex \
    && chown -R 60000:60000 /var/lib/ai-workspace /tmp/codex \
    && chmod 0700 /var/lib/ai-workspace/codex-home /var/lib/ai-workspace/workspaces /tmp/codex

USER 60000:60000
WORKDIR /var/lib/ai-workspace/workspaces
