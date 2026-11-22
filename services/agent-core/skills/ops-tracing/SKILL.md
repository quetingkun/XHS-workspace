---
name: ops-tracing
description: >
  通过 skywalking MCP 查询 SkyWalking 慢链路与链路详情，供运维对话使用（不涉及 RCA job_id）。
  适用于用户询问：慢请求、慢链路、调用链、trace、TraceID、接口变慢、哪个下游拖慢。
version: 1.0.1
metadata: {"go_agent":{"prefers":{"mcp_servers":["skywalking"]},"category":"ops"}}
---

# Ops Tracing（对话入口 · SkyWalking）

Skill root: `{baseDir}`

## 适用场景

- 「某服务最近慢请求 / 慢链路」「看一下调用链」
- 口语含 Trace / TraceID / endpoint 变慢，**不必**说 SkyWalking

## 不适用

- 仅问 CPU/内存曲线 → metrics MCP
- 日志 ERROR 正文 → es_log
- RCA 作业链内证据字段 → 根因专项（可复用同类 JSON，但勿挂 `job_id` 工具）

## 强制流程

```
1. mcp__skywalking__list_trace_datasources（keyword/system 过滤）
2. 取 data_source_id
3. mcp__skywalking__list_slow_traces（service / window_minutes / min_duration_ms）
4. 需要明细时 mcp__skywalking__get_trace(trace_id)
```

## 作答

- 先列最慢的 3～5 条：duration_ms、endpoint、is_error
- get_trace 后总结 `slow_steps`（下游 peer / SQL tag 如有）
- 无绑定 / 空 traces → 引导数据接入 SkyWalking，**不编造**链路

## Do not

- 猜测 data_source_id / trace_id
- 用本机指标或编造 span
