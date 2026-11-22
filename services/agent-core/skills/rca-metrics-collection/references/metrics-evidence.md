# MCP 指标/日志证据解读

> 现行 agent-core 不调用这些 MCP 工具。下面是证据 JSON 的字段说明。

## metric evidence 结构（典型）

`mcp__rca_baseline__query_alert_window` / `mcp__rca_grafana__query_panel` / `mcp__rca_metrics__*` 的 `evidence` 字段：

```json
{
  "evidence_id": "metric_01H...",
  "metric_name": "hikaricp_connections_active",
  "current_value": 98.0,
  "baseline_value": 40.0,
  "offset_percent": 145.0,
  "unit": "connections",
  "time_window": { "start": "...", "end": "..." },
  "labels": { "service": "order-service" }
}
```

### 解读要点

| 字段 | 分析用途 |
|------|----------|
| `evidence_id` | **唯一**可写入 `RcaReport.evidence_chain` / `root_cause_candidates[].evidence_ids` |
| `offset_percent` | 相对基线偏离；>50% 通常在 summary 中强调 |
| `current_value` vs `baseline_value` | 量化对比，禁止改写数值 |
| `time_window` | 与告警 `starts_at` 对齐说明异常时段 |

### 异常判定（运维常识）

- 连接池：`current` 接近 `max` 或远高于 `baseline` → 池耗尽风险
- CPU：持续 >75% 且与告警时间重叠 → 资源瓶颈
- 内存：>85% 或 OOM 相关日志同时出现 → 高危
- 轻微偏离（<10%）→ 降置信，勿作唯一根因

## log cluster 结构（典型）

`mcp__rca_elasticsearch__cluster_errors` 的 `clusters[]`：

```json
{
  "evidence_id": "log_cluster_01H...",
  "message_template": "Connection is not available, request timed out after * ms",
  "severity": "error",
  "count": 42,
  "relevance_score": 0.91,
  "summary": "...",
  "sample_logs": [ { "timestamp": "...", "message": "..." } ]
}
```

### 解读要点

- 优先 `relevance_score` 高且 `count` 大的 cluster
- `message_template` 用于与 metric 异常（如连接池满）交叉验证
- `sample_logs` 是引用原文的唯一来源，禁止 paraphrase 为不存在的堆栈

## collection_trace

每次工具响应可能含 `collection_trace`：

```json
{ "tool": "baseline.query_alert_window", "status": "ok", "latency_ms": 120 }
```

用于判断采集是否降级；**不**写入 `RcaReport` 正文，但可影响 `confidence`。

## evidence_quality 等价判断（Agent 自检）

在输出 `RcaReport` 前自检：

| 条件 | 建议 |
|------|------|
| 无任何 `evidence_id` | `confidence < 0.4`，`missing_evidence` 列全缺失项 |
| 仅 metric 无 log | `confidence` 中等，注明日志未采集 |
| metric + log 时间对齐且语义一致 | 可提高 `confidence`，写入 `evidence_chain` |
| 多次工具 `ok: false` | `final_result` 倾向 `inconclusive` 或 `needs_more_data` |

## 与 EvidenceBundle 的字段对应

| agent_driven 工具输出 | EvidenceBundle 路径 |
|----------------------|---------------------|
| metric `evidence` | `metrics[]`（每条带 `evidence_id` 与 `layer`） |
| log `clusters[]` | `logs.sources.*.clusters[]` |
| SkyWalking `traces[]` / `rows[]` | `traces.slow_traces[]` / `traces.db_sql[]` |
| NPM `urls[]` / 方向分榜 | `traces.npm_urls[]` |
| NPM `connect_fail_requests[]` | `traces.npm_connect_fail[]` |
| 工具失败 | `evidence_quality.failed_collectors[]`（Phase 4 组装） |
