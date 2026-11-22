---
name: ops-alert-summary
description: >
  通过 alerts MCP 汇总 Grafana 告警中心，供运维对话使用。
  适用于用户询问：最近有什么告警、告警风暴、firing、谁在告警、告警摘要，
  或系统运行情况 / 有什么问题等需要实时告警信息的场景。
  只读；不涉及 RCA job_id。
version: 1.3.1
metadata: {"go_agent":{"prefers":{"mcp_servers":["alerts"]},"category":"ops"}}
---

# Ops Alert Summary（对话入口 · 告警）

Skill root: `{baseDir}`

## 适用场景

- 「最近有什么告警」「现在有多少 firing」「把 critical 列一下」
- 「xx系统近三小时有什么问题 / 运行情况」中的告警部分（运行概况还须配套 metrics + es_log，本 Skill 只负责告警）
- 口语即可，不必说 Grafana

## 不适用

- 深度根因 / 开 RCA / 「对 alert xxx 再分析」→ **对话入口可读已有报告**（`get_alert_rca`）；**重跑/新开 RCA 作业**仍须根因定位页手动发起；**禁止**声称已调度 `root_cause_analysis_agent`
- 只问制度里「告警处置规范」→ `search_knowledge`
- 运维上下文为 **ambiguous（多系统候选）** → 先请用户选系统，本轮不要查告警

## 推荐流程

```
1. 若目标系统已锁定：mcp__alerts__alert_summary（range + system=<正式名>）
2. 需要明细：mcp__alerts__list_alerts（同样传 system；status=firing 等；时间窗内批量列举）
3. **最新/解决/无时间窗定量列表类**（非「近1h有多少告警」）→ `mcp__alerts__get_latest_alert`：
   - 最新一条：`selector=latest`（可选 system，`limit=1`）
   - 最新 N 条（如「最新10条」）：`selector=latest`，`limit=N`（最大 50）
   - 无显式时间窗地列出 N 条（如「列出10条营销2.0的告警」）：同样使用 `selector=latest, limit=N`；禁止套用会话默认近1h
   - 最新 firing：`selector=latest_firing`
   - 最新已解决：`selector=latest_resolved`
   - 有没有已恢复：`selector=has_resolved`（返回 has_resolved / resolved_count / latest）
   - **有吗/有没有**：未解决/firing → `selector=has_firing`；已解决/恢复 → `selector=has_resolved`（**勿**把「未解决」当成 resolved）
   - 禁止用 `alert_summary`（近1h 统计）回答上述问句
4. 用户追问某条告警根因：mcp__alerts__get_alert_rca（incident_id 或 instance_id；或 fingerprint+episode_key）
   - 「其他/剩余/另外的告警的根因」：以 prompt 中“其他告警 RCA 续问”的候选 ID 为准，排除已分析 ID 后逐条调用；禁止复用上一条 alert_id，禁止 search_knowledge
   - 候选超过 3 条：先请用户指定，或确认是否查询全部，避免一次生成过长报告
5. 未指定系统且用户要「全部」：可不传 system（平台级）；回复中按系统分组
```

## 作用域（scoped）硬规则

- 运维上下文已有「目标系统」时：**必须**传 `system` 精确过滤（匹配 labels.system）
- **禁止**用 `keyword=测试营销2.0` 代替 `system`（子串会误伤「营销2.0」）
- 工具若仍返回其它系统条目，写回答前丢弃；不得计入「本系统有 N 条告警」
- range 可用 `1h` / `3h` / `6h` / `24h` 等；「近三小时」用 `3h`
- **日历日**：用户说「2026年8月25日」等，传 `from`/`to`（北京时间当日 00:00～次日 00:00 的 RFC3339），**不要**用会话默认 `range=1h` 顶替
- 「近一天」可用 `range=24h`；与「某年某月某日」不同，后者是绝对日不是滚动 24h

## 作答

- 先给数字摘要（firing / resolved），再列明细表
- **明细 Markdown 表格必须含列**：告警ID、故障ID、告警名称、级别、状态、开始时间（北京时间）、**关联服务/接口**（`related_target`）、**摘要**（`summary`）、RCA 状态（中文）
- 表后可加「摘要」小节复述 firing 条目的 `summary` 与 RCA 关联（**禁止省略**关联服务/接口与摘要列）
- items 为空 → 说明时间窗内**该系统**无告警实例，**不要编造**
- 用户要深挖某条 → **必须** `get_alert_rca`；有 `report_markdown` 时**原样贴出**（纯文本四章 + 文末摘自，勿加 `###`）；无报告时勿用知识库历史案例顶替；重跑 RCA 须到根因定位页

## Do not

- 调用 `rca_*` 且伪造 job_id
- 把 silenced/suppressed 说成正在故障（以返回 noise_state 为准）
- 把其它系统告警写进已锁定系统的运行情况
- 列表只展示告警名/RCA 状态而隐藏 episode_key、incident_id
- 有 `report_markdown` 时擅自改写成散文摘要
- 用户已给日历日仍传 `range=1h` / 沿用「近 1 小时」会话默认窗

