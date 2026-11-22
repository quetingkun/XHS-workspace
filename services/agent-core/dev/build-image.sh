#!/usr/bin/env bash
# 构建 go-agent-core 镜像
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${GO_AGENT_CORE_IMAGE:-go-agent-core:latest}"

echo "==> 准备 Codex Linux 二进制 ..."
bash "${ROOT}/deploy/ensure-codex-bin.sh"

echo "==> 构建镜像 ${IMAGE} ..."
docker build -t "${IMAGE}" -f "${ROOT}/Dockerfile" "${ROOT}"

echo "==> 完成。示例启动:"
echo "    docker run --rm -p 8081:8081 -e DEEPSEEK_API_KEY=\$DEEPSEEK_API_KEY ${IMAGE}"
