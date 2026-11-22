---
name: log-rca
description: >-
  告警 RCA 报告回合：只读 EvidenceBundle / agent_view，仅输出 RcaReport v1 JSON（不调用工具）。
  适用于：根因分析、根因定位、告警分析、故障分析、RcaReport、EvidenceBundle、
  agent_view、incident investigation，以及采集完成后的值班根因研判。
triggers: [根因分析, 根因定位, 告警分析, 故障分析, 智能根因, root cause, alert rca, incident investigation, evidence bundle, rca report, rcareport, agent_view, on-call]
version: 2.1.0
metadata: {"go_agent":{"category":"oncall"}}
---

# Log Root Cause Analysis（告警 RCA 报告）

Skill root: `{baseDir}`

> **报告 turn 专用**：基于已就绪的 EvidenceBundle / `agent_view` 输出 RcaReport v1。  
> 采集由 `rca-metrics-collection` 负责。本 skill **不声明** MCP prefers（分析 turn `MCPDeny`，禁止调用工具）。

## Quick start

1. **只读证据**：使用 prompt 中的 `agent_view` / EvidenceBundle / `allowed_evidence_ids`；禁止工具调用。
2. **按规则填报**：遵循已预加载的 [analysis-rules.md](references/analysis-rules.md)（证据充分性、字段写法、书写禁令）。
3. **仅输出 JSON**：形状见 [rca-report-v1.md](references/rca-report-v1.md) 与 Schema；不要 Markdown、代码围栏或解释文字。

## References

| 文件 | 用途 | 默认预加载 |
|------|------|-----------|
| `references/analysis-rules.md` | **写法权威源**（充分性门控、字段、SW/NPM 按需） | 是（报告 turn） |
| `references/rca-report-v1.md` | 输出契约指针 + Schema / golden | 是（报告 turn） |
| `references/evidence-bundle-v1.md` | 输入契约说明（prompt 已含 agent_view 时不必再读） | 否 |

## 缺证时

- 上一 turn 采集失败或证据不足：按 analysis-rules「证据充分性」写入 `missing_evidence` 并调整 `confidence`。
- **禁止**编造未出现在输入中的数值、主机名、SQL、URL、`trace_id`、日志原文。
