#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/dev/.env.local"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${DEEPSEEK_API_KEY:?请在 dev/.env.local 中设置 DEEPSEEK_API_KEY}"

# 本地默认密钥（可被 .env.local 覆盖）；DB 注册中心只存环境变量名，进程需注入实际值
export AIW_OPS_MCP_INTERNAL_SECRET="${AIW_OPS_MCP_INTERNAL_SECRET:-dev-ops-mcp-internal-secret}"
export AIW_OPS_MCP_ACTOR_SECRET="${AIW_OPS_MCP_ACTOR_SECRET:-dev-ops-mcp-actor-secret}"
export AIW_ES_LOG_MCP_INTERNAL_SECRET="${AIW_ES_LOG_MCP_INTERNAL_SECRET:-dev-es-log-internal-secret}"
export AIW_ES_LOG_MCP_ACTOR_SECRET="${AIW_ES_LOG_MCP_ACTOR_SECRET:-dev-es-log-actor-secret}"
export AIW_ES_LOG_MCP_CURSOR_SECRET="${AIW_ES_LOG_MCP_CURSOR_SECRET:-dev-es-log-cursor-secret}"
export AIW_ES_LOG_MCP_ENABLED="${AIW_ES_LOG_MCP_ENABLED:-true}"
export AIW_RCA_MCP_INTERNAL_SECRET="${AIW_RCA_MCP_INTERNAL_SECRET:-dev-rca-mcp-internal-secret}"
export AIW_RCA_MCP_ACTOR_SECRET="${AIW_RCA_MCP_ACTOR_SECRET:-dev-rca-mcp-actor-secret}"

mkdir -p /tmp/go-agent-api-state /tmp/go-agent-agentx-home

MONOREPO_ROOT="$(cd "$ROOT/.." && pwd)"
WORKSPACE_ROOT="${GO_AGENT_WORKSPACE_ROOT:-$MONOREPO_ROOT}"
RESOLVE_AIW="$MONOREPO_ROOT/scripts/resolve-aiw-api-base.sh"
if [[ -z "${GO_AGENT_PLATFORM_API_BASE:-}" && -x "$RESOLVE_AIW" ]]; then
  GO_AGENT_PLATFORM_API_BASE="$("$RESOLVE_AIW" base || true)"
fi
GO_AGENT_PLATFORM_API_BASE="${GO_AGENT_PLATFORM_API_BASE:-http://127.0.0.1:19081}"

cd "$ROOT"

exec env AGENTX_HOME=/tmp/go-agent-agentx-home \
  GO_AGENT_PLATFORM_API_BASE="$GO_AGENT_PLATFORM_API_BASE" \
  GO_AGENT_PLATFORM_INTERNAL_SECRET="${GO_AGENT_PLATFORM_INTERNAL_SECRET:-dev-master-key-change-me}" \
  python server.py \
  --addr :8081 \
  --workspace-root "$WORKSPACE_ROOT" \
  --state-root /tmp/go-agent-api-state \
  --config "$ROOT/dev/config.api.toml" \
  --agent-config-root "$ROOT/configs" \
  --cors-origins "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
