# agent-core

对话主路径。监听 `:8081`。实现是 Python，代码在 `core_svc/`。

| 文件 | 作用 |
| :--- | :--- |
| `server.py` | 进程入口 |
| `core_svc/api.py` | `/health`、`/v1/capabilities`、`/v1/engine/routing`、`POST /v1/agent-turns` |
| `core_svc/routing.py` | 默认引擎与按功能的引擎。取值是 `agent-core` 或 `codex` |
| `core_svc/local_engine.py` | 本地引擎：OpenAI 兼容的 `/chat/completions` 流式补全 |
| `core_svc/codex.py` | 官方 Codex app-server，stdio JSON-RPC |
| `core_svc/config.py` | 读 toml，环境变量可覆盖 |
| `core_svc/websearch.py` | Tavily，然后百度，然后 Bing |

启动方式见服务目录的 `README.md`。

## 引擎

- `agent-core`：本地模型。问询助手和头脑风暴各有一段系统提示词。
- `codex`：官方二进制可用、并且路由选中它时使用。二进制缺失时，除了请求头明确指定 `codex`，都会改走 `agent-core`。明确指定但二进制不可用时，SSE 返回错误「Codex 二进制不可用」。

功能只有两个：`general_qa`（问询助手）、`brainstorm`（知识头脑风暴）。

`GET/PUT /v1/engine/routing` 读写 `{state_root}/config/engine-routing.json`。`PUT` 的引擎名必须是 `agent-core` 或 `codex`。

## 一轮对话

`POST /v1/agent-turns` 在开始输出前就要有非空 `prompt`，否则 `400`，正文是 `{"error":{"code":"invalid_input","message":"prompt required"}}`。

成功时响应是 SSE，`data: {json}\n\n`。响应头有 `X-Engine` 和 `X-Engine-Version`。

生成前可以先取证，两台引擎都把摘录附在提示词后面：

- 上下文带了 `knowledge_base_ids`，或提示词里有 `[知识库检索:开启]`，并且没有 `[知识库检索:关闭]`：调用 knowledge 的 `POST /api/knowledge/retrieve`。事件名 `mcp__knowledge__search`。
- 提示词里有 `[联网搜索:开启]`：走联网搜索。事件名 `mcp__web_search__search`。

事件类型：`tool.call.started`、`tool.call.completed`、`model.output.delta`（字段 `payload.delta`）、`turn.completed`（字段 `payload.final_message`）。失败时是 `error` 和 `turn.failed`，字段 `payload.message`。

Codex 进程按会话复用一条连接，回合串行。只发 `initialize`、`thread/start`、`turn/start`。

## 测试

在 `services/agent-core` 目录执行：

```bash
python -m unittest discover -s tests -t .
```
