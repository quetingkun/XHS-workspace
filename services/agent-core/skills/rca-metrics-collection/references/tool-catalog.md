# RCA MCP 工具目录（入参 / 出参）

> 契约：[contracts/rca/mcp-tool-mapping.md](../../../../contracts/rca/mcp-tool-mapping.md)  
> 传输：JSON-RPC 2.0 `tools/call`（6 域 MCP Server）  
> 鉴权：`X-Internal-Secret`（`AIW_RCA_MCP_INTERNAL_SECRET`）

> **暂时禁用（Agent 侧）**：`rca_baseline` / `rca_metrics` MCP 已从根因分析 Agent 工具白名单移除，待 Grafana 取证调通后恢复。下文 API 仍保留供后续启用参考。

## MCP Server 与公开工具名

| MCP Server | HTTP 路由 | 工具数 |
|------------|-----------|--------|
| `rca_baseline` | `POST /api/internal/mcp/rca-baseline` | 4 |
| `rca_grafana` | `POST /api/internal/mcp/rca-grafana` | 2 |
| `rca_metrics` | `POST /api/internal/mcp/rca-metrics` | 4 |
| `rca_elasticsearch` | `POST /api/internal/mcp/rca-elasticsearch` | 2 |
| `rca_skywalking` | `POST /api/internal/mcp/rca-skywalking` | 2 |
| `rca_npm` | `POST /api/internal/mcp/rca-npm` | 1 |

公开工具名格式：`mcp__{server_id}__{short_name}`（与运维对话 MCP 一致）。

## 通用入参（Agent 可见）

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | string | **必填**；服务端按此补全告警上下文 |
| `system` | string | 业务系统名；**`list_panels` 必填**（取自 prompt 内 `alert_context.query_scope.system`） |
| `keyword` | string | catalog / list_panels 过滤 |
| `limit` | int | 返回条数上限（**`search_logs` 勿传**；抽样用数据源 `rca_sample_size`） |
| `window_minutes` | int | 覆盖默认告警窗口 |
| `baseline_config_id` | string | baseline 查询 |
| `monitoring_id` | string | Grafana 系统 ID |
| `panel_id` / `panel_record_id` | string | Grafana 面板 |
| `promql` / `query` | string | PromQL 或 ES 查询 |
| `data_source_id` | string | 指标数据源 |
| `step_seconds` | int | range 查询步长 |

> InputSchema **不暴露** `alert_context` / `layer`；字段细节以各工具 schema 为准。

## 工具列表（15 个）

### Baseline（`mcp_servers.rca_baseline`）

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_baseline__catalog` | catalog | `items[]`, `total` |
| `mcp__rca_baseline__query_alert_window` | query_alert_window | `evidence`, `collection_trace` |
| `mcp__rca_baseline__resolve_instance` | resolve_instance | `resolved_config_id`, `match_score` |
| `mcp__rca_baseline__get_scheduled_baseline` | get_scheduled_baseline | `scheduled_baseline`, `evidence` |

### Grafana（`mcp_servers.rca_grafana`）

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_grafana__list_panels` | list_panels | `items[]`, `monitoring_id`（入参必填 `job_id` + `system`） |
| `mcp__rca_grafana__query_panel` | query_panel | `evidence`（`list_panels` 非空时对列表内全部可查询面板各调一次） |

### Metrics（`mcp_servers.rca_metrics`）

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_metrics__query_instant` | query_instant | `evidence` |
| `mcp__rca_metrics__query_range` | query_range | `evidence`, `series` |
| `mcp__rca_metrics__query_by_layer` | query_by_layer | `evidence_list`（遗留工具，Agent 不调用） |
| `mcp__rca_metrics__suggest_queries` | suggest_queries | `suggestions[]`（仅推荐，不执行） |

### Elasticsearch（`mcp_servers.rca_elasticsearch`）

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_elasticsearch__search_logs` | search_logs | 统一日志 ES（`rca_role=ulog`）；**阶段 F 始终**；须有 workload（pod/dep/service/**sts/ds/job/cronjob/host**）；仅 `http_host`/`request_p` → `no_workload_scope`；抽样=`rca_sample_size`（默认 3）；`hits[]`（`evidence_id`=`log_hit_*`）, `total`, 可选 `historical_fallback` |
| `mcp__rca_elasticsearch__cluster_errors` | cluster_errors | SLS K8s 事件（`rca_role=k8s_event`）；开闸同 search_logs；`k8s_event` 可用时必调；0 命中=`not_found`（勿重试），无绑定=`missing`；空簇不自动 fallback |

### SkyWalking（`mcp_servers.rca_skywalking`）

> **触发**：`alert_context.capabilities.skywalking.available == true`（数据树已绑定 SkyWalking）时**必调**（见 [discovery-workflow.md](discovery-workflow.md) 阶段 D）。

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_skywalking__slow_traces` | slow_traces | `selected_trace_id`、`traces[]`、`query_meta.top_n` / `timeout_budget` / `detail_enriched`、`es_targets`。TopN 选几条就深挖几条；超时预算≈`列表预留+TopN×单条`，总上限兜底（默认 120s，须 ≤ MCP `tool_timeout`） |
| `mcp__rca_skywalking__db_sql` | db_sql | `rows[]`（需 `trace_id`；**仅当** `slow_traces.analysis.sql_statements` 为空或持有外部 `trace_id` 时调） |

**`rca_tag_defaults`（数据源接入 · RCA 取证参数）**：服务端按 **alert → alert+defaults → defaults** 检索（告警有则先用告警；同名字段告警胜；指纹相同跳过）。**告警已有 `request_p`/endpoint 或 `trace_id` 时跳过纯 defaults**（防换入口跑偏）。配置键示例：`service_name`（真实 OAP 服务名，勿填字面量 `service_name`）、`request_p`、`from_ip`、`status_code`。详见 `docs/aiw2-apm-skywalking-gap-analysis.md` §2.6 / §2.7。

### NPM（`mcp_servers.rca_npm`）

> **触发**：`alert_context.capabilities.npm.available == true`（数据树已绑定 NPM）时**必调**（见 [discovery-workflow.md](discovery-workflow.md) 阶段 E）。

| 公开工具名 | MCP 短名 | 关键出参 |
|------------|---------|----------|
| `mcp__rca_npm__url_errors` | url_errors | `workload`、`time_window`、`totals`、`top_errors[]`/`top_slow[]`（收+发合并加权主榜）、**`top_receive_errors[]`/`top_sent_errors[]`/`top_receive_slow[]`/`top_sent_slow[]`（方向分榜）**、`top_errors_by_rate[]`/`top_errors_by_count[]`、`top_slow`+`by_rate`/`by_count`、`connect_fail_requests[]`、`summary`、`urls[]`（扁平兼容）；`collection_trace.direction_boards` 含各向条数（需 `master_ip` + `namespace` + `workload`） |

## 响应信封

MCP `tools/call` 返回 `content[].text` 为 JSON；内层字段 `ok` 表示业务成功与否。`evidence_id` 仅来自工具响应。

## 示例：catalog → query

```json
// 1. mcp__rca_baseline__catalog
{ "job_id": "job-1", "system": "order-service", "keyword": "pool" }

// 2. mcp__rca_baseline__query_alert_window
{ "job_id": "job-1", "baseline_config_id": "bcfg-xxx" }
```

## 示例：grafana

```json
// 1. mcp__rca_grafana__list_panels
{ "job_id": "job-1", "system": "order-service" }

// 2. mcp__rca_grafana__query_panel
{ "job_id": "job-1", "panel_record_id": "smp_12" }
```
