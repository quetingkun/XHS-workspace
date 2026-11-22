---
name: rca-metrics-collection
description: 通过 mcp__rca_*__* MCP 工具做 Agent 驱动的 RCA 证据采集。先 Grafana 面板 discovery，再按 alert_context 查询 Elasticsearch 日志。适用于 collection_mode=agent_driven、prompt 含 alert_context，或值班需要在输出 RcaReport v1 前增量取证。
triggers: [agent_driven, alert_context, mcp__rca_grafana, mcp__rca_elasticsearch, 按需采集, 指标采集, 日志采集, discovery, query_panel, cluster_errors]
version: 1.5.3
metadata: {"go_agent":{"category":"oncall","prefers":{"mcp_servers":["rca_grafana","rca_elasticsearch","rca_skywalking","rca_npm"]}}}
---

# RCA Metrics Collection（agent_driven 采集）

Skill root: `{baseDir}`

> **职责**：在 `agent_driven` 模式下通过 `mcp__rca_*__*` 完成 discovery → query，为 `log-rca` 提供带 `evidence_id` 的事实。  
> **不做**：维度/层次推断、场景配置匹配、后端 `collection_plan`、Bundle 组装、RcaReport 输出。

> **暂时禁用**：`rca_baseline` / `rca_metrics` MCP（待 Grafana 取证调通后恢复；见 [discovery-workflow.md](references/discovery-workflow.md) 阶段 B/C）。

## 本 turn 怎么做

binding 已预加载 [discovery-workflow.md](references/discovery-workflow.md)（权威 SOP）与 [collection-rules.md](references/collection-rules.md)（门控/停止/禁止）。  
**直接按 discovery-workflow 执行**；全部必做阶段完成后**只回一行** `COLLECTION_DONE`。

## 与 log-rca 的分工

| Skill | 阶段 |
|-------|------|
| **rca-metrics-collection**（本 skill） | 采集 turn：MCP 取证 |
| **log-rca** | 报告 turn：因果分析 + RcaReport v1 |

## References

| 文件 | 用途 | 默认预加载 |
|------|------|-----------|
| [references/discovery-workflow.md](references/discovery-workflow.md) | discovery → query SOP（权威） | 是 |
| [references/collection-rules.md](references/collection-rules.md) | capabilities 门控 / 停止 / 禁止 | 是 |
| [references/alert-context-v1.md](references/alert-context-v1.md) | 输入契约 | 否 |
| [references/metrics-evidence.md](references/metrics-evidence.md) | 证据解读 | 否 |
| [references/tool-catalog.md](references/tool-catalog.md) | MCP 工具 API | 否 |
| [references/budget-and-stopping-rules.md](references/budget-and-stopping-rules.md) | tool 预算 | 否 |
