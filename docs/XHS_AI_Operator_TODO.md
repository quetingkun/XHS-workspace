# 小红书模块开发 TODO

日期：2026-11-21  
代码目录：`D:\09.person\XHS-workspace`  
启动（**默认 Docker**）：`python scripts/xhs.py pack && python scripts/xhs.py start` → http://127.0.0.1:8097 ；排错可用 `scripts/redeploy.py`（勿与 Docker 同占 8097）  
导航设计：`docs/XHS_AI_Operator_导航与信息架构.md`

代码都在这个目录，不改 `AI-workspace`。模型和 Embedding 配在本目录设置页，文件在 `data/xhs/settings/`。知识库用 `data/xhs/knowledge`。采集路线见 `docs/XHS_AI_Operator_热点采集路线.md`；P0 `hot_daily` 已开启，其余采集器默认关闭。

## 智能体（agent-core）

- [x] 本仓库 `services/agent-core`（自 AI-workspace 复制并定制，不修改 AI-workspace）
- [x] 功能 `xhs_ops`：`routing.py`、`local_engine.system_for`、`configs/agents/xhs-ops.yaml`、`agent-routing.yaml`
- [x] 知识库走 `GET /api/xhs/knowledge/retrieve`；模型读 `data/xhs/settings/llm.settings.json`
- [x] `scripts/redeploy.py` 默认同时拉起 xhs `:8097` 与 agent-core `:8081`（`--no-agent-core` 可关）
- [x] Docker：`deploy/docker-compose.yml` + `scripts/xhs.py pack|start`（对齐 `AI-workspace/scripts/aiw.py`）
- [x] **模型配置 · 智能体引擎**：`GET/PUT /api/xhs/settings/agent-engine` 代理 agent-core 路由；与 AI-workspace 一样可选 agent-core / Codex
- [ ] 创作页 / 首页 SSE 流式直连 agent-core（当前问询仍 `POST /api/xhs/turns` 聚合 JSON）

## 已实现（能力与后端）

- [x] 服务监听 `127.0.0.1:8097`，`GET /health`
- [x] 设置：账号配置、模型配置、系统设置（`/start`、`/settings`、`/system`）
- [x] 设置页保存对话模型和 Embedding。密钥只回显后四位，文件在 `data/xhs/settings/`，不进仓库
- [x] 知识库可写入已确认文档；Embedding 索引后向量检索，否则关键词
- [x] 提问先检索已确认文档，再交给本目录配置的模型；没有模型时只返回摘录和来源
- [x] 对话会保存。问热点、选题、文案、封面、发布或复盘时，回答里带对应步骤的链接
- [x] 素材池记录平台、进入方式、时间和状态。相同链接或笔记 ID 合并为一条
- [x] 失败、空结果、浏览器失败和模拟数据留在素材池，不能进入选题
- [x] 搜索、详情、评论、归档的入口在。采集器未启用时返回 `source_unavailable`，不产生笔记
- [x] 一条可用素材生成 5 个候选。报告分开写事实、知识库和判断
- [x] 适配看热度、账号匹配、本账号历史、已确认策略、差异和制作成本。定位是「待确定」时适配保持「中」
- [x] 候选可以选定、否决或改写。选定后才按模板生成 3 到 6 页草稿
- [x] 模板：知识科普、教程步骤、观点分析、经验分享。草稿含标题、摘要、标签和分页，不抄素材里的他人正文
- [x] 视觉方案和卡片分开产出。封面和各页用同一套 1080×1440 模板，并检查溢出
- [x] 提交前要勾完事实、原创、内容质量、图片、排版、标题和平台规则。确认只绑定当前版本
- [x] 改标题、正文或重新出图后，原确认失效。未配置 `XHS_MCP_URL` 时发布记为失败，并留下发布记录
- [x] 本账号指标可录入，涨粉可空。复盘对照本账号已有笔记，并标明观察或假设
- [x] 复盘、案例和周期报告先放在待确认目录。确认之后才进入检索

## 侧栏 IA 落地（对照设计稿）

设计目标：首页 → 热点 → 创作 → 工具 → 资源 → 设置。详见导航文档。

- [x] **首页**：侧栏「首页」，路由 `/`
- [x] **热点**：`/hot/today`、`/hot/news`，底层共用素材池并分视图筛选
- [x] **创作 · 一键成文**：`/create/article?step=1..6` 顶栏六步向导，嵌入选题 / 笔记 / 发布
- [x] **创作 · 一键成图**：`/create/visual`
- [x] **工具**：`/tools/extract`、`/download`、`/review`、`/metrics`
- [x] **资源**：`/library/works`、`/hits`、`/shelf`、`/ideas`
- [x] **设置**：账号 / 模型 / 系统（不变）

旧路径 `/materials`、`/topics` 等会重定向到新路由。

## 通过验证后再开

- [ ] hot-daily 真实免登录采集（PoC 进行中）。已内置 `services/xhs/scripts/hot_list_cli.py`，`collectors.yaml` 中 `hot_daily.enabled: true` 且 `command` 留空即用；需本机 Chrome/Edge + 能访问小红书。通过标准：至少 5 条带标题和可打开链接的真实笔记；失败仍不进选题，重复失败合并为一条采集记录
- [ ] dailytop 的 Playwright 免登录且重复运行稳定。付费 API 不作为通过条件，也不自动充值
- [ ] MediaCrawler 的关键词、详情或评论。登录失效或风控记失败，不设计绕过
- [ ] XHS-Downloader 把选定笔记的图片或视频归档到 `data/xhs/`。以外部进程调用，不复制源码
- [ ] 配置 `XHS_MCP_URL` 后的真实发布。一次只发当前这篇的当前版本，失败不自动重试

## 不做

- 不把代码写进 `AI-workspace` 的页面、启动脚本或 nginx
- 不注册、不调用 Agent-Reach
- 不做验证码绕过、Cookie 保活，也不把模拟数据当成热点
- 不自动发布、自动评论、自动私信
- 其他平台第一版只接受人工放入的链接、截图说明或文案
- 侧栏不照搬外部 Creator 产品菜单名；只做本产品的热点 / 创作 / 工具 / 资源语义