---
name: historical-case
description: >
  通过知识库检索相似历史运维案例（search_knowledge 或 mcp__knowledge__search），无独立案例 MCP。
  适用于用户询问：有没有类似案例、历史案例、同类故障、以前怎么处理、复盘案例。
  优先选用案例/经验类文档；须标注来源；禁止编造 case_id。
version: 1.0.0
metadata: {"agent":{"prefers":{"tools":["search_knowledge","mcp__knowledge__search"]},"category":"ops"}}
---

# Historical Case（对话入口 · 案例走知识库）

Skill root: `{baseDir}`

## 产品定位

2.0 **不单独建案例 MCP**。历史案例 / 经典经验 / 故障复盘作为**知识库内容**（可单独建「故障案例」知识库或标签），统一检索与引用。

- 本地引擎和 Codex 都由 agent-core 在生成前检索知识库，摘录附在提示词里

与 1.0 `historical_case` 向量库的差异：结构化 case_id / 根因类别召回暂无；待 RCA 案例沉淀后再评估薄 MCP。

## 适用场景

- 「有没有类似案例」「以前 CPU 高怎么处置」「同类故障复盘」

## 流程

```
1. 检索知识库（query 保留系统名、现象、对象）
2. 有命中 → 摘录要点并 [n] 引用
3. 无命中 → 说明知识库未覆盖；可建议补充复盘文档或查实时指标/日志
```

## Do not

- 编造 case_id / 根因类别
- 用本机指标、告警 MCP 或未调用检索的内容冒充「查过案例」
- 与实时巡检混淆：用户明确要实时 CPU/告警时走 metrics/alerts，不是本 Skill
