# RcaReport v1（输出契约指针）

> **写法权威源**：[analysis-rules.md](analysis-rules.md)（字段怎么填、证据充分性、书写禁令）。  
> 本文件只提供机器契约与样例入口，不重复写法细则。

## Schema / Golden

| 资源 | 路径 |
|------|------|
| JSON Schema | [contracts/rca/rca-report-v1.schema.json](../../../../contracts/rca/rca-report-v1.schema.json) |
| 高置信样例 | [contracts/rca/samples/db_pool_exhausted/rca-report.json](../../../../contracts/rca/samples/db_pool_exhausted/rca-report.json) |
| 低置信样例 | [contracts/rca/samples/missing_logs/rca-report.json](../../../../contracts/rca/samples/missing_logs/rca-report.json) |

## 输出硬约束（摘要）

1. **仅输出**合法 RcaReport v1 JSON；不要 Markdown、解释文字、代码围栏。
2. 必填字段以 Schema `required` 为准；平台会补 `report_id` / `job_id` / `incident_id` / `bundle_id` / `bundle_revision` / `engine` / `agent_id` / `turn_id` / `created_at`。
3. `supporting_evidence[].evidence_id`、非空的 `counter_evidence[].evidence_id`、与 `evidence_chain[].evidence_refs` **必须**存在于 bundle / `allowed_evidence_ids`；`counter_evidence` **禁止**字符串元素，无反证写 `[]`。
4. **禁止**旧版 Dify 字段：`suspected_cause`、`key_abnormal_digest`、四维块、`next_data_needed`、字符串数组版 `disposal_suggestions`；候选禁用 `title` / `description` 代替 `cause`。

其余字段形状、篇幅、置信度门控、SkyWalking/NPM 按需规则 → 一律见 [analysis-rules.md](analysis-rules.md)。
