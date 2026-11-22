#!/usr/bin/env bash
# 后台启动 go-agent-core（:8081），供网关 / start-all 依赖
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="$ROOT/dev/.env.local"
REPO_ENV="$ROOT/../.env"
PID_FILE="${GO_AGENT_CORE_PID_FILE:-/tmp/go-agent-dev/agent.pid}"
LOG_FILE="${GO_AGENT_CORE_LOG_FILE:-/tmp/go-agent-dev/logs/go-agent-core.log}"
HEALTH_URL="http://127.0.0.1:8081/health"
mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$PID_FILE")"

# 仓库根 .env（MCP 密钥等）→ 再被 .env.local 覆盖
if [[ -f "$REPO_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ENV"
  set +a
fi
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${DEEPSEEK_API_KEY:?请在 dev/.env.local 中设置 DEEPSEEK_API_KEY}"
# Codex sidecar 只读进程环境里的密钥名。优先本机 OpenAI-compatible（omlx），否则 DeepSeek。
export AIW_CODEX_MODEL_KEY="${AIW_CODEX_MODEL_KEY:-${OPENAI_API_KEY:-$DEEPSEEK_API_KEY}}"
mkdir -p /tmp/go-agent-dev/codex-home

# DB 注册中心只存 secret 环境变量名；进程必须注入实际值（与 platform-api configs/local.yaml 对齐）
export AIW_OPS_MCP_INTERNAL_SECRET="${AIW_OPS_MCP_INTERNAL_SECRET:-dev-ops-mcp-internal-secret}"
export AIW_OPS_MCP_ACTOR_SECRET="${AIW_OPS_MCP_ACTOR_SECRET:-dev-ops-mcp-actor-secret}"
export AIW_ES_LOG_MCP_INTERNAL_SECRET="${AIW_ES_LOG_MCP_INTERNAL_SECRET:-dev-es-log-internal-secret}"
export AIW_ES_LOG_MCP_ACTOR_SECRET="${AIW_ES_LOG_MCP_ACTOR_SECRET:-dev-es-log-actor-secret}"
export AIW_ES_LOG_MCP_CURSOR_SECRET="${AIW_ES_LOG_MCP_CURSOR_SECRET:-dev-es-log-cursor-secret}"
export AIW_ES_LOG_MCP_ENABLED="${AIW_ES_LOG_MCP_ENABLED:-true}"
export AIW_RCA_MCP_INTERNAL_SECRET="${AIW_RCA_MCP_INTERNAL_SECRET:-dev-rca-mcp-internal-secret}"
export AIW_RCA_MCP_ACTOR_SECRET="${AIW_RCA_MCP_ACTOR_SECRET:-dev-rca-mcp-actor-secret}"

if curl -sf -m 2 "$HEALTH_URL" >/dev/null 2>&1; then
  live_pid="$(lsof -tiTCP:8081 -sTCP:LISTEN 2>/dev/null | head -1 || true)"
  [[ -n "$live_pid" ]] && echo "$live_pid" >"$PID_FILE"
  expected_aiw="${GO_AGENT_PLATFORM_API_BASE:-}"
  if [[ -n "$live_pid" && -n "$expected_aiw" ]]; then
    running_aiw="$(ps eww -p "$live_pid" 2>/dev/null | tr ' ' '\n' | sed -n 's/^GO_AGENT_PLATFORM_API_BASE=//p' | head -1 || true)"
    if [[ -n "$running_aiw" && "$running_aiw" != "$expected_aiw" ]]; then
      echo "go-agent-core 已在运行，但 GO_AGENT_PLATFORM_API_BASE=$running_aiw（期望 $expected_aiw），正在重启..."
      kill "$live_pid" 2>/dev/null || true
      sleep 1
    else
      echo "go-agent-core 已在运行 (:8081${live_pid:+, pid=$live_pid}, aiw=${running_aiw:-$expected_aiw})"
      exit 0
    fi
  else
    echo "go-agent-core 已在运行 (:8081${live_pid:+, pid=$live_pid})"
    exit 0
  fi
fi

stale="$(lsof -tiTCP:8081 -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$stale" ]]; then
  echo "==> 清理 :8081 上的陈旧进程 (pid $stale)..."
  kill $stale 2>/dev/null || true
  sleep 1
fi
rm -f "$PID_FILE"

mkdir -p /tmp/go-agent-api-state /tmp/go-agent-agentx-home

MONOREPO_ROOT="$(cd "$ROOT/.." && pwd)"
WORKSPACE_ROOT="${GO_AGENT_WORKSPACE_ROOT:-$MONOREPO_ROOT}"
RESOLVE_AIW="$MONOREPO_ROOT/scripts/resolve-aiw-api-base.sh"
if [[ -z "${GO_AGENT_PLATFORM_API_BASE:-}" && -x "$RESOLVE_AIW" ]]; then
  GO_AGENT_PLATFORM_API_BASE="$("$RESOLVE_AIW" base || true)"
fi
# 本机全栈优先直连 :19081，避免走 Docker 网关导致 MCP URL 不可达。
GO_AGENT_PLATFORM_API_BASE="${GO_AGENT_PLATFORM_API_BASE:-http://127.0.0.1:19081}"
if curl -sf -m 2 http://127.0.0.1:19081/api/health >/dev/null 2>&1; then
  GO_AGENT_PLATFORM_API_BASE="http://127.0.0.1:19081"
fi

echo "==> 后台启动 agent-core (:8081, workspace=$WORKSPACE_ROOT)..."
DAEMONIZE="$ROOT/../scripts/daemonize.sh"
bash "$DAEMONIZE" "$PID_FILE" "$LOG_FILE" "$ROOT" \
  env AGENTX_HOME=/tmp/go-agent-agentx-home \
  AIW_CODEX_MODEL_KEY="$AIW_CODEX_MODEL_KEY" \
  GO_AGENT_PLATFORM_API_BASE="$GO_AGENT_PLATFORM_API_BASE" \
  GO_AGENT_PLATFORM_INTERNAL_SECRET="${GO_AGENT_PLATFORM_INTERNAL_SECRET:-dev-master-key-change-me}" \
  AIW_OPS_MCP_INTERNAL_SECRET="$AIW_OPS_MCP_INTERNAL_SECRET" \
  AIW_OPS_MCP_ACTOR_SECRET="$AIW_OPS_MCP_ACTOR_SECRET" \
  AIW_ES_LOG_MCP_INTERNAL_SECRET="$AIW_ES_LOG_MCP_INTERNAL_SECRET" \
  AIW_ES_LOG_MCP_ACTOR_SECRET="$AIW_ES_LOG_MCP_ACTOR_SECRET" \
  AIW_ES_LOG_MCP_CURSOR_SECRET="$AIW_ES_LOG_MCP_CURSOR_SECRET" \
  AIW_ES_LOG_MCP_ENABLED="$AIW_ES_LOG_MCP_ENABLED" \
  AIW_RCA_MCP_INTERNAL_SECRET="$AIW_RCA_MCP_INTERNAL_SECRET" \
  AIW_RCA_MCP_ACTOR_SECRET="$AIW_RCA_MCP_ACTOR_SECRET" \
  GO_AGENT_STREAM_DELTA_CHARS="${GO_AGENT_STREAM_DELTA_CHARS:-4}" \
  GO_AGENT_STREAM_DELTA_INTERVAL_MS="${GO_AGENT_STREAM_DELTA_INTERVAL_MS:-8}" \
  python server.py \
  --addr :8081 \
  --workspace-root "$WORKSPACE_ROOT" \
  --state-root /tmp/go-agent-api-state \
  --config "$ROOT/dev/config.api.toml" \
  --agent-config-root "$ROOT/configs" \
  --cors-origins "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:8080,http://127.0.0.1:8080"

for i in $(seq 1 40); do
  if curl -sf -m 2 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "就绪: $HEALTH_URL (pid=$(cat "$PID_FILE"), 日志 $LOG_FILE)"
    exit 0
  fi
  sleep 0.5
done
echo "启动超时，请查看日志: $LOG_FILE" >&2
exit 1
