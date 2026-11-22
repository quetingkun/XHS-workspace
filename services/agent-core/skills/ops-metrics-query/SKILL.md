---
name: ops-metrics-query
description: >
  通过 metrics MCP 查询远程 Grafana/Prometheus 指标，供运维对话使用（不涉及 RCA job_id）。
  适用于用户对已点名的系统/服务（如 demo-pay）询问：查 CPU、内存、QPS、面板、Grafana、远程主机指标。
  禁止对远程应用使用 fetch_host_metrics。
version: 1.0.1
metadata: {"go_agent":{"prefers":{"mcp_servers":["metrics"]},"category":"ops"}}
---

# Ops Metrics Query（对话入口 · 远程指标）

Skill root: `{baseDir}`

## 适用场景

- 某个业务系统 / 微服务的 CPU、内存、流量、面板瞬时值或最近曲线
- 口语含 Grafana / Prometheus / 大盘，但**不必**出现这些词

## 不适用

- 「本机 / 当前主机」→ `fetch_host_metrics`
- RCA 作业链 → `mcp__rca_grafana__*` / `mcp__rca_metrics__*`（需 `job_id`，勿混用）

## 强制流程

```
1. mcp__metrics__list_panels
   - 必填 system 或 monitoring_id（业务系统名优先）
   - keyword 可填 CPU / 内存 等
   - 列举「有哪些面板」时不要传 layer（除非用户明确指定层级）
2. 从返回取 **panel_record_id**（完整 `smp_` + 长哈希，例如 `smp_54a1d1a45896338a`）
   - **不要**用 `panel_id`（Grafana 数字 id，如 `65`）
   - **禁止**自行拼接 `smp_` + `panel_id`（例如把 `65` 写成 `smp_65` —— 这不是合法 record id）
3. mcp__metrics__query_panel
   - 传 `panel_record_id=<list 返回的完整值>`（或 `panel_id` 字段填同一完整值）
   - 服务端按 1.0 同款路径：Text 读 content；Table/时序走 Grafana targets → /api/ds/query
   - 支持 Prometheus / Oracle SQL / ES / Infinity / JSON API 等（与 Grafana 面板源一致）
   - 禁止自行编造 PromQL；仅当用户/面板明确给出时才传 promql 覆盖
```

## 选择面板

| 情况 | 行为 |
|------|------|
| list 命中相关面板 | 优先选 **metrics_queryable=true** 的标题匹配项；**原样复制**其 `panel_record_id` 再 query_panel |
| `metrics_queryable=false` / `panel_type=logs` / 有 `skip_reason` | **禁止** query_panel（例：「错误日志详情」）；总览跳过，日志段改用 **es_log** list→search |
| list 返回 `hint` / `skipped_count` | 遵守 hint；勿把 skipped 面板当指标故障 |
| 多条候选且模糊 | 列 panel_title / dashboard_title / layer 请用户确认 |
| query 返回 current/stats | 用 evidence.summary / stats 回答；若有 `stats.preferred_ref_id` / `stats.series`，**以 preferred（如「错误率」）为准**，勿把同面板的请求总量 avg/max 当成错误率 |
| `source=grafana_text_panel` | Text 面板：用 `raw_content` / summary 中的 SQL/说明文本作答，**不是**时序指标失败 |
| `source=grafana_panel_table` | Table 面板：用 `table.summary_preview` / `table.rows` 摘要，**不要**编造 avg/max |
| 空列表 | 说明需在「数据接入」绑定 Grafana 面板，**不要编造曲线** |
| ds/query 无数值 | 说明时间窗无数据或面板非数值型，可建议换面板/时间窗 |
| 返回 `skipped` / `plugin.unavailable` | 服务端已软跳过：继续查其它面板；汇总注明「某面板因 Grafana 插件不可用已跳过」，**勿**写成业务故障 |
| 错误含「非 JSON / 空响应」 | 多为 Infinity/JSON API/表格面板异常，建议在 Grafana UI 打开该面板核对 |
| 错误含 panel_record_id 不存在 / smp_数字 | 说明误用了 Grafana `panel_id`；回到 list 复制完整 `panel_record_id` 重试 |

## 空结果

- evidence 无 current / series 为空 → 说明该时间窗无数据；可建议换面板或放宽 window_minutes
- **禁止**把本机指标说成该系统的值

## 最终回答格式

- 「运行情况 / Grafana 面板实时情况」等多面板总览：用 **Markdown 表格**（面板名 | 当前值 | 说明），**不要**用 `<structured view="table">`（易截断成半截标签）。运行概况还须配套 alerts + es_log，本 Skill 只负责指标侧。
- **禁止**输出 `{ "summary", "details": { "alerts", "metrics", "logs" } }` 这类 JSON 对象；先用 1～3 句中文摘要，再用 `### 告警` / `### 指标` / `### 日志` 分段。
- 表格建议 ≤15 行；更多则按 layer 分组或只列关键数值型面板，并注明总数。
- 总览优先数值面板；Text/Table 若已查到：按正文/表格预览展示，勿写成数据源故障。logs 勿 query_panel，改用 es_log。

## Do not

- 未 list 就猜 panel_id / 编造 `smp_…`
- 把 Grafana `panel_id`（如 `65`）改写成 `smp_65` 再 query
- 用 `fetch_host_metrics` 顶替远程系统
- 调用需 `job_id` 的 `rca_*` 工具
- 输出未闭合的 `<structured>` 标签
- 最终回复 dump JSON（含 summary/details）
- 对 `metrics_queryable=false` / `panel_type=logs`（如「错误日志详情」）强行 query_panel；日志请走 es_log
- 把插件 unavailable / 软跳过写成业务运行异常或「指标数据源全挂」
- 把 query_panel 对 logs 的软跳过（skipped / message 提示 es_log）说成指标数据源故障
