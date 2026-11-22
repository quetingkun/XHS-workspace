# Discovery → Query 工作流 SOP

> 所有 RCA 采集工具均为 MCP（`mcp__rca_*__*`），契约见 [tool-catalog.md](tool-catalog.md)。  
> **每次调用必须传 `job_id`**。工具字段形状以注入的 InputSchema 为准；**不要**传 `alert_context` / `layer`（服务端按 job_id 补全；schema 已不暴露这两项）。

> **暂时禁用**：阶段 B（Baseline）、阶段 C（Metrics）— 待 Grafana 取证调通后恢复。

## 总流程（当前启用 · 按 MCP Server 串行）

> **强制**：当前 Server 内全部取证完成后，再进入下一 Server；**禁止交叉调用**。

```text
alert_context
  → 【阶段1 · rca_grafana】list_panels → 全部可查询面板 query_panel
  → 【阶段2 · rca_skywalking】（capabilities.skywalking.available）slow_traces → db_sql
  → 【阶段3 · rca_npm】（capabilities.npm.available）url_errors
  → 【阶段4 · rca_elasticsearch】search_logs（始终）；cluster_errors 仅当 capabilities.k8s_event.available
  → 全部阶段完成后回复一行 COLLECTION_DONE（**本 turn 禁止输出 RcaReport**；报告由后续 report turn 基于 EvidenceBundle 生成）
```

**Server 顺序表**：

| 阶段 | MCP Server | 工具链 | 进入下一 Server 的前置条件 |
|------|------------|--------|---------------------------|
| 1 | `rca_grafana` | `list_panels` → `query_panel`×N | `list_panels` 已调；`items` 非空时全部可查询面板已 `query_panel` |
| 2 | `rca_skywalking` | `slow_traces` → `db_sql`? | 触发时本阶段工具已调完 |
| 3 | `rca_npm` | `url_errors` | 触发时本阶段工具已调完 |
| 4 | `rca_elasticsearch` | `search_logs`；`k8s_event` 时另调 `cluster_errors` | 日志阶段结束 |

## 阶段 A：Grafana 路径（`rca_grafana` · 阶段1 · 必须先完成）

适用于：数据接入中已为该系统配置「用于 RCA」的 Grafana 面板。

**本阶段完成前，禁止调用 `rca_skywalking` / `rca_npm` / `rca_elasticsearch` 的任何工具。**

1. **`mcp__rca_grafana__list_panels`**
   - **取值**：`system` ← `alert_context.query_scope.system` 或告警 `labels.system`（必填）
   - 出参：`items[].panel_record_id`, `panel_id`, `panel_title`, `metrics_queryable`, `used_for_rca`
   - 若 `items: []` 且含 `message`（无 RCA 面板）：记入 `missing_evidence`，继续后续阶段

2. **`mcp__rca_grafana__query_panel`**（`list_panels` 返回非空时**必调 · 紧接 list_panels**）
   - **触发 / 时机**：`items` 非空时在阶段1内连续完成；不得插入其他 Server 工具
   - **范围**：对列表内**全部** `metrics_queryable=true` 的面板各调用一次；**禁止**只挑部分
   - **取值**：`panel_record_id`（优先）或 `panel_id` ← `list_panels.items[]`
   - 若 `collection_trace.status=skipped`（时间窗无数据），记入 `missing_evidence`，**继续**下一阶段，勿重试
   - 出参：`evidence`（含 `evidence_id`）；单面板失败记入 `missing_evidence`，继续查下一个

<!--
## 阶段 B：Baseline 路径（暂时禁用）

适用于：已配置动态基线的指标（`baseline_configs` 表）。

1. **`mcp__rca_baseline__catalog`**
   - **取值**：`system` ← query_scope / labels；可选 `keyword`、`limit`
   - 出参：`items[].baseline_config_id`, `metric_name`, `rank_score`；选 `rank_score` 最高的 1~3 项

2. **`mcp__rca_baseline__query_alert_window`**
   - **取值**：`baseline_config_id` ← catalog；可选 `window_minutes`
   - 出参：`evidence`、`collection_trace`；解读见 [metrics-evidence.md](metrics-evidence.md)

## 阶段 C：Metrics 直查（暂时禁用）

适用于：已知 PromQL 或需补充趋势查询。

| 工具 | 何时使用 |
|------|----------|
| `mcp__rca_metrics__query_instant` | 单点当前值（告警触发时刻附近） |
| `mcp__rca_metrics__query_range` | 趋势、尖峰、持续异常 |
| `mcp__rca_metrics__suggest_queries` | 获取 PromQL 建议（不执行） |

必填：`job_id` + `promql`（suggest 除外）。
-->

## 阶段 D：SkyWalking（`rca_skywalking` · 阶段2）

**前置**：阶段1 `rca_grafana` 已全部完成。

**触发条件（硬门槛）**：

1. `alert_context.capabilities.skywalking.available == true`  
   （后端按业务系统数据树是否绑定 `skywalking` 写入；**不以系统名白名单或「业务告警」标题判断**）

满足则**必调**；未接入时跳过。参数不足时仍调用一次，由工具返回 `missing_evidence`，不阻断主流程。

| 工具 | 用途 |
|------|------|
| `mcp__rca_skywalking__slow_traces` | 慢链路 TopN + Span 根因；出参含 `es_targets`（pod/deployment/sts/ds/job/cronjob/host）供阶段 F |
| `mcp__rca_skywalking__db_sql` | 若 `slow_traces` 已含 `analysis.sql_statements` 则跳过；否则在有 `trace_id` 时按需提取慢 SQL |

**取值（可选显式覆盖）**：`service_name` / `endpoint` ← labels（`parent_service`/`microservice`/`request_p`）或数据源 `rca_tag_defaults`；**不要用**业务系统名 `system` 当 `service_name`。通常只传 `job_id` 即可。

**服务端检索（无需 Agent 关心细节）**：alert → alert+defaults → defaults（有强入口 path/`trace_id` 时跳过纯 defaults）。有告警 path 仍 0 命中 → 空 traces。

出参：`traces[].evidence_id`；有命中时 `es_targets` 可用于后续 ES。

**本阶段完成前，禁止调用 `rca_npm` / `rca_elasticsearch`。**

## 阶段 E：NPM（`rca_npm` · 阶段3 · 数据树接入驱动）

**前置**：阶段1 完成；若触发阶段2，则阶段2 亦已完成。

**触发条件（硬门槛）**：

1. `alert_context.capabilities.npm.available == true`  
   （后端按数据树是否绑定 `xieyun_npm` 写入；**不以系统名或告警标题判断**）

满足则**必调**；未接入时跳过。参数不足时仍调用一次，由工具返回 `missing_evidence`，不阻断主流程。

| 工具 | 用途 |
|------|------|
| `mcp__rca_npm__url_errors` | 业务 URL 错误 / 慢请求 TopN |

**取值（可选）**：`master_ip` / `namespace` / `workload` ← labels / `query_scope`；缺失时工具侧补全或返回 `missing_evidence`。通常只传 `job_id`。

**本阶段完成前，禁止调用 `rca_elasticsearch`。**

## 阶段 F：日志（`rca_elasticsearch` · 阶段4 · 最后）

**前置**：阶段1 完成；已触发的阶段2/3 亦已完成。

| 工具 | 何时 | 数据源 | 用途 |
|------|------|--------|------|
| `mcp__rca_elasticsearch__search_logs` | **始终必调** | 统一日志 ES（`rca_role=ulog`） | 应用/容器日志抽样 `hits[]` |
| `mcp__rca_elasticsearch__cluster_errors` | **仅当** `capabilities.k8s_event.available == true` | SLS（`rca_role=k8s_event`） | K8s Warning 事件聚类 `clusters[]` |

两 tool **并行独立**：无调用依赖，服务端**不会**空簇自动回退。有 K8s 事件能力时建议先 `cluster_errors` 再 `search_logs`。

**未配 SLS / `k8s_event.available=false`**：跳过 `cluster_errors`，只调 `search_logs`（勿空跑）。

**取值**：
- `keyword`/`query` ← 告警 `annotations.summary` / `description` 关键词
- 可选 `pod` / `deployment` / `namespace` / `log_types` ← 告警 labels 或阶段 D 的 `es_targets`（与 `cluster_errors`/`search_logs` 共用）
- 抽样条数由数据源 `rca_sample_size`（默认 3）决定，**勿传 `limit` 给 `search_logs`**

**Workload 开闸**（`cluster_errors` 与 `search_logs` 共用）：须至少有
`pod` ∪ `deployment` ∪ `service` ∪ `statefulset` ∪ `daemonset` ∪ `job` ∪ `cronjob` ∪ `host`（节点）之一；
仅 `namespace`、仅 `http_host`/`request_p` → `no_workload_scope` 跳过（**禁止**用域名/路径开闸扫 accesslog）。

**SkyWalking → 日志 scope**：若阶段 D 返回 `es_targets`（可含 sts/ds/job/cronjob/host），后续 **`cluster_errors`（SLS）与 `search_logs`（ES）共用** 该 workload scope。

**空结果**：
- `cluster_errors`：`not_found` / `missing` → 记 `missing_evidence`，**禁止同参重试**，继续 `search_logs`
- `search_logs`：无命中时可有 `historical_fallback`；仍无命中则 `missing_evidence`

**`search_logs` 默认过滤**：ES 默认 `log_type=k8s_normal_container`（数据源可关）。`cluster_errors`（SLS）不用该过滤。

## 推荐组合（按场景 · 当前启用）

### 通用（Grafana + 日志 · 无 K8s 事件绑定）

```text
mcp__rca_grafana__list_panels → mcp__rca_grafana__query_panel（列表内全部可查询面板）
→ mcp__rca_elasticsearch__search_logs
```

### 已接入 K8s 事件 SLS（`capabilities.k8s_event.available`）

```text
mcp__rca_grafana__list_panels → mcp__rca_grafana__query_panel
→ mcp__rca_elasticsearch__cluster_errors → mcp__rca_elasticsearch__search_logs
```

### 已接入 SkyWalking 的系统

> 触发：`capabilities.skywalking.available == true`

```text
mcp__rca_grafana__list_panels → mcp__rca_grafana__query_panel（列表内全部可查询面板）
→ mcp__rca_skywalking__slow_traces → 若有 trace_id 且无 analysis.sql → mcp__rca_skywalking__db_sql
→ （若 k8s_event）cluster_errors → search_logs
```

### 已接入 NPM 的系统

> 触发：`capabilities.npm.available == true`

```text
mcp__rca_grafana__list_panels → mcp__rca_grafana__query_panel（列表内全部可查询面板）
→ mcp__rca_npm__url_errors
→ （若 k8s_event）cluster_errors → search_logs
```

<!--
### 应用连接池类（含 Baseline，暂时禁用）

mcp__rca_grafana__list_panels → mcp__rca_grafana__query_panel
→ mcp__rca_baseline__catalog → mcp__rca_baseline__query_alert_window ×1~2
→ mcp__rca_elasticsearch__cluster_errors → mcp__rca_elasticsearch__search_logs
-->

## 失败处理

| 响应 | 动作 |
|------|------|
| `ok: false` + error | 记入 `missing_evidence`，换路径或继续日志 |
| Grafana `message` 含「无法解析告警所属系统」 | **补传** `system`（取自 `query_scope.system`）后重试一次 `list_panels` |
| Grafana `items: []` + `message`（无 RCA 面板） | 记入 `missing_evidence`（Grafana 无证据），**不 retry**，继续后续阶段 |
| HTTP 501 | 跳过，不 retry |
| `cluster_errors`：`not_found` / `missing` / 空簇 | 记 `missing_evidence`，**不重试**，继续 `search_logs` |
| `k8s_event.available=false` | **跳过** `cluster_errors`，只调 `search_logs` |
| `search_logs` 无命中 | 记入 `missing_evidence`；禁止编造 |
| 无 `evidence_id` | 不得写入 `RcaReport` 引用 |
