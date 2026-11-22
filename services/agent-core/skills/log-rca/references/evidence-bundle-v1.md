# EvidenceBundle v1（Agent 输入契约）

> 机器可读 Schema：[contracts/rca/evidence-bundle-v1.schema.json](../../../../contracts/rca/evidence-bundle-v1.schema.json)
> Golden Sample：[contracts/rca/samples/db_pool_exhausted/evidence-bundle.json](../../../../contracts/rca/samples/db_pool_exhausted/evidence-bundle.json)
> 报告 turn 如何引用证据 / 判定充分性：见 [analysis-rules.md](analysis-rules.md)（默认预加载）；本文件通常不必再读。

## 用途

`EvidenceBundle` 是 RCA Agent 的**唯一事实输入**。智能体不得引用 bundle 与 `agent_view` 之外的主机名、指标值、日志原文。

## MVP0 必填区块

| 区块 | 说明 |
|------|------|
| `schema_version` | 固定 `"1.0"` |
| `bundle_id` / `job_id` / `incident_id` / `revision` | 版本追溯 |
| `incident` | 分析对象摘要 |
| `alerts` | 相关告警（MVP0 通常 1 条） |
| `metrics` | 指标证据扁平数组（每条含 `evidence_id`、`layer`） |
| `logs.sources.application` | 日志 cluster / hits（可为 failed） |
| `evidence_quality` | 缺失 / 失败 / 降级 |
| `collection_trace` | 采集审计 |

## metrics 结构（v1 扁平数组）

`metrics` 为 **数组**，不再使用 `metrics.application` / `metrics.business` 等分桶对象。

每条元素为一条指标证据，**必须**含稳定 `evidence_id`（`metric_*`），建议含 `layer`：

| 字段 | 说明 |
|------|------|
| `evidence_id` | RcaReport 引用 ID |
| `layer` | `application` \| `business` \| `infrastructure` \| `database` |
| `metric_name` / `summary` / `current` / `stats` | 指标语义与数值摘要 |
| `source` | 如 `grafana_panel`、`prometheus`、`grafana_alert` |
| `time_window` | 与告警窗口对齐 |

示例（单条 business 层 Grafana 面板）：

```json
"metrics": [
  {
    "evidence_id": "metric_46b6356a93b0e209",
    "layer": "business",
    "metric_name": "外网MQ连接等待数(>100)",
    "current": 71,
    "source": "grafana_panel",
    "summary": "外网MQ连接等待数(>100) current=71.00 avg=896.50 ..."
  }
]
```

> **兼容说明**：历史 bundle 可能仍为 `metrics.{application,business,...}[]` 分桶；`platform-api` 读取时通过 `metricsAsList` 扁平化。新写入一律使用数组格式。

## logs 结构（MVP0 统一表达）

使用 `logs.sources.<dimension>.clusters[]`，**不要**同时使用旧版 `sampled_logs` 扁平数组。

每个 cluster 必须有稳定 `evidence_id`（`log_cluster_*`），供 RcaReport 引用。  
`search_logs` 的单条命中使用 `log_hit_*`，可引用。`cluster_errors` 空簇时不再依赖 `fallback_hits`（两 tool 独立）。

## agent_view

由 `platform-api` 按 token 预算裁剪生成，字段结构与完整 bundle 一致但体量更小。Task Prompt 中嵌入的是 `agent_view`，不是 raw payload。

**agent_driven 模式**：Bundle 在 Agent turn 完成后由 `EvidenceAssembler` 从 `rca_tool_audits` 组装落库；分析阶段 Agent 以工具返回的 `evidence_id` 为事实来源。

## 与旧版 log-rca 输入的区别

| 旧版（Dify） | v1 |
|--------------|-----|
| `parsed_alert_json` | `incident` + `alerts[]` |
| `dimension_metrics` | `metrics[]`（每条带 `evidence_id` 与 `layer`） |
| `sampled_logs` | `logs.sources.*.clusters[]` |
| 无 | `evidence_quality` 必填 |

分析时优先读取高 `relevance_score` 的 log cluster，不得把 `failed_collectors` 解释为「无异常」。
