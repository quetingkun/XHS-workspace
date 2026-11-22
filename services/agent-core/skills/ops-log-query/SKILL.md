---
name: ops-log-query
description: >
  通过 es_log MCP 查询 Elasticsearch 应用日志，供运维对话使用。
  适用于用户询问：查日志、ERROR、超时、慢接口、HikariPool、日志分析（不必提 ES），
  或系统运行情况 / 健康 / 有什么问题等需结合告警与指标查看实时错误日志的场景。
  必须先 list_log_datasources 再 search_logs；禁止猜测 sys_* / ds_* 数据源 ID。
version: 1.0.1
metadata: {"go_agent":{"prefers":{"mcp_servers":["es_log"]},"category":"ops"}}
---

# Ops Log Query（对话入口 · ES 日志）

Skill root: `{baseDir}`

## 适用场景

- 查 ERROR / WARN、超时、连接池、接口变慢等**可观测日志**
- 「xx系统运行情况 / 健康 / 有什么问题」中的**日志部分**（与 alerts、metrics 同为运行概况必查，对齐 V1：alerts → grafana → log）
- 口语即可，不必出现「ES」「Elasticsearch」「知识库」

## 不适用

- 仅问「统一日志索引模式 / 字段含义」等**制度说明** → 走 `search_knowledge`，不是本 Skill
- RCA 作业链内的 `mcp__rca_elasticsearch__*`（需 `job_id`）→ 根因专项 Agent
- 运维上下文为 **ambiguous（多系统候选）** → 先请用户选系统，本轮不要查日志

## 运行概况（与 alerts / metrics 配套）

用户问「运行情况 / 近 N 小时有什么问题」且系统已锁定时：
1. 本 Skill **必须**走 list → search（同时间窗；可 `has_error` / levels=ERROR,WARN,FATAL）
2. 不要因「只是概况」跳过日志；无绑定或空命中如实说明
3. 最终回答在 `### 日志` 段摘要；禁止编造 ERROR 正文

## 强制流程

```
1. mcp__es_log__list_log_datasources
   - 可用 keyword 过滤业务系统名 / 绑定名
   - healthy_only 默认 true
2. 从返回取 system_bindings[].system_id 与 data_source_id
3. mcp__es_log__search_logs（必填 system_id、data_source_id、start_time、end_time RFC3339）
   - **不要**传大 limit（如 50）；服务端按「数据接入」该 ES 数据源的「抽样条数」（`rca_sample_size`，默认 3）输出，与 RCA 一致；ES 拉取上限用同页「抽样总数」（`rca_size`，默认 50）
   - 返回 `sample_size` / `fetched_count`；`### 日志` 段只摘要抽样结果，勿贴全文
```

## 业务系统 vs 服务名

- 用户说「服务11」「系统11」→ 多指数据接入里的 **system_name**（业务系统），不是 K8s 应用名
- `filters.services` 应使用 binding 的 `scope.services`（如 `order-service`）
- **禁止**把业务系统名直接塞进 services filter

## 选择绑定

| 情况 | 行为 |
|------|------|
| list 仅 1 条且与用户说法相关 | 直接用该条 ID 查询 |
| 多条候选 | 列 `system_name` / `display_name` / `scope.services` 请用户确认 |
| 无绑定 / 不健康 | 说明需先在「数据接入」配置日志源，**不要编造**日志内容 |

## 空结果与时间

- 按用户问的相对时间窗原样传 `start_time` / `end_time`（如近 3 小时、近 7 天）
- 默认最长 **24h**（`capabilities.max_window_minutes`=1440）：若跨度更大，服务端会**按 end_time 往前截断到上限并继续查询**，在 `warnings` 中说明；**不会**因超窗失败
- `items` 为空 → 说明该时间窗无命中；可建议放宽过滤或换关键词；**不得编造 ERROR 正文**
- 「昨天」「6月2日」→ 换成 RFC3339

## Do not

- 未 list 就 search（本 turn 内已 list 且绑定未变可复用 ID）
- 猜测或编造 `sys_*` / `ds_*`
- 把 list 失败说成「查过日志但没有 ERROR」
- 因担心超 24h 而自行放弃查日志（服务端会截断，仍应调用）
