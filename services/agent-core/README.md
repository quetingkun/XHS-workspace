# services/agent-core

AI-workspace **Agent 运行时**，支持：

- **agent-core**：本地模型，OpenAI 兼容的流式补全
- **codex**：官方 Codex app-server（`[codex] enabled=true` 且二进制可用）

轻量 `services/agent`（Brainstorm 兼容层）暂并存；对话主路径为本服务的 `/v1/agent-turns`。

## 本地启动

```bash
python server.py --addr :8081 --config configs/docker.aiw.toml --state-root ./data/state
```

Docker：`python scripts/aiw.py pack --agent-core` 然后 `python scripts/aiw.py start --agent-core`。

需 knowledge（`:8092`）与可用的 LLM。`python scripts/aiw.py start`（或 `start --agent-core`）会从
`services/knowledge/data/llm.settings.json` 注入 `OPENAI_API_KEY` / `OPENAI_BASE_URL`。

Brainstorm 前端优先 `POST /v1/agent-turns`（`function_id=brainstorm`），失败回退轻量 `services/agent`。

## Codex

1. 安装官方 Codex CLI，或将 musl 二进制放到 `deploy/codex-bin/codex-linux`  
2. 在 `configs/local.dev.toml` / `docker.aiw.toml` 打开 `[codex] enabled=true`，设置 `binary_path`  
3. 配置 `[codex.model]`（Responses API；Chat Completions 可走 adapter bridge）  
4. `[codex.routing] default_engine = "codex"`

接口、引擎和 SSE 见 `docs/README.md`。服务关系见仓库 `docs/architecture.md`。
