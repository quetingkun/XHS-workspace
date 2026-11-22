# 采集规则（门控 / 停止 / 禁止）

> **执行细节以已预加载的 [discovery-workflow.md](discovery-workflow.md) 为准**（阶段顺序、工具入参、失败处理）。本文不重复 SOP。

> **暂时禁用**：`rca_baseline` / `rca_metrics` MCP（待 Grafana 取证调通后恢复；细节见 discovery-workflow 阶段 B/C）。

## 1. 读取顺序

1. 解析 `alert_context.alerts[0]` 的 `name`、`labels`、`annotations`
2. 从 `annotations.summary` / `description` 提取关键词，供 `search_logs` 的 `keyword` / `query`
3. 按 discovery-workflow **分 Server 串行**采集

## 2. capabilities 门控

| 能力 | 条件 | 动作 |
|------|------|------|
| Grafana | 始终 | 阶段1（见 discovery-workflow） |
| SkyWalking | `capabilities.skywalking.available == true` | 阶段2 |
| NPM | `capabilities.npm.available == true` | 阶段3 |
| 日志 | 始终（最后） | `search_logs` |
| K8s 事件 | `capabilities.k8s_event.available == true` | 另调 `cluster_errors`（与 `search_logs` 独立） |

能力由后端 `ContextBuilder` 按数据树 binding 写入；**不得**靠系统名或告警标题猜测。

## 3. 停止采集

满足**任一**即可结束（只回一行 `COLLECTION_DONE`，**不**输出 RcaReport）：

- 已按 discovery-workflow 完成各阶段必调工具，且日志阶段已执行
- 工具预算接近上限（见 [budget-and-stopping-rules.md](budget-and-stopping-rules.md)）
- 连续 2 次同类 discovery 返回空（`items: []` / `total: 0`）

## 4. 禁止

- 编造 `evidence_id`、指标值、日志原文
- 向任何 `mcp__rca_*__*` 传 `layer` 或 `alert_context`（schema 已不暴露；传了会被拒 / 剥离）
- 调用 `mcp__rca_baseline__*` / `mcp__rca_metrics__*`（当前未启用）
- 未 discovery 时猜测 `panel_id`；跨 Server 交叉取证
- 报告 turn（含 EvidenceBundle / `agent_view`、无采集指令）调用本 skill 的采集步骤
