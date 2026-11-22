# alert_context v1（agent_driven 输入契约）

> 机器可读 Schema（Phase 4）：`contracts/rca/alert-context-v1.schema.json`  
> 组装方：`platform-api/internal/rca` `ContextBuilder`（Phase 4）；Phase 0~3 由 `BuildAgentDrivenCollectionPrompt` 提供最小骨架。

## 用途

`agent_driven` 模式下，Agent **不**接收完整 `EvidenceBundle agent_view`，而是接收 `alert_context`，在 turn 内通过 `mcp__rca_*__*` MCP 工具按需采集证据，最终仍输出 `RcaReport v1`。

## MVP 必填字段（Phase 0~3）

| 字段 | 说明 |
|------|------|
| `schema_version` | 固定 `"1.0"` |
| `job_id` | RCA job ID；**每次工具调用必须原样传入** |
| `incident_id` | Incident ID |
| `collection_mode` | 固定 `"agent_driven"` |
| `incident` | `{ title, status }` 摘要 |
| `alerts` | 告警数组，每项含 `alert_id`, `name`, `status`, `labels`, `annotations` |

## Phase 4 扩展字段

| 字段 | 说明 |
|------|------|
| `query_scope` | `{ service, namespace, pod, deployment, system, system_id }` — MCP 查询模板占位符 |
| `monitoring_id` | 业务系统 ID（=`business_systems.id`，与 `query_scope.system_id` 同值） |
| `time_windows` | `{ core_window_minutes, log_window_minutes }` — 覆盖默认时间窗 |
| `affected_services` | 从 labels/CMDB 解析的受影响服务列表 |
| `capabilities` | 数据树接入能力；见下 |

## capabilities（数据源能力门）

后端 `ContextBuilder` 按业务系统数据树 binding 写入，供 Agent 决定是否调用系统专属补证工具。

| 字段 | 说明 |
|------|------|
| `capabilities.npm.available` | `true` = 该系统已绑定 `xieyun_npm` → 阶段 E **必调** `mcp__rca_npm__url_errors` |
| `capabilities.npm.system_id` | 解析到的业务系统 ID（有则写入） |
| `capabilities.npm.binding_id` | NPM binding ID（仅 `available=true`） |
| `capabilities.npm.data_source_id` | NPM 数据源 ID（仅 `available=true`） |
| `capabilities.npm.data_source_status` | 如 `healthy`（有则写入） |
| `capabilities.skywalking.available` | `true` = 该系统已绑定 `skywalking` → 阶段 D **必调** `mcp__rca_skywalking__slow_traces` |
| `capabilities.skywalking.system_id` | 解析到的业务系统 ID（有则写入） |
| `capabilities.skywalking.binding_id` | SkyWalking binding ID（仅 `available=true`） |
| `capabilities.skywalking.data_source_id` | SkyWalking 数据源 ID（仅 `available=true`；采集侧优先用此选源） |
| `capabilities.skywalking.data_source_status` | 如 `healthy`（有则写入） |
| `capabilities.k8s_event.available` | `true` = 该系统日志层已绑 SLS 且 `rca_role=k8s_event` → 阶段 F **必调** `mcp__rca_elasticsearch__cluster_errors` |
| `capabilities.k8s_event.system_id` | 解析到的业务系统 ID（有则写入） |
| `capabilities.k8s_event.binding_id` | K8s 事件 binding ID（仅 `available=true`） |
| `capabilities.k8s_event.data_source_id` | SLS 数据源 ID（仅 `available=true`） |
| `capabilities.k8s_event.data_source_status` | 如 `healthy`（有则写入） |

Agent **禁止**再用系统名白名单或标题猜测是否调 SkyWalking / NPM / K8s 事件。各轨独立，互不依赖。

> **注意**：`alert_context` **不包含** `suggested_layers` / `primary_layer`；RCA 采集流程**不做维度推断**，MCP 工具 InputSchema **不暴露** `layer`（见 [discovery-workflow.md](discovery-workflow.md)）。

## Grafana 面板采集约定

1. 调用 `mcp__rca_grafana__list_panels` 时**必填** `system`（取自 `query_scope.system` 或 `labels.system`）。
2. 后端按告警所属系统列举 `used_for_rca=true` 面板；`items` 非空时 Agent **在阶段1内紧接**对列表内全部可查询面板调用 `query_panel`。
3. **阶段1（rca_grafana）全部完成后**，才可进入 SkyWalking / NPM / 日志 Server（见 [discovery-workflow.md](discovery-workflow.md)）。
4. 若该系统无 RCA 面板，工具返回 `ok: true`、`items: []` 与 `message`，**不算失败**；记入 `missing_evidence` 后进入后续 Server。

## 从 labels 推断 scope（无 query_scope 时）

工具层会调用 `collectors.BuildQueryScope(alerts)`，常见 label 键：

| 语义 | 常见 label 键 |
|------|----------------|
| 服务 | `service`, `app`, `application` |
| 命名空间 | `namespace`, `kubernetes_namespace` |
| Pod | `pod`, `kubernetes_pod_name` |
| 部署 | `deployment`, `kubernetes_deployment` |

Agent **仅在 user prompt** 中读取 `alert_context`；**MCP 工具调用只传 `job_id` 与工具特有字段**（`list_panels` 另须传 `system`）。InputSchema 不暴露 `alert_context`/`layer`；后端 `ToolRequestEnricher` 按 job_id 注入完整上下文。

## 与 EvidenceBundle 的关系

| 阶段 | Agent 输入 | 落库产物 |
|------|------------|----------|
| 采集 turn | `alert_context` + 工具返回值 | Phase 4 `EvidenceAssembler` 组装 Bundle |
| 报告 turn | EvidenceBundle / `agent_view` | RcaReport v1 |

采集过程中记录的 `evidence_id`（来自 MCP 响应）是 `RcaReport` 引用的唯一合法 ID 来源。
