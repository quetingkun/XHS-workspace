---
name: semantic-observability-query
description: >
  通过工作台 UModel 语义层查询指标与日志（dataset → plan → execute）。
  适用于用户询问：语义模型、指标集、日志集、UModel、按组件查 QPS/错误率/日志、
  接入了多少监控面板/可查指标、kind=baseline 曲线/基线数值探查，
  或希望按 rca.metric.* / rca.log.business_system 取数（而非 Grafana panel id）。
  当本 Skill 已预加载（/semantic-observability-query）时，基线配置/偏离仍用
  list_datasets + query_metrics(kind=baseline) 作答；禁止拒答或要求切换 Skill。
  禁止编造 PromQL 或 curl 直连存储端点。
  禁止调用 systems / metrics / baseline / es_log MCP；仅使用 mcp__umodel__*。
version: 1.3.2
metadata: {"go_agent":{"prefers":{"mcp_servers":["umodel"]},"category":"ops"}}
---

# Semantic Observability Query（对话入口 · UModel）

Skill root: `{baseDir}`

服务端完成 **resolve → plan → execute**。凭据留在工作台；Agent 只拿 `dataset` 与查询结果。

**只使用 `mcp__umodel__*`**：`catalog_summary` / `list_datasets` / `query_metrics` / `query_logs`。
禁止 `mcp__systems__*`、`mcp__metrics__*`、`mcp__baseline__*`、`mcp__es_log__*`、官方 `umodel-mcp` / `umctl`。

## 适用场景

- 全平台清点：「接入了多少监控面板 / 各系统有哪些可查指标」
- 按业务系统查语义指标集 / 应用日志 / **kind=baseline 曲线与数值**
- 用户已预加载本 Skill，并问「有哪些基线 / 基线有没有偏离」→ **仍用本 Skill 取数**，不要拒答、不要让用户换 Skill
- 用户提到 UModel、本体对象图、metric_set、log_set、组件指标

## 不适用（本 Skill 被强制时也不要改调其它 MCP）

- Grafana 按标题查瞬时值 → 仍用本 Skill 的 `catalog_summary` / `list_datasets` / `query_metrics`；不要调 `mcp__metrics__list_panels`
- ES 关键字检索 → 仍用本 Skill 的 `query_logs`（带系统过滤），不要调 `es_log`
- RCA 作业链 → `mcp__rca_*`（需要 `job_id`）
- 本机 CPU/内存 → `fetch_host_metrics`
- **禁止**改调 `mcp__baseline__*`；结构化偏离（current/baseline/deviation 字段）若结果里没有，就用曲线点如实说明「无结构化偏离字段」，并汇总已查出的当前值/趋势；**禁止**空转让用户去切 ops-baseline

## 基线相关问句（本 Skill 已预加载时）

```
1. mcp__umodel__list_datasets（system / system_id）
2. 筛选 kind=baseline 的 items，报 Name / counts.baseline
3. 对可查 dataset 调 mcp__umodel__query_metrics（近 1h 或用户时间窗）
4. 作答：列出基线条目；用 series/当前值描述是否异常或趋势；storage not found 如实说明
```

## MCP 工具（仅 umodel）

| 工具 | 何时用 |
|------|--------|
| `mcp__umodel__catalog_summary` | 全平台清点；**禁止**对每个系统 `list_datasets` |
| `mcp__umodel__list_datasets` | 已锁定/口语单系统，取 `items` 里的 dataset |
| `mcp__umodel__query_metrics` | 查 `kind=panel` 或 `baseline` |
| `mcp__umodel__query_logs` | 查 `kind=log` |

## 两套面板口径（必须分开报）

| 字段 | 含义 | 用户问法 |
|------|------|----------|
| `configured` | 数据接入页 `monitorPanels` 全量 | 「接入了多少监控面板」 |
| `panel` | 语义可查询 `kind=panel`，可跟 `query_metrics` | 「能查多少 / 可查询面板」 |
| `unqueryable` / `skipped` | 已配置但不可查，及原因 | 解释缺口；**禁止**对这些面板调 `query_metrics` |

`totals.configured` 应等于 `totals.panel + totals.unqueryable`。不要把 `baseline` / `log` 加进「监控面板」总数。

## 强制流程

### A. 全平台清点（多少面板 / 各系统可查指标）

```
1. mcp__umodel__catalog_summary
   - 不要先调 list_business_systems
   - 不要对 systems[] 再逐个 list_datasets
2. 作答
   - 开头用 presentation.headline（或 totals.configured / totals.panel）
   - 分系统表 **必须原样粘贴** presentation.table_markdown
   - 系统名必须用 presentation.rows[].system_name 原文
   - 禁止「其他系统」「其余」「Other」「等 N 个系统」；禁止把两个系统合成一行
   - 0 块也要保留原名（如「浙电安全学习平台 | 0 | 0 | —」）
   - unqueryable>0：用 skipped[].name + reason_label 说明缺口
   - 未出现在 presentation.rows 的名字不要写进表
```

### B. 单系统发现 + 查数

```
1. mcp__umodel__list_datasets
   - 已锁定系统：传 system_id（monitoring_id）
   - 仅有口语名：传 system=用户说法；服务端解析（不要调 systems.resolve）
   - policy=ask_user_if_ambiguous / empty_catalog / not_found：只澄清，禁止 query
2. 计数用返回的 configured / counts / groups / skipped，禁止手数 items
   - 从 items 原样复制 dataset
   - 指标：kind=panel 或 baseline，operation=get_metrics
   - 日志：kind=log，operation=get_logs（dataset 一般为 rca.log.business_system）
   - 多条 kind=log：必须原样复制该项的 dataSourceId，作为 query_logs.data_source_id
   - skipped 里的面板没有 dataset，不要编造 rca.metric.*
3. mcp__umodel__query_metrics 或 mcp__umodel__query_logs
   - 必填 system_id
   - query_metrics 必填 dataset
   - 多日志源时 query_logs 必填 data_source_id
   - 可选 from/to（RFC3339）；step 可省略
   - dry_run=true 只看 plan，不打上游
```

## 选择数据集

| 情况 | 行为 |
|------|------|
| 用户点名面板/组件 | 选 Name 匹配的 panel dataset；若只在 skipped 里，说明不可查原因 |
| 用户问 QPS / 基线曲线 / 基线有没有偏离 | 优先 kind=baseline，并 query_metrics；无偏离字段则报当前值与趋势，勿拒答 |
| 用户问日志/ERROR | query_logs；可带 filter；多日志源时带 data_source_id |
| 多条候选且模糊 | 列出 Name / kind / dataset 请用户确认 |
| items 为空 | 看 configured/skipped：有配置但不可查就解释原因；都没有则说明需在「数据接入」绑定面板/基线/日志，**不要编造曲线** |

## 列举面板 / 基线 / 日志时的分组

- 全平台：用 `presentation.table_markdown`；覆盖层级已写在 `coverage` 里，不要自己从 `groups` 再截前两层
- 单系统：用 `list_datasets` 的 `groups` / `counts`，以及 items 的 `groupLabel`
- **禁止**根据面板标题猜测「业务/数据库/中间件」归属
- 常见 `groupLabel`：`业务/应用层`、`网络层`、`数据库层`、`中间件/缓存层`（仅 Redis 等）、`日志`
- 用户问「接入了哪些面板」：先报 `configured`，可查询用 `counts.panel`；基线用 `counts.baseline` 单独一节

## 结果怎么读

- `mode=data`：用 `series` / `grafana` 摘要 / `logs` 作答
- Grafana 面板：看 `grafana.current` / `grafana.table`，**不要**索要 raw
- `mode=plan`（dry_run）：只说明将执行的 dialect / dataset，勿把 plan 里的 PromQL 改写后再查
- 空 series / 空 logs：说明该时间窗无数据，或 Grafana 面板暂不可查；不要笼统说「未同步语义模型」

## Do not

- 调用 `mcp__systems__list_business_systems` / `resolve_business_system` 做语义清点或消歧
- 调用 `mcp__metrics__list_panels` 代替 `catalog_summary`
- 编造 `rca.metric.*` dataset 或 PromQL
- 把 Grafana `panel_id`（数字）当成 dataset
- 对 `skipped` 面板调用 `query_metrics`
- 调用 umodel-mcp / `umctl` / 直连 Prometheus、ES、SLS
- 调用需 `job_id` 的 `rca_*` 工具
- 把本机指标说成该系统的值
- 把未查询到的系统写成「0 块面板」
- 把多个系统合并成「其他系统 / 其余 / Other」
- 改写 `presentation.rows` 里的系统名
- 把 `panel` 说成数据接入全量，或把 `configured` 说成都能查
- 最终回复 dump 整段 JSON；清点类用 `presentation.table_markdown`，其余用中文摘要 + Markdown 表格
