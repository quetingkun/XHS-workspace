# 工具预算与停止规则

> platform-api 默认 loop：`max_tool_calls=20`，`max_duration_seconds=600`（见 `rca.agent_loop` 配置）。

> **当前阶段**：Baseline / Metrics MCP 已关闭，预算以 Grafana + 日志 + 系统补证为主。

## 预算分配建议

| 阶段 | 建议调用次数 |
|------|--------------|
| skill_view（历史；现已由 binding preload） | 0 |
| Grafana（list_panels + query_panel 全量） | 2~8 |
| skywalking / npm（满足触发条件时必调） | 1~3 |
| logs（cluster + search，必调，最后执行） | 1~3 |
| **合计** | ≤ 15（留余量给 repair） |

## 必须停止采集并输出报告

1. 已收集 ≥2 个不同 `evidence_id`（含 Grafana 或日志），且日志阶段已执行
2. `max_tool_calls` 接近上限（剩余 ≤3）
3. 同一工具连续失败 2 次
4. 已执行完整 SOP 但某路径无数据 → 写入 `missing_evidence` 后仍输出 JSON

## 禁止浪费预算

- 不要对 501 占位工具 retry
- 不要重复相同参数的 query（结果应一致）
- 不要传 `layer` / `alert_context`（schema 已不暴露）
- **不要跨 MCP Server 交叉取证**（例如 `list_panels` 后先调 `slow_traces` 或 `cluster_errors`）
- **不要**调用 `mcp__rca_baseline__*` / `mcp__rca_metrics__*`（当前未启用）
- 报告 turn（无采集指令）零 tool call

## 采集完成检查清单

输出 `RcaReport` 前确认：

- [ ] 所有引用的 `evidence_id` 来自工具返回值
- [ ] `job_id` 与 `alert_context` 一致
- [ ] **阶段1** Grafana 已完成：`list_panels` + 全量 `query_panel`（`items` 非空时）
- [ ] **阶段2** `capabilities.skywalking.available=true` 时已按序完成 SkyWalking
- [ ] **阶段3** `capabilities.npm.available=true` 时已调 NPM
- [ ] **阶段4** 已调 `search_logs`；`capabilities.k8s_event.available=true` 时已调 `cluster_errors`
- [ ] 工具调用顺序符合 Server 串行规则（无交叉）
- [ ] 无编造数值/日志/主机名
