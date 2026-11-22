# RCA 分析规则（RcaReport v1）

> **本文件是报告 turn 写法唯一权威源。** 输出契约 / Schema / golden 见 [rca-report-v1.md](rca-report-v1.md)。  
> **禁止**输出旧版 Dify 字段：`suspected_cause`、`key_abnormal_digest`、四维块、字符串数组版 `disposal_suggestions`。

## 目录

1. [适用场景](#适用场景)
2. [证据充分性（置信度门控）](#证据充分性置信度门控)
3. [总原则](#总原则)
4. [字段写法](#字段写法v1)
5. [篇幅与数值](#篇幅与数值)
6. [书写禁令](#书写禁令必须遵守)
7. [Pod 副本数类告警](#pod-副本数类告警)
8. [SkyWalking / NPM（按需）](#skywalking--npm按需)

## 适用场景

用于 **analysis / report / repair / regen** turn（证据已就绪）。采集由 `rca-metrics-collection` 在上一 turn 完成。

| 输入 | 事实来源 | evidence_id |
|------|----------|-------------|
| 报告 / repair / regen | `agent_view` 或完整 EvidenceBundle | 仅引用 bundle / `allowed_evidence_ids`；**禁止调用工具** |

角色：基于输入证据输出**仅含事实与可追溯引用**的 RcaReport v1 JSON。

## 证据充分性（置信度门控）

### `evidence_id` 前缀

| 前缀 | 含义 | 可否引用 |
|------|------|----------|
| `metric_*` | 指标 | 是 |
| `log_cluster_*` | 日志聚类 | 是 |
| `log_hit_*` | `search_logs` 单条命中 | 是 |
| `trace_*` | SkyWalking | 是（须有效，见下） |
| `npm_*` / `npm_url_*` | NPM URL | 是（须有效） |
| `ai_*` / `alert_*` | 告警对象 | 可用于 `evidence_chain` 链首 |

### 有效证据 vs 缺失表述

| 情况 | 正确处理 |
|------|----------|
| `evidence_quality.failed_collectors` 非空 | 写入 `missing_evidence`，降低相关 `confidence` |
| 采集 `status=ok` 但 logs hits/clusters 为空 | **不是**采集失败；写「窗口内无匹配日志」或列入 `verification.unverified`；**禁止**写「日志采集失败」 |
| ≥2 条相互印证的异常 metrics（含量化值）且机制自洽 | 即使无高价值日志，报告 `confidence` 仍可 ≥0.7；`missing_evidence` 可注明缺堆栈/明细 |
| 仅有告警标题，无异常 metrics / 有效 logs / traces | `confidence < 0.4`；`final_result` 只写排查方向 |
| 某类证据无异常 | 不必凑候选；可在 `verification.verified` 写一句「该类未显示异常」 |

不得把 `failed_collectors` 解释为「该层无异常」。

## 总原则

1. 结论**必须紧密贴合**输入；**禁止**编造未出现的数值、主机名、SQL、日志、URL、`trace_id`。
2. **仅输出**合法 RcaReport v1 JSON；不要 Markdown、解释文字或代码围栏。
3. 填入：`root_cause_candidates[]`（最多 3，`rank` 从 1 连续）、报告级 `evidence_chain` / `timeline` / `verification`、根级 `disposal_suggestions` / `missing_evidence` / `next_steps`。
4. **禁止**在单个候选内写 `evidence_chain` 或 `verification`；候选证据一律放 `supporting_evidence`。
5. 候选用 `rank` / `cause` / `category` / `confidence` / `supporting_evidence`；**禁止**用 `title` / `description` 代替 `cause`。
6. 报告级 `confidence < 0.4` 时，`final_result` 只能写排查方向，不能写成确定根因。

## 字段写法（v1）

### `summary` / `final_result`

- 各 **≤ 2 句**，完整成句，以 `。`（或 `！` `？`）结尾。
- `summary`：告警对象 + 主要异常现象（量化优先）。
- `final_result`：最可信结论，或明确的「证据不足、下一步排查方向」。

### `root_cause_candidates[]`

- 最多 3 条；`category`：`application` | `database` | `network` | `infrastructure` | `change` | `dependency` | `capacity` | `unknown`。
- `cause`：**1～3 句**（建议 50～200 字），写清机制与对象；勿缩成标题。
- `supporting_evidence[].summary`：一句写清指标名、当前值、基线/阈值、偏离、时间对齐；`evidence_id` 必须存在。
- `counter_evidence`：**削弱/否定本候选根因**的已有证据；元素与 `supporting_evidence` 同形 `{evidence_id, source, summary}`，`evidence_id` 必须来自 `allowed_evidence_ids`。
  - 适用：bundle 中有证据表明「错误不在该层 / 该假设不成立」（例如主因是应用 HTTP 404 时，用 DB CPU 正常、异常等待=0 作反证；怀疑库因时，用 HTTP 404、无 SQL 的 trace 作反证）。
  - **严禁**编造 id、数值，或把「未采集到 / 日志中未出现…」写成字符串或无 id 对象冒充反证。
  - **无可用反证时写 `[]`**，不要为满足格式而捏造；缺证写入本候选或根级 `missing_evidence`，或 `verification.blocked_by_missing_evidence`。
- 候选内 `missing_evidence` / `verification_steps` / `recommended_actions` 按需；无则空数组。

### `evidence_chain`（报告级）

- 每项 `{step, summary, evidence_refs}`；`step` 从 1 递增。
- `summary` 一句：「时间 → 异常对象 → 指标/日志要点」；**禁止**粘贴原文。
- 有告警时间写链首（可引用 `ai_*` / `alert_*`）；有量化对比写入对应步骤。
- 有效 SW / SQL / NPM 时按 [SkyWalking / NPM](#skywalking--npm按需) 写入要点。

### `timeline`（报告级，可空）

- `{time, title, type}`（`time` RFC3339；`type`：`alert` | `metric` | `log` | `trace` | `change` | `spread` | `root`）；可选 `evidence_id`。
- **禁止**旧字段名 `timestamp` / `event`。

### `verification`（报告级）

- `{verified, unverified, blocked_by_missing_evidence}` 均为字符串数组。
- 真·采集失败、缺 Trace/变更等写入 `blocked_by_missing_evidence`，并与根级 `missing_evidence` 呼应。

### `disposal_suggestions`（根级对象数组）

- **最多 2 条**；含 `action`、`risk_level`（`L0`|`L1`|`L2`|`L3`）、`requires_approval`。
- `action` 完整成句并以 `。` 结尾；**首条**须对应 `root_cause_candidates[0].cause`（含可检索对象）；禁止首条仅为「排查某某日志」。
- L2 / L3 必须 `requires_approval=true`；L3 必须含 `rollback_plan`、`expected_observation`。
- **禁止**在候选内写处置冒充根级（候选仅可用 `recommended_actions` 短提示）。

### `missing_evidence` / `next_steps`

- 缺证、失败采集 → `missing_evidence`；可执行补采/核对 → `next_steps`。

## 篇幅与数值

1. 有数据时，`cause` 与关键 `supporting_evidence[].summary` / `evidence_chain[].summary` 须含可验证数值；禁止整段仅「正常」。
2. 百分比、比率、小数 **≤2 位有效小数**；计数用整数。
3. **严重度启发式**（非 Schema）：容器 CPU &lt;75%、内存 &lt;85% 不宜作首要根因；偏离越大、持续越久、错误相对历史越高，措辞越重。

## 书写禁令（必须遵守）

适用于：`summary`、`final_result`、`cause`、各类 `summary`/`title`/`action`、`verification` 元素、`next_steps`。

1. **严禁**「…」、`...`、`..`、`⋯` 与半截句。
2. 叙述字段每句须完整；`disposal_suggestions[].action` 必须以 `。` 结尾。
3. 输出前自检：仍含省略号或关键句末无句号 → **重写**后再输出。

## Pod 副本数类告警

- 写清 workload、实际/期望副本、偏离 %。
- **禁止**堆砌 CPU/内存/线程「无数据」；CPU&lt;75% 或常规内存**不作为**根因写入 `cause`。

## 优先写入的可验证片段

堆栈行（含 `at`）、SQL 要点、K8s Events（CrashLoopBackOff / ImagePullBackOff / OOMKilled）、指标数值——写入 `supporting_evidence[].summary` 或 `evidence_chain[].summary`，并带 `evidence_id`。

## SkyWalking / NPM（按需）

**仅当** bundle / `agent_view` 已有对应有效证据时应用；无证据则遵守缺失禁令，勿臆造。

### 有效证据判定

| 类型 | 视为有效 | 典型 ID |
|------|----------|---------|
| 慢链路 | 非空 traces / `trace_id`，非单纯 `skipped`/`error` | `trace_*` |
| DB SQL | 非空 `sql_text` / `sql` / `sql_statements` | 同上或关联 SQL |
| NPM URL | `ok=true` 且有 summary / 分榜 / totals；或 `npm_*` 命中 | `npm_*` |

### SkyWalking（有有效证据时）

1. 使用证据字段：`trace_id`、`duration_ms`、`request_paths`、`analysis.slow_steps`、`analysis.sql_statements`、`overall_root_cause_hints`。
2. `evidence_chain` / `supporting_evidence`：写清最慢 trace、慢 Span/接口、是否伴随慢 SQL；数值与 `trace_id` 一致。
3. traces 含 SQL → `category=database` 或摘要中摘录 SQL 与耗时（勿臆造）。
4. 首条 `cause`：吸纳 hints + 最慢 Span，并与指标/日志交叉。
5. **禁止**把 SkyWalking 当成 ES 日志复述。

### NPM（有有效证据时）

证据常含：`workload`、`time_window`、`totals`、合并榜与方向分榜、`connect_fail_requests`。

1. `evidence_chain`：收/发量与错误、慢请求；**优先方向分榜**（URL、错误率/慢率）；有建联失败写对象。
2. 首条 `cause`：**接收**异常偏自身接口，**发出**偏下游；与指标/日志交叉，禁止只抄告警标题。
3. `skipped`/`error`/`ok=false` → `missing_evidence` 一句说明；**禁止**编造 URL。

### 交叉与缺失禁令

- 错误率 + SW：须写明被调方返回业务错误或 HTTP 5xx（trace 标记错误）的机制，勿只写调用关系。
- **无**有效 SW 证据 → **禁止**出现 SkyWalking、慢链路、`trace_id`。
- **无**有效 NPM 证据 → **禁止**出现 NPM、eBPF 业务 URL。
