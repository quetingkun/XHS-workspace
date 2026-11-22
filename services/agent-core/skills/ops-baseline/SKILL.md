---
name: ops-baseline
description: >
  通过 baseline MCP 查询动态基线目录及当前相对基线的偏离（不涉及 RCA job_id）。
  适用于用户询问：基线、动态基线、基线配置、偏离、比平时高、历史基线、基线模板查询。
  对话中禁止创建或训练基线；写入类操作引导至「数据接入 / 动态基线中心」。
  禁止用 metrics.list_panels 或 umodel 回答「有哪些基线配置」。
version: 1.1.1
metadata: {"go_agent":{"prefers":{"mcp_servers":["baseline"]},"category":"ops"}}
---

# Ops Baseline（对话入口 · 动态基线）

Skill root: `{baseDir}`

## 适用场景

- 「营销2.0有哪些基线配置」「demo-pay CPU 比基线高吗」「有没有配置内存基线」
- 口语含 基线 / 基线配置 / 偏离 / 比平时，**不必**说「动态基线中心」

## 不适用

- 创建/训练/启用基线模板 → 引导「数据接入 / 动态基线」页面，对话只读
- RCA 作业链 → `mcp__rca_baseline__*`（需 `job_id`）
- 实时 Grafana 曲线（不问基线）→ metrics MCP
- 语义指标集 / UModel 曲线探查 → `semantic-observability-query`（**不是**本 Skill）

## 强制流程

```
1. mcp__baseline__list_catalog（system / keyword / layer；全平台可传 {}）
2. 取 baseline_config_id
3. 偏离对比 → mcp__baseline__query_window
   或只要定时结果 → mcp__baseline__get_scheduled
```

多轮会话遵循助手通用规则：本轮新问句必须重新调 MCP，勿复用上一轮 catalog 结果。

## 作答

- 说明 metric、current、baseline、deviation（若有）
- catalog 条数对齐「数据接入 → 基线配置」启用列表，**禁止**用「面板绑定了 baseline_config_id」代替
- catalog 为空 → 引导先配置基线，勿编造偏离
- get_scheduled 无结果 → 说明尚未跑出定时基线
- 工具表中无 `mcp__baseline__*` → 如实说明未接入，**禁止**改调 `mcp__metrics__list_panels` / `mcp__umodel__*` 冒充清单

## Do not

- 猜测 baseline_config_id
- 调用需 `job_id` 的 `mcp__rca_baseline__*`
- 在对话里宣称已创建/训练基线
- 将 `*_custom`（自定义子类）作为推荐首选；目录无匹配时引导用户在管理端手动选「自定义」并自行配参
- 用 metrics / umodel 回答「有哪些基线配置 / 有没有偏离」
