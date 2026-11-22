# XHS AI Operator：小红书 AI 运营系统技术方案

> 版本：v0.5\
> 日期：2026-11-21\
> 状态：方案设计稿\
> 目标：在现有 AI-workspace 上增加小红书运营模块，而不是另起一套运行时。\
> 代码依据：`D:\09.person\AI-workspace`（架构见该仓库 `docs/architecture.md`）。\
> 变更：运行时改为复用 agent-core、knowledge、agent 兼容层和 React 工作台。采集、审批和八步状态放到新增的 `services/xhs`。

------------------------------------------------------------------------

## 1. 项目目标与建设原则

### 1.1 项目目标

建设一套面向个人运营的小红书 AI
辅助系统。主流程是八步：热点与素材发现、热点分析与账号适配、选题决策与内容策划、图文内容生产、视觉设计与卡片生成、人工审核与发布、数据跟踪与效果复盘、知识沉淀与策略优化。复盘结论经人工确认后，回到下一轮热点分析和选题。

系统增加独立的机器人助手和本地运营知识库，使用户既可以通过自然语言与系统交互，也可以持续沉淀账号资料、运营方法、爆款案例、内容资产和运营数据。

### 1.2 已确定的产品选择

  项目               当前选择
  ------------------ --------------------------------------------------
  账号方向           暂未确定，后续通过选题实验逐步明确
  运营方式           个人运营，AI 辅助，人工审核后发布
  宿主工程           `D:\09.person\AI-workspace`
  对话运行时         `services/agent-core`（Python，:8081）
  对话引擎           本地模型 `agent-core`，或官方 Codex 二进制 `codex`
  知识库             `services/knowledge`（:8092），SQLite + Qdrant
  交互入口           现有 React 工作台 `apps/web`（:5173）
  发布策略           必须人工明确确认，不允许自动发布

### 1.3 建设原则

1.  **沿用现有工作台**：对话、检索、设置和页面壳都在 AI-workspace 里。小红书业务状态不塞进问询助手的提示词。
2.  **页面是主入口**：用户在 React 工作台操作。Codex 是 agent-core 可选引擎，不是单独的客户端。
3.  **知识原件仍是 Markdown**：确认后的运营知识进入 knowledge 服务。素材池、选题、审批和指标放在 `services/xhs` 的 SQLite。
4.  **不另起运行时**：不新建 Go 服务，不把检索退回一套新的 FTS5。知识检索用现有分块、关键词和 Qdrant。
5.  **AI 辅助，人工把关**：选题、文案和图片由 AI
    辅助生成；发布前必须人工审核和确认。
6.  **工具可替换**：LLM、采集工具、图片生成工具和发布工具通过接口或适配层接入，避免业务逻辑绑定单一产品。
7.  **采集先验证再接入**：小红书采集尽量免费，不把长期维护 Cookie
    当作前提，输出结构化数据，并接入 Go
    Agent。先验证免登录热点，再验证深度采集。浏览器失败或模拟数据返回
    `failed`，不进入选题。

------------------------------------------------------------------------

## 2. 产品功能架构

系统以第 7 节的八步运营流程为业务主线。页面在 `apps/web`。对话走 `services/agent-core` 的 `POST /v1/agent-turns`。素材、选题、草稿版本和审批由新增的 `services/xhs` 保存。

### 2.1 机器人助手

作为系统的自然语言交互入口，支持：

-   按八步流程发起或继续任务：发现素材、分析适配、确定选题、生产文案、生成卡片、提交审核、记录数据和沉淀知识。
-   运营知识问答：账号定位、内容策略、标题、封面和发布建议。
-   知识管理：检索、提交资料入库、查询知识来源。

机器人回答时，应区分：知识库已有资料和结论；本次实时采集或工具调用结果；模型基于资料给出的分析或假设。采集失败和模拟数据不能被说成真实热点。

### 2.2 八步流程与产物

  步骤   名称                     主要产物
  ------ ------------------------ ------------------------------------------
  1      热点与素材发现           统一素材池
  2      热点分析与账号适配       热点分析报告、账号适配度、候选选题
  3      选题决策与内容策划       选题方案、内容脚本
  4      图文内容生产             完整笔记文案、图文页面内容
  5      视觉设计与卡片生成       封面图、正文配图、完整图文预览
  6      人工审核与发布           已发布笔记、发布记录
  7      数据跟踪与效果复盘       笔记分析报告、运营周期报告、优化建议
  8      知识沉淀与策略优化       持续更新的运营知识库

第 5 步是独立环节，专门处理封面和排版。第 6 步的发布必须经过人工确认。第 8 步的策略更新必须经过人工确认，然后供第 2 步和第 3 步使用。

------------------------------------------------------------------------

## 3. 总体技术架构

小红书模块挂在已经运行的 AI-workspace 上。仓库路径是 `D:\09.person\AI-workspace`。后端是一组本机 Python HTTP 服务，前端是 React。数据在各服务自己的 SQLite 里；知识向量在 Qdrant。没有 Go 代码，本文不再新建 Go Agent。

### 3.1 现有服务

启动入口是 `python scripts/aiw.py start`。Web 容器内的 nginx 把路径转到对应服务。

``` text
apps/web  React :5173
  ├─ /api/knowledge/*      → knowledge    :8092
  ├─ /api/agent/*          → agent        :8093
  ├─ /v1/agent-turns 等    → agent-core   :8081
  ├─ /api/mail-digest/*    → mail-digest  :8095
  ├─ /api/video-download/* → video-download :8096
  └─ /api/xhs/*            → xhs          :8097   （新增）

knowledge → Qdrant :6333、可选 MinerU :8000、可选 LightRAG :9621
agent     → agent-core、knowledge
agent-core → 本地模型或官方 Codex 二进制，以及 knowledge
xhs       → 采集器进程、knowledge、发布用的小红书 MCP
```

| 服务 | 现状 | 小红书怎么用 |
| --- | --- | --- |
| `apps/web` | React、Vite。内容中心在 `/content`，视频下载在 `/content/downloads`。专题模块的写法见 `apps/web/src/a-share` | 新增 `apps/web/src/xhs`，路由放在 `/content/xhs` |
| `services/agent-core` | `POST /v1/agent-turns` 返回 SSE。功能目前有 `general_qa`、`brainstorm`。引擎是本地 `agent-core` 或官方 `codex` 二进制。`SKILL.md` 按提示词热加载 | 新增功能 `xhs_ops` 和对应 agent 配置、运营技能 |
| `services/knowledge` | 库 `kb_default`（Wiki）、`kb_materials`（素材）。检索 `POST /api/knowledge/retrieve`，支持关键词。模型配置在 `llm.settings.json` | 确认后的运营知识进新库 `kb_xhs`，原始摘录可进 `kb_materials` |
| `services/agent` | 兼容层。`content_drafts` 只有标题、正文、状态、渠道、标签 | 不承载八步状态。小红书草稿版本放在 `services/xhs` |
| `services/video-download` | 独立工具服务，yt-dlp，文件在 `data/videos/downloads/` | 作为「工具服务」的样例。小红书采集不复用它 |

模型不在小红书模块里再配一套。agent-core 继续使用 knowledge 注入的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`。页面上的模型设置仍是 `/settings`。

### 3.2 新增的 xhs 服务

`services/xhs` 是本机 Python 服务，建议端口 `8097`。它只做小红书业务：

-   素材池、选题、内容脚本、图文页面数据和审批。
-   调用采集器，把结果写成第 11 节的统一 JSON。
-   保存封面和配图的相对路径。路径落在 `data/xhs/`。
-   人工确认后调用本机小红书 MCP 发布。
-   记录笔记指标和复盘任务。

agent-core 在 `xhs_ops` 这一轮开始前读取 xhs 服务的任务上下文，生成后再把草稿写回去。页面直接调 `/api/xhs/*`，不把八步状态只留在对话里。

nginx 增加 `location /api/xhs`，反代方式和 `/api/video-download` 相同。`deploy/docker-compose.yml` 与 `scripts/aiw.py` 增加这个服务的构建和启动。

### 3.3 职责划分

| 层次 | 落点 | 职责 |
| --- | --- | --- |
| 页面 | `apps/web/src/xhs` | 八步操作、预览、确认和失败状态 |
| 对话 | `services/agent-core` | 按功能 `xhs_ops` 调用模型，附上技能和知识摘录 |
| 知识 | `services/knowledge` | 已确认文档的保存、分块和检索 |
| 业务 | `services/xhs` | 素材池、流程状态、版本、审批、指标 |
| 采集 | 外部项目 + xhs 适配器 | 热点、搜索、评论和素材文件 |
| 发布 | 本机小红书 MCP | 只在当前版本已确认时执行 |

原则：

-   页面和对话都调用同一套 xhs API。
-   采集失败和模拟数据停在素材池，不进入分析。
-   `content_drafts` 继续给定通用草稿用。小红书笔记用 xhs 自己的版本表。
-   不把 Agent-Reach 接到这条链路。

------------------------------------------------------------------------

## 4. 对话、技能与业务模块

### 4.1 沿用 agent-core

一轮运营对话使用现有接口：

``` http
POST /v1/agent-turns
```

请求里带非空 `prompt`，并指定功能 `xhs_ops`。响应是 SSE，事件沿用现有类型：`tool.call.started`、`tool.call.completed`、`model.output.delta`、`turn.completed`。失败时是 `error` 和 `turn.failed`。

引擎路由仍是 `GET/PUT /v1/engine/routing`。取值只有 `agent-core` 和 `codex`。Codex 二进制不可用时，除了请求明确指定 `codex`，都会改走本地模型。

知识摘录沿用现有机制：上下文带上 `knowledge_base_ids`，其中包含 `kb_xhs`。agent-core 调用 `POST /api/knowledge/retrieve`，摘录附在提示词后面。事件名仍是 `mcp__knowledge__search`。

需要增加的配置：

-   `services/agent-core/configs/agent-routing.yaml` 增加 `xhs_ops`。
-   `services/agent-core/configs/agents/xhs-ops.yaml` 写系统提示词。提示词要求区分知识库、本次采集结果和模型判断，并禁止把失败采集说成热点。
-   `core_svc/routing.py` 的功能列表，以及 `core_svc/local_engine.py` 的 `system_for`，目前只处理 `general_qa` 和 `brainstorm`。`xhs_ops` 要加进这两处。

本地模型提示词禁止 shell。采集、归档和发布由 xhs 服务执行，不让模型直接跑外部爬虫命令。

### 4.2 技能

技能是 `SKILL.md`。agent-core 的 `core_svc/skills.py` 在每轮对话前按修改时间热加载，命中的说明附在提示词后面，单次最多 3 段。

运营技能放在：

``` text
services/agent-core/skills/
├── xhs-research/
├── xhs-analysis/
├── xhs-content/
├── xhs-design/
└── xhs-review/
```

技能只描述选题、拆解、文案和审核方法。采集命令、Cookie 和发布动作不写进技能。

### 4.3 xhs 服务模块

| 模块 | 职责 | 优先级 |
| --- | --- | --- |
| Material Pool | 统一素材池、去重、失败状态 | P0 |
| Collector | 按第 11 节调用外部采集器并归一化 | P0 |
| Workflow | 八步任务、当前步骤和产物 | P0 |
| Draft | 选题方案、脚本、3～6 页结构化内容 | P0 |
| Approval | 绑定笔记版本的人工确认 | P0 |
| Metrics | 本账号指标和复盘记录 | P1 |
| Publisher | 确认后调用小红书 MCP | P1 |

`services/agent` 的灵感库、书架和 Wiki 写回保持原样。确认后的复盘由 xhs 服务写成 Markdown，再交给 knowledge 导入 `kb_xhs`。

------------------------------------------------------------------------

## 5. 页面与对话怎么接

### 5.1 页面

小红书页面参照 `apps/web/src/a-share`：独立目录、自己的类型和 API 封装，在 `apps/web/src/App.tsx` 注册路由。

| 路径 | 页面 |
| --- | --- |
| `/content/xhs` | 八步入口和当前任务 |
| `/content/xhs/materials` | 素材池，含失败状态 |
| `/content/xhs/topics` | 适配分析和候选选题 |
| `/content/xhs/notes/:id` | 脚本、页面内容和图文预览 |
| `/content/xhs/publish` | 审核、确认和发布记录 |
| `/content/xhs/reviews` | 指标和复盘 |

侧栏放在现有「内容中心」下，不新开一套工作台。问询助手 `/assistant/daily` 继续负责通用问答。运营任务从内容中心进入；需要对话时，页面把当前步骤和任务 id 放进 `xhs_ops` 的 prompt。

### 5.2 对话请求

用户在页面里说：「结合知识库分析最近的热点，推荐 5 个选题。」

页面调用：

``` json
{
  "function_id": "xhs_ops",
  "prompt": "结合知识库分析最近的热点，推荐5个选题",
  "context": {
    "knowledge_base_ids": ["kb_xhs"]
  }
}
```

这是 `core_svc/api.py` 现在的请求形状：`prompt` 必填，`function_id` 默认 `general_qa`，知识库 id 放在 `context.knowledge_base_ids`。`system_for` 和 `routing.py` 里的功能列表目前只区分 `general_qa` 与 `brainstorm`，增加 `xhs_ops` 时这两处一起改。

xhs 服务负责列出真实素材。agent-core 只根据这些素材和知识摘录生成分析。采集器不暴露成五个独立的页面按钮以外的隐藏入口；页面上的「采集」调用 `POST /api/xhs/collect`。

------------------------------------------------------------------------

## 6. 本地知识库设计

### 6.1 存储原则

知识库用现有 `services/knowledge`，不另建一套索引。

-   Markdown 仍是确认后知识的原件。导入 `kb_xhs` 后，由 knowledge 分块并写入它自己的 SQLite。
-   关键词检索用现成的 `searchMode=keyword`。向量用现成的 Qdrant，集合名形如 `kg_chunks_{维度}_cosine`。
-   素材池、八步状态、审批和指标放在 `services/xhs` 的 SQLite，文件在 `data/xhs/`。
-   图片只存相对路径。
-   精确统计走 xhs 服务的表。例如「收藏最高的 10 篇」查指标表，不靠向量相似度。

### 6.2 知识分类

  分类             主要内容
  ---------------- ------------------------------------------------
  账号知识库       账号定位、人设、目标用户、内容方向、语言风格
  爆款案例库       笔记链接、标题、正文、封面、互动数据和拆解结论
  运营方法库       选题、标题、封面、图文结构和发布经验
  内容资产库       历史笔记、草稿、模板、图片和已发布内容
  运营数据知识库   笔记指标、用户反馈、阶段复盘和策略假设

账号方向暂未确定，因此账号定位放在 `services/xhs` 的配置里，不写死在技能或提示词中。

### 6.3 知识目录

目录是导入 `kb_xhs` 的 Markdown 结构，建议放在 `data/xhs/knowledge/`，用现有 `scripts/aiw.py import-data` 的方式增加这个库的导入，而不是再写一个导入器。

``` text
data/xhs/knowledge/
├── account/
│   ├── profile.md
│   ├── persona.md
│   ├── audience.md
│   └── content-positioning.md
├── operation/
│   ├── topic-selection.md
│   ├── viral-analysis.md
│   ├── title-writing.md
│   ├── cover-design.md
│   └── publishing-guide.md
├── viral-cases/
│   └── 2026/
├── competitors/
├── content/
│   ├── published/
│   ├── drafts/
│   └── templates/
├── analytics/
│   ├── weekly-review/
│   └── monthly-review/
└── inbox/
    ├── pending/
    └── processed/
```

### 6.4 Markdown 文档规范

每篇知识文档使用统一元数据格式：

``` markdown
---
id: viral-001
type: viral_case
title: AI Agent 自动化工作流
source_url: https://example.com
created_at: 2026-11-21
tags:
  - AI Agent
  - 自动化
  - 技术教程
status: approved
---

# 案例分析

## 原始内容

...

## 爆款结构

...

## 值得借鉴的经验

...

## 适用场景

...

## 数据来源

...
```

建议至少定义以下字段： - `id`：全局唯一 ID； - `type`：知识类型； -
`title`：标题； - `source_url`：来源链接，可为空； -
`created_at`：创建日期； - `tags`：标签； -
`status`：`pending`、`approved`、`rejected` 或 `archived`。

### 6.5 SQLite 表设计

文档和分块已经在 knowledge 服务里。对话过程在 agent-core。`services/agent` 的 `content_drafts` 只有标题、正文、状态、渠道和标签，不保存页面结构和版本，小红书不用这张表装八步产物。

`services/xhs` 新增这些表：

  表名                用途
  ------------------- ------------------------------------------
  `materials`         统一素材池：采集结果、人工输入和其他平台灵感
  `collect_runs`      一次采集的来源、查询、状态和原始 JSON
  `collected_items`   归一化后的笔记、互动数据和素材相对路径
  `topics`            选题方案和内容脚本
  `notes`             笔记草稿、3～6 页结构化内容和版本
  `note_metrics`      本账号运营指标
  `workflow_runs`     八步任务的当前步骤和产物
  `approvals`         绑定笔记版本的人工确认

设计注意事项： - 数据库记录 Markdown
文件的相对路径，不将文件绝对路径写死。 -
对核心表增加创建时间和更新时间。 -
对任务、审批和发布记录保留状态变化及错误信息。 - SQLite
使用事务保证状态更新一致性。 - 对文档 ID、笔记 ID 和工作流 ID
建立唯一约束。

### 6.6 知识检索流程

``` text
用户问题
   |
   v
问题分类
   |
   +---- 账号问题 ------> 账号知识库
   |
   +---- 爆款问题 ------> 爆款案例库
   |
   +---- 运营方法问题 --> 运营方法库
   |
   +---- 数据问题 ------> services/xhs 的指标表
   |
   v
检索结果排序与筛选
   |
   v
LLM 结合上下文生成回答
   |
   v
返回答案和来源引用
```

不要用向量检索回答精确统计问题。例如"收藏量最高的 10 篇笔记"应执行 SQL
查询，而不是依靠语义相似度。

机器人回答知识库问题时应提供来源文件和相关标题。没有检索到证据时，明确说明没有找到，不得编造知识库结论。

### 6.7 知识入库机制

知识入库采用"AI 提取 + 人工确认"：

``` text
接收资料
   |
   v
内容提取
   |
   v
分类、标签和摘要生成
   |
   v
相似内容检查
   |
   v
写入 knowledge/inbox/pending
   |
   v
人工审核
   |
   +---- 通过 ----> 正式知识目录 + SQLite 索引
   |
   +---- 拒绝 ----> 标记 rejected 或归档
```

以下内容可作为入库来源： - 爆款拆解结果； - 有长期价值的热点研究； -
已发布原创笔记； - 人工确认的运营复盘； -
用户主动提交的文章、文档和链接。

不要将一次偶然的数据表现自动总结为永久运营规律。AI
生成的结论应标注为观察、假设或已验证经验，并记录适用范围。

------------------------------------------------------------------------

## 7. 工作流设计

运营主流程是下面八步。每一步保存自己的产物，下一步只读取状态明确的上游结果。采集失败、空结果和模拟数据停在素材池，不进入分析。

``` text
1 热点与素材发现
        ↓
2 热点分析与账号适配
        ↓
3 选题决策与内容策划
        ↓
4 图文内容生产
        ↓
5 视觉设计与卡片生成
        ↓
6 人工审核与发布
        ↓
7 数据跟踪与效果复盘
        ↓
8 知识沉淀与策略优化
        ↓
   回到第 2 步和第 3 步
```

### 7.1 热点与素材发现

多渠道发现热点，形成统一素材池。

-   小红书：轻量热点采集、公开内容采集、人工补充。热点榜优先用 xiaohongshu-hot-daily；每日爆款用 xiaohongshu-dailytop；关键词、详情和评论用 MediaCrawler。选定案例的图片和视频用 XHS-Downloader 归档。
-   其他平台：抖音、B站、微博、知乎等作为趋势和灵感来源。第一版由人工放入链接、截图或文案。自动采集以后再接入，并且仍要满足第 11 节的筛选标准。Agent-Reach 因 Cookie 维护成本不使用。
-   人工输入：笔记链接、截图、文案、竞品账号。
-   采集异常时标记 `failed`、`empty`、`auth_required` 等状态。不用模拟数据冒充真实热点。

素材写入 `materials`，并保留来源平台、进入方式和原始采集状态。同一条内容按链接或笔记 ID 去重。

输出：统一素材池。

### 7.2 热点分析与账号适配

判断热点是否适合当前账号，而不只是判断热点是否热门。分析只使用素材池中状态为 `ok` 或 `partial` 的真实条目，并读取账号配置和历史笔记。

-   热点热度：近期讨论量、互动表现、增长趋势。
-   账号匹配：是否符合账号定位、目标读者和内容风格。
-   历史表现：参考本账号过往笔记的曝光、互动和转化。
-   竞争与差异化：是否有新的切入角度。
-   制作成本：预估文案、图片和制作时间。

输出：热点分析报告、账号适配度和候选选题。

### 7.3 选题决策与内容策划

从候选选题中确定值得投入的主题。人工确认选题后，才进入内容生产。

-   确定目标读者和用户需求。
-   确定内容角度、核心观点和差异化表达。
-   设计标题、正文结构和内容节奏。
-   确定图文页数、每页核心信息和行动引导。

输出：选题方案和内容脚本。

### 7.4 图文内容生产

AI 负责内容创作，人负责把控质量。生成结果是草稿，不是待发布版本。

-   生成标题、正文、摘要和标签。
-   根据内容类型选择模板：知识科普、教程步骤、观点分析、经验分享等。
-   将文案拆分成 3～6 页图文卡片。
-   生成结构化内容数据，供第 5 步的视觉引擎使用。

输出：完整笔记文案和图文页面内容。

### 7.5 视觉设计与卡片生成

视觉生产是独立环节，重点解决封面和排版耗时问题。它消费第 4 步的结构化页面数据，不在文案生成时顺带出图。

-   AI 生成封面创意、页面布局和视觉风格。
-   使用固定模板渲染文字、标题、图标和装饰元素。
-   AI 按需生成插画或背景素材。
-   自动检查文字溢出、图片尺寸、字体和页面一致性。

视觉方案使用 xhs-visual-director-skill，卡片生产使用 baoyu-xhs-images。两者不互相替代。

输出：封面图、正文配图及完整图文预览。

### 7.6 人工审核与发布

人工负责最终质量和发布决策。

-   审核事实准确性、原创性和内容质量。
-   检查图片、排版、标题及平台规范。
-   人工确认最终版本。
-   经明确授权后，通过小红书 MCP 等工具辅助发布。
-   保存发布记录和内容版本。

标题、正文或图片发生变化后，原确认失效，按第 8 节的审批规则重新确认。发布失败保留原因，不自动连续重试。

输出：已发布笔记及发布记录。

### 7.7 数据跟踪与效果复盘

以实际发布数据验证选题和内容策略。

-   记录曝光、阅读、点赞、收藏、评论等指标。
-   对比不同选题、标题、封面和内容结构的表现。
-   分析账号自身的历史表现，不简单套用其他账号的爆款数据。
-   找出高表现和低表现内容的可能原因。

指标来自人工录入或后续经过验证的合规获取方式。报告中的原因标为观察或假设，并写明依据的是哪些笔记。

输出：笔记分析报告、运营周期报告和优化建议。

### 7.8 知识沉淀与策略优化

将运营结果沉淀为可复用的知识资产。入库仍走第 6.7 节的人工确认。

-   优秀笔记沉淀为爆款案例。
-   账号表现沉淀为账号画像和历史数据。
-   有效的内容结构沉淀为模板。
-   复盘结论经人工确认后更新运营策略。
-   将新知识反馈到下一轮热点分析和选题决策。

输出：持续更新的运营知识库。

### 7.9 工作流状态管理

建议采用 SQLite 持久化状态机，不需要第一版就引入 Temporal 等工作流平台。

通用状态：

-   `PENDING`：等待执行；
-   `RUNNING`：执行中；
-   `WAITING_INPUT`：等待用户补充信息；
-   `WAITING_APPROVAL`：等待人工审批；
-   `COMPLETED`：完成；
-   `REJECTED`：人工拒绝；
-   `FAILED`：执行失败；
-   `CANCELLED`：已取消。

工作流记录应包括任务
ID、当前状态、输入参数、执行步骤、输出结果、错误信息、重试次数和时间戳。

------------------------------------------------------------------------

## 8. 内容审核与发布安全

### 8.1 发布状态机

``` text
DRAFT
  |
  v
REVIEW
  |
  v
WAITING_APPROVAL
  |
  +---- 人工拒绝 ----> REJECTED
  |
  +---- 人工确认 ----> PUBLISHING
                           |
                           +---- 成功 ----> PUBLISHED
                           |
                           +---- 失败 ----> FAILED
```

### 8.2 审批规则

1.  只有进入 `WAITING_APPROVAL` 的笔记才可以申请发布审批。
2.  审批必须绑定具体笔记 ID 和内容版本。
3.  标题、正文或图片发生修改后，原审批自动失效。
4.  必须针对当前笔记明确确认，不得将一次授权理解为永久授权。
5.  发布失败应记录原因，不允许无限自动重试。
6.  发布工具仅在审批有效时执行。

### 8.3 本机安全

-   Agent 服务默认只监听 `127.0.0.1`。
-   MCP Adapter 只连接本机服务。
-   API Token 和第三方密钥通过环境变量或安全配置读取。
-   不将 Cookie、Token、个人账号凭据提交到 Git。
-   不将小红书 MCP 服务直接暴露到公网。
-   对发布、审批和数据修改操作保留审计记录。

------------------------------------------------------------------------

## 9. 代码落点

改动都在 `D:\09.person\AI-workspace` 里。

``` text
AI-workspace/
├── apps/web/src/xhs/              # 页面、类型和 API 封装
├── apps/web/src/App.tsx           # 注册 /content/xhs 路由
├── apps/web/docker/nginx.conf     # 增加 /api/xhs
├── services/xhs/                  # 新增 Python 服务
│   ├── server.py
│   ├── xhs_svc/
│   │   ├── api.py
│   │   ├── materials.py
│   │   ├── collector.py
│   │   ├── workflow.py
│   │   ├── approval.py
│   │   └── db.py
│   └── configs/
├── services/agent-core/
│   ├── configs/agents/xhs-ops.yaml
│   ├── configs/agent-routing.yaml
│   ├── core_svc/routing.py        # 功能列表
│   ├── core_svc/local_engine.py   # system_for
│   └── skills/xhs-*/
├── data/xhs/                      # SQLite、图片、导入用 Markdown
├── deploy/docker-compose.yml
└── scripts/aiw.py                 # pack / start 增加 xhs
```

### 9.1 职责

-   `apps/web/src/xhs/`：八步页面。写法对齐 `apps/web/src/a-share`。
-   `services/xhs/`：素材池、采集适配、任务、版本和审批。
-   `services/agent-core/`：只增加功能、提示词和技能。不把爬虫进程放进对话服务。
-   `services/knowledge/`：增加 `kb_xhs` 的创建和导入。检索接口不变。
-   `data/xhs/`：业务库和文件。知识 Markdown 在 `data/xhs/knowledge/`。

------------------------------------------------------------------------

## 10. API

页面能直接用的现有接口：

| 方法 | 路径 | 服务 | 用途 |
| --- | --- | --- | --- |
| `POST` | `/v1/agent-turns` | agent-core | 运营对话，SSE |
| `GET` `PUT` | `/v1/engine/routing` | agent-core | 选择本地模型或 Codex |
| `POST` | `/api/knowledge/retrieve` | knowledge | 检索 `kb_xhs` 等库 |
| `GET` | `/api/agent/content/drafts` | agent | 通用草稿，小红书八步不使用 |

`services/xhs` 新增：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/xhs/collect` | 发起一次采集 |
| `GET` | `/api/xhs/collect/{id}` | 采集状态和统一 JSON |
| `GET` | `/api/xhs/materials` | 素材池 |
| `POST` | `/api/xhs/materials` | 人工放入链接、截图说明或文案 |
| `POST` | `/api/xhs/workflows` | 创建八步任务 |
| `GET` | `/api/xhs/workflows/{id}` | 当前步骤和产物 |
| `GET` | `/api/xhs/topics` | 选题列表 |
| `GET` | `/api/xhs/notes` | 笔记和版本 |
| `POST` | `/api/xhs/approvals` | 对当前版本提交确认 |
| `POST` | `/api/xhs/notes/{id}/metrics` | 录入本账号指标 |

采集请求和失败状态仍用第 11 节的 JSON。对话请求用第 5.2 节的 `prompt`、`function_id` 和 `context`。

错误体与 knowledge 一致：`{"error":"..."}`。删除成功返回 `204`。

------------------------------------------------------------------------

## 11. 外部项目组合

第一版优先复用现有开源项目，不重复开发已有能力。采集项目不直接进入业务代码，先经过统一采集接口和 PoC。

小红书采集只接受同时满足下面四条的工具：

1.  只服务小红书，不为了跨平台引入另一套登录体系。
2.  尽量免费。仓库开源免费，还要单独确认数据接口是否免费、是否会变成付费。
3.  不依赖长期维护 Cookie。允许用户偶发扫码，不接受把复制、刷新和保活 Cookie 当成日常步骤。
4.  能输出结构化数据，并由 `services/xhs` 的适配器接进工作台。

按这个标准，优先测试两个方向：

-   **免登录浏览器采集**：每天发现小红书公开热门笔记。先测 xiaohongshu-hot-daily，再测 xiaohongshu-dailytop。
-   **开源爬虫框架**：后续做关键词搜索、笔记详情、评论和竞品分析。对应 MediaCrawler。XHS-Downloader 只做选定案例的素材归档。

仓库免费，不等于数据接口永久免费，也不等于永远不需要登录。小红书页面结构和访问策略变化后，原来可用的采集方式也会失效。PoC 记录的是当时的结果，接入后仍要能返回 `failed`。

  环节         项目                          主要用途                         集成建议
  ------------ ----------------------------- -------------------------------- ----------------------------------------
  热点榜       xiaohongshu-hot-daily         免登录读取公开热门笔记           优先 PoC，通过后作为热点主路径
  每日爆款     xiaohongshu-dailytop          按分类或关键词查看当日爆款       验证多数据源和本机 Playwright
  深度采集     MediaCrawler                  关键词搜索、笔记详情、评论       PoC 通过后按小规模任务启用
  素材归档     XHS-Downloader                归档选定笔记的图片、封面和视频   只处理已选定的参考笔记
  跨平台采集   Agent-Reach                   依赖 Cookie 的跨平台信息         不符合小红书筛选标准，默认关闭
  爆款分析     xiaohongshu-ops-skill         爆款拆解、账号诊断               先验证 Codex 兼容性和实际能力
  视觉策划     xhs-visual-director-skill     封面、分页面画面和提示词规划     负责视觉方案，不重复负责图片生产
  图片生成     baoyu-xhs-images              将文章拆分为多张图文卡片         负责图片生产
  小红书发布   xiaohongshu-mcp               发布图文笔记                     仅在人工审批后调用

项目地址：

-   Agent-Reach：<https://github.com/Panniantong/Agent-Reach>
-   MediaCrawler：<https://github.com/NanmiCoder/MediaCrawler>
-   XHS-Downloader：<https://github.com/JoeanAmier/XHS-Downloader>
-   xiaohongshu-ops-skill：<https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill>
-   xhs-visual-director-skill：<https://github.com/ziguishian/xhs-visual-director-skill>
-   baoyu-skills：<https://github.com/JimLiu/baoyu-skills>
-   xiaohongshu-mcp：<https://github.com/xpzouying/xiaohongshu-mcp>

> 注意：以上项目的仓库地址、Skill
> 名称、运行方式和接口能力应在实施时逐一核验。不要仅凭 GitHub Star
> 数判断项目成熟度。重点验证 Windows 环境、Codex
> 兼容性、登录状态、稳定性和数据合规性。
>
> xiaohongshu-hot-daily 与 xiaohongshu-dailytop
> 目前主要以技能包形式流传。技能说明里出现过
> `https://github.com/openclaw/xiaohongshu-hot-daily`，2026-11-21
> 核验时该地址无法访问。许可证、运行方式和数据源以拿到的项目文件为准。

### 11.1 采集工具分工

四个小红书项目按任务拆开，由 Collector Router 选择。Agent-Reach 不参与这条路由。

**xiaohongshu-hot-daily：第一个测试，每日热点。**

技术组合是 Python、agent-browser 和 Chromium，许可证为 MIT。它用浏览器读取小红书探索页的公开热门笔记，声称无需登录，按点赞取 Top N，并可做关键词分类、摘要和 JSON 导出，也能配定时任务每天收集。

它适合第一阶段：每天发现公开热门内容。关键词搜索、评论和素材下载不由它承担。

项目说明写明，浏览器不可用时会改用模拟数据。这个行为不能进入正式运营。Go 适配器要包住它：关闭模拟数据回退；浏览器不可用、超时或识别到模拟数据时，返回 `status=failed`，`items` 为空。正式流程只接受真实笔记。

**xiaohongshu-dailytop：第二个测试，多源回退。**

技术组合是 Node.js 或 Python，加上 Playwright。它的数据源按固定顺序回退：

``` text
RedFox API
    ↓ 不可用
自定义 API
    ↓ 不可用
Playwright 本地抓取
```

它支持两种语言、输出统一格式、返回原始笔记链接，并可作为 Codex 等 Agent Skill 使用。RedFox 是可选数据源，项目不强制使用付费 API。自动充值不接入 `services/xhs`。API Key 只从环境变量读取。

值得借鉴的是回退结构。PoC 要单独证明最后一级：Playwright 能否在不登录时取得真实笔记，以及重复运行时字段和链接是否稳定。某一级失败不能被上一级的成功覆盖。页面能打开但列表为空，记为 `empty` 或 `auth_required`。Playwright 这一级未通过时，dailytop 不作为免登录热点源；已通过的 hot-daily 继续承担每日热点。

**MediaCrawler：后续深度采集。**

仓库为 NanmiCoder/MediaCrawler，技术组合是 Python、Playwright 和 SQLite 等存储。截至 2026-11-21，GitHub 页面约 71.5K Stars、852 次提交，之后以仓库页面为准。

它支持小红书关键词搜索、笔记详情、互动数据、评论和指定博主作品，可存 CSV、JSON、SQLite、MySQL，并提供 Web UI。素材文件归档仍交给 XHS-Downloader，避免两套文件目录。

它解决不了免登录问题。当前推荐连接本机 Chrome，复用已有登录状态，也支持扫码登录。这样不必手工复制 Cookie，但仍然依赖有效登录态。登录态留在本机浏览器目录，不提交到 Git。遇到验证码、登录失效或风控提示时停止并返回 `failed` 或 `auth_required`。本方案不设计绕过平台校验的做法。

因此它用于后续的关键词、详情、评论和竞品分析，不作为每日热点的唯一入口。第一版 PoC 先做小规模搜索、详情和评论；指定博主采集在这次 PoC 通过后再单独打开。项目使用非商业学习许可，只作个人学习和技术验证，不并入本仓库源码。

**XHS-Downloader：爆款素材归档。**

仓库为 JoeanAmier/XHS-Downloader。它提取作品、搜索结果和用户作品链接，并下载笔记图片、视频等内容。用途是选定爆款案例后的素材归档，不是热点榜工具。

人工选定笔记后，把封面、图片或视频保存到 `workspace/`，数据库只记录相对路径。集成使用本机命令行或仅监听 `127.0.0.1` 的 API。是否需要登录按实际下载场景验证，不把它写成免登录方案。项目为 GPL-3.0，以外部进程调用，不把源码拷进本仓库。

**Agent-Reach：因 Cookie 问题不进入小红书主路径。**

Agent-Reach 的小红书能力依赖 Cookie，而 Cookie 会失效，需要持续维护。这不符合本节的筛选标准。小红书热点、日榜、搜索、详情、评论和素材归档都不使用它。配置保持关闭；第一版不为它单独做通过性验收。

四个小红书项目的差异：

  项目                     主要能力                     登录依赖               免费情况                     推荐用途
  ------------------------ ---------------------------- ---------------------- ---------------------------- ------------------
  xiaohongshu-hot-daily    探索页热门笔记               声称无需登录           免费，MIT                    每日热点
  xiaohongshu-dailytop     多源热门采集                 需验证本地采集方式     本地采集免费，API 可付费     热点采集
  MediaCrawler             搜索、详情、评论、博主       需要登录态             开源免费                     深度研究
  XHS-Downloader           搜索结果、作品及素材         按实际采集场景验证     开源免费                     案例素材归档

### 11.2 统一采集接口

采集器在 `services/xhs/xhs_svc/collector.py` 实现同一组能力。页面和八步任务只提交能力名和参数，不写某个项目的命令行。

``` python
CAPABILITIES = (
    "hot_list",
    "daily_rank",
    "search",
    "note_detail",
    "comments",
    "media_archive",
)
```

请求字段为 `capability`、`keyword`、`category`、`note_url`、`top_n`、`source`。适配器返回第 11.3 节的 JSON。模型不直接执行这些进程。

路由器按能力选择已启用的采集器：

  能力               默认采集器              关闭时的行为
  ------------------ ----------------------- ------------------------------
  `hot_list`         xiaohongshu-hot-daily   返回 `source_unavailable`
  `daily_rank`       xiaohongshu-dailytop    返回 `source_unavailable`
  `search`           MediaCrawler            返回 `source_unavailable`
  `note_detail`      MediaCrawler            返回 `source_unavailable`
  `comments`         MediaCrawler            返回 `source_unavailable`
  `media_archive`    XHS-Downloader          返回 `source_unavailable`

`cross_platform` 第一版不注册。Agent-Reach 不进入路由器。

`source` 用于写明实际成功的数据源。dailytop 未指定 `source` 时，按 `redfox`、`custom_api`、`playwright` 顺序回退。每一跳的失败原因单独保留，最终 `source` 只能是真正返回数据的那一级。

适配器负责超时、进程退出码和输出解析。解析失败返回 `parse_failed`，不把原始报错直接交给模型当作笔记内容。

建议配置：

``` yaml
collectors:
  hot_daily:
    enabled: false
  daily_top:
    enabled: false
    fallback:
      - redfox
      - custom_api
      - playwright
  media_crawler:
    enabled: false
    max_notes: 15
    max_comments_per_note: 10
  xhs_downloader:
    enabled: false
  agent_reach:
    enabled: false
```

上例是 PoC 之前的配置，五个采集器都关闭。P0 通过后只打开 `hot_daily`；其余采集器在各自 PoC 通过后单独打开。

### 11.3 JSON 数据结构

每次采集产生一份结果。原始 JSON 写入 `collect_runs`，条目写入 `collected_items`。缺字段保留 `null`，不用 0 或空字符串冒充"已采集"。

``` json
{
  "task_id": "collect-001",
  "collector": "xiaohongshu-hot-daily",
  "capability": "hot_list",
  "source": "browser",
  "status": "ok",
  "collected_at": "2026-11-21T18:00:00+08:00",
  "query": {
    "keyword": "",
    "category": "",
    "note_url": "",
    "top_n": 10
  },
  "error": null,
  "items": [
    {
      "platform": "xiaohongshu",
      "note_id": "",
      "title": "",
      "author": "",
      "url": "",
      "cover_url": "",
      "category": "",
      "published_at": null,
      "content": null,
      "metrics": {
        "like_count": null,
        "collect_count": null,
        "comment_count": null,
        "share_count": null
      },
      "comments": [],
      "media_files": [],
      "source": {
        "collector": "xiaohongshu-hot-daily",
        "source_name": "browser",
        "raw_ref": ""
      }
    }
  ]
}
```

字段约定：

-   `collector`：实际执行的项目名。
-   `source` / `source_name`：同一项目内的数据源，例如 `browser`、`playwright`、`api`。
-   `note_id` 和 `url`：至少有一项可回溯到来源页面。两者都没有的条目丢弃。
-   `content`：笔记正文。热点榜通常为空。
-   `comments`：仅 `comments` 能力填充，元素包含评论 ID、文本和点赞数。不采集评论者的联系方式。
-   `media_files`：仅素材归档填充，保存工作区相对路径和文件类型。
-   `metrics`：页面没有给出的指标保持 `null`。

评论元素：

``` json
{
  "comment_id": "",
  "text": "",
  "like_count": null
}
```

素材元素：

``` json
{
  "type": "image",
  "relative_path": "workspace/assets/note-001/001.webp"
}
```

`type` 取 `image`、`cover`、`video` 或 `live_photo`。

### 11.4 失败状态

采集失败是结果的一部分。适配器捕获错误后仍返回 `CollectResult`，`items` 为空数组或已成功的部分条目。进程崩溃、超时未产出文件时，接口返回 error，并由调用方补一条失败记录。

  状态                   含义                                       后续处理
  ---------------------- ------------------------------------------ ------------------------------------
  `ok`                   取得真实数据，字段通过基本校验             可进入归类和选题
  `partial`              部分条目成功，其余失败                     只使用成功条目，并保留失败原因
  `empty`                请求完成，但没有真实条目                   不进入选题，不解释成"该主题没有热点"
  `failed`               浏览器失败、模拟数据或采集过程失败         整次结果丢弃，正式流程不使用
  `auth_required`        需要登录或登录态失效                       保持该采集器关闭，等待人工处理
  `rate_limited`         来源限流                                   停止本次任务，不做连续重试
  `timeout`              超过适配器超时                             记失败，允许人工再次发起
  `source_unavailable`   采集器未启用、未安装或所选源不存在         保留失败状态，由人工决定是否改用其他已启用采集器
  `parse_failed`         进程有输出，但无法映射到统一 JSON          保留原始输出路径供排查
  `cancelled`            人工取消                                   不保留半成品条目

`partial` 必须列出失败条目或失败数量。只有标题、没有可打开链接的热点结果记为 `parse_failed`。hot-daily 的模拟数据即使结构完整，也记为 `failed`，`error.code` 取 `mock_data`。浏览器不可用时 `error.code` 取 `browser_unavailable`。

### 11.5 PoC 测试计划

PoC 在 Windows 本机执行。每个项目单独记录命令、数据源、状态和样例 JSON。通过后再把配置改为 `enabled: true`。

  编号   项目                     验证内容                               通过标准                                                         未通过时
  ------ ------------------------ -------------------------------------- ---------------------------------------------------------------- ------------------------------
  P0     xiaohongshu-hot-daily    免登录热点，且失败不回退模拟数据           不登录取得不少于 5 条真实笔记，含标题和可打开链接；模拟数据返回 `failed`   热点主路径不验收
  P1     xiaohongshu-dailytop     Playwright 能否免登录且结果稳定        最后一级在不登录时取得真实链接；重复运行字段稳定；三级结果分开记录       不作为免登录源，不阻塞 P0
  P2     MediaCrawler             关键词搜索、笔记详情、评论             一个关键词的小规模结果能映射到统一 JSON，且详情或评论至少一类有值   深度采集保持关闭
  P3     XHS-Downloader           爆款素材归档                           一条已选定笔记的封面或图片写入 workspace，JSON 中为相对路径         选题流程仍可继续，归档步骤标失败
P0 是热点主路径的门槛。包装层必须演示一次浏览器失败：结果为 `failed`，选题库中没有新增笔记。P1 对 RedFox、自定义 API 和 Playwright 分别记录是否免费、是否需要登录、是否返回原始链接。P1 的通过只看 Playwright 这一级。P2 的规模沿用配置上限，并记录它复用的是本机登录态还是扫码登录。P3 使用 P0 或 P1 已取得的真实链接，同时记录该次下载是否要求登录。Agent-Reach 不列入 PoC 通过条件。

PoC 报告至少包含：项目版本或提交、Windows 上的运行方式、是否需要登录、实际数据源、结果状态、样例条数、失败时的原始输出位置。

### 11.6 接到 AI-workspace

`services/xhs` 调用采集器。页面和 agent-core 都不直接执行这些项目。

1.  适配器在 `services/xhs/xhs_svc/collector.py`。每个适配器把外部命令或本机 HTTP 的输出映射为第 11.3 节的 JSON。
2.  路由器按第 11.2 节的能力表选择已启用采集器。该能力没有已启用采集器时返回 `source_unavailable`。
3.  页面只调用 `POST /api/xhs/collect`。`xhs_ops` 对话读取采集结果，不把五个外部项目变成五个对话工具。
4.  `GET /api/xhs/collect/{id}` 返回状态、错误和条目。
5.  热点分析只消费 `status` 为 `ok` 或 `partial` 的条目。`partial` 中失败的部分不参与评分。
6.  素材归档在人工选定参考笔记之后执行。文件写入 `data/xhs/`。归档失败不回滚已保存的选题。
7.  密钥和浏览器用户目录留在本机环境或采集项目自己的配置目录，不进入 Git，也不写入知识库 Markdown。小红书主路径不增加 Cookie 刷新任务。

### 11.7 能力边界与使用约束

-   xiaohongshu-hot-daily 负责每日公开热点。浏览器失败时由包装层返回 `failed`。
-   xiaohongshu-dailytop 负责多源热点，免登录能力以 Playwright 最后一级的验证结果为准。
-   MediaCrawler 负责后续的关键词搜索、笔记详情、评论和竞品分析，依赖登录态。
-   XHS-Downloader 负责已选定案例的链接提取和素材归档。
-   Agent-Reach 因 Cookie 维护成本不进入小红书采集。
-   运营 Skill 负责内容分析方法。
-   Visual Director 负责视觉策划。
-   Baoyu 负责图片生产。
-   小红书 MCP 负责发布执行。
-   `services/xhs` 负责调度、状态和归一化。确认后的知识交给 knowledge 服务。

同一类数据只由一个已启用采集器生产。评论不从下载器补抓，图片文件不从 MediaCrawler 再下一份。

采集范围限于公开笔记和用户主动提供的链接，服务个人运营参考。遇到验证码、登录失效或风控提示即停止。不把他人正文直接写入待发布草稿。MediaCrawler 按它的非商业学习许可使用；XHS-Downloader 按外部程序调用。

------------------------------------------------------------------------

## 12. 账号配置设计

账号定位尚未确定，因此使用配置文件管理，不在代码中硬编码。

`services/xhs/configs/account.yaml`：

``` yaml
account:
  name: ""
  positioning: "待确定"
  target_audience: []

content:
  enabled_categories: []
  preferred_types:
    - 教程
    - 经验分享
    - 工具测评
    - 知识科普

  avoid:
    - 未经核实的热点
    - 直接搬运他人内容
    - 无实际价值的营销内容

style:
  tone: "自然、真实、有信息价值"
  language: "简体中文"

publishing:
  mode: "manual_approval"
  auto_publish: false
```

在账号定位明确之前，可以先进行小规模选题实验，积累数据后再确定长期内容方向。

------------------------------------------------------------------------

## 13. 实施计划与里程碑

以下为初步开发估算，实际进度取决于外部项目适配和接口验证情况。

### M1：接上现有工作台（预计 2～3 天）

-   [ ] 增加 `services/xhs` 的健康检查，并挂到 compose、`aiw.py` 和 nginx 的 `/api/xhs`。
-   [ ] 在 `apps/web` 增加 `/content/xhs` 页面壳。
-   [ ] 增加功能 `xhs_ops`：路由表、`system_for` 和 agent 配置。
-   [ ] 沿用 `/settings` 里已配置的模型，不另接一套 LLM。
-   [ ] 从内容中心发起一轮 `POST /v1/agent-turns`。

**验收标准：** 打开 `http://127.0.0.1:5173/content/xhs`，能完成一轮运营对话。响应头能看出用的是 `agent-core` 或 `codex`。

### M2：运营知识库（预计 2～3 天）

-   [ ] 在 knowledge 中创建 `kb_xhs`。
-   [ ] 按第 6.3 节导入一份选题方法 Markdown。
-   [ ] `xhs_ops` 的上下文传入 `knowledge_base_ids: ["kb_xhs"]`。
-   [ ] 回答带来源文档。找不到时说明没找到。

**验收标准：** 在内容中心提问选题方法，回答引用刚导入的文档。检索走现有 `POST /api/knowledge/retrieve`。

### M3：小红书运营工作流（预计 4～6 天）

-   [ ] 实现 Collector 接口、统一 JSON 和失败状态。
-   [ ] 完成 P0：xiaohongshu-hot-daily 免登录热点。
-   [ ] 完成 P1：xiaohongshu-dailytop 的三级回退，并单独验证 Playwright 免登录结果是否稳定。
-   [ ] 完成 P2：MediaCrawler 的关键词、笔记详情和评论，记录登录态方式。
-   [ ] 完成 P3：XHS-Downloader 素材归档，记录该场景是否需要登录。
-   [ ] 确认 Agent-Reach 保持关闭，小红书工作流不调用它。
-   [ ] 用采集路由器接入热点整理和选题工作流。
-   [ ] 验证运营分析 Skill。
-   [ ] 实现内容创作工作流。
-   [ ] 接入视觉策划和图片生成。
-   [ ] 实现内容审核。
-   [ ] 保存选题、草稿、采集记录和任务记录。

**验收标准：**

1.  P0 通过：不登录即可取得真实公开热点，统一 JSON 的状态为 `ok`。浏览器失败或模拟数据返回 `failed`，选题库不增加笔记。
2.  热点发现工作流经 Collector Router 调用 hot-daily，不调用 Agent-Reach。
3.  P1 留下三级数据源的独立记录。Playwright 未在免登录条件下取得稳定真实链接时，dailytop 不作为免登录热点源。
4.  P2 至少完成一次小规模关键词采集，笔记详情或评论之一映射进统一 JSON，并写明使用的是本机 Chrome 登录态还是扫码登录。登录失效或风控记为 `auth_required` 或 `failed`，深度采集保持关闭。
5.  P3 对一条已选定笔记归档封面或图片，JSON 中记录 workspace 相对路径。
6.  一条 `ok` 的素材能依次形成适配分析、选题方案、3～6 页文案和可预览的图文草稿，任务记录可追踪。

### M4：发布与运营闭环（预计 2～3 天）

-   [ ] 验证小红书 MCP。
-   [ ] 实现审批状态机。
-   [ ] 实现笔记版本绑定。
-   [ ] 实现人工确认后发布。
-   [ ] 保存发布结果。
-   [ ] 建立运营指标记录。
-   [ ] 生成复盘报告。
-   [ ] 将经人工确认的复盘结论入库。

**验收标准：** 完成一篇笔记的人工审核、人工确认和发布记录；用该笔记的实际指标写出复盘，并经人工确认后回写知识库。复盘依据本账号数据，不套用其他账号的爆款结论。

------------------------------------------------------------------------

## 14. 第一版验收标准

不要以安装了多少个 GitHub
项目作为验收标准，而应以实际运营产出作为验收依据。

  验收项目              第一版目标
  --------------------- -----------------------------------------
  内容中心对话          `/content/xhs` 能完成一轮 `xhs_ops`
  模型接入              使用工作台已配置的模型，引擎可在本地模型和 Codex 间切换
  知识检索              能检索 Markdown 并返回来源
  知识入库              支持待审核和正式入库
  热点采集              P0 免登录热点通过，结果为统一 JSON
  每日爆款              P1 证明 Playwright 免登录结果稳定后才启用
  深度采集              P2 通过后才启用搜索、详情、评论和后续竞品分析
  素材归档              P3 通过后，选定笔记能保存本地素材路径
  Agent-Reach           因 Cookie 维护成本保持关闭
  素材池                采集结果和人工输入进入同一素材池，失败状态可见
  账号适配              候选选题同时给出热度和账号适配度
  选题与脚本            人工确定选题后得到选题方案和内容脚本
  内容生产              生成标题、正文，并拆成 3～6 页结构化页面
  视觉生产              独立生成封面、配图和完整预览
  内容审核              能检查事实、文字、图片和内容规范
  发布                  人工确认后完成发布
  数据复盘              能记录笔记指标并形成复盘报告

------------------------------------------------------------------------

## 15. 第一版暂缓建设的内容

为了控制复杂度，以下功能暂时不做：

| 功能 | 暂缓原因 |
| --- | --- |
| 另起 Go 服务或新的前端工程 | 工作台、对话和知识库已经在 AI-workspace |
| 自研爬虫体系 | 先复用现有采集项目 |
| 其他平台自动采集 | 第一版用人工链接、截图和文案进入素材池 |
| 自研图片生成引擎 | 先复用现有图片工具和模型 |
| 自动发布 | 当前明确要求人工审核 |
| 自动评论和私信 | 不是第一版能力，且有额外风险 |
| 独立数据大屏 | 先积累真实运营数据 |
| 多账号管理 | 先跑通单账号 |
| 再引入 Redis / Kafka / Milvus | 现有 SQLite、Qdrant 和可选 LightRAG 够用 |
| 复杂工作流平台 | xhs 服务里的状态表足以支撑第一版 |

------------------------------------------------------------------------

## 16. 后续演进路线

### 第一阶段：内容中心里的小红书模块

-   页面在现有 React 工作台。
-   对话走 agent-core，引擎用已配置的本地模型或 Codex。
-   运营知识进 `kb_xhs`。
-   素材、选题、版本和审批在 `services/xhs`。
-   人工确认后发布。

### 第二阶段：把日常操作补齐

-   定时收集已通过验证的免登录热点。
-   深度采集和素材归档在 PoC 通过后打开。
-   复盘结论稳定写回 `kb_xhs`，下一轮分析能检索到。
-   其他平台仍以人工素材进入，直到有符合筛选标准的采集器。

### 第三阶段：页面加深

八步都留在 `/content/xhs` 下。总览页可以增加一条「今日小红书」入口，不把小红书拆成新的侧栏体系。

------------------------------------------------------------------------

## 17. 已按代码确定的决策

这些项以 `D:\09.person\AI-workspace` 的现状为准：

| 决策项 | 决定 | 依据 |
| --- | --- | --- |
| 宿主 | 扩展 AI-workspace | 仓库已有 Web、知识库和对话 |
| 对话 | `services/agent-core` 的 `/v1/agent-turns` | 问询和头脑风暴已经这么走 |
| Codex | agent-core 的可选引擎 | `core_svc/codex.py`，不是独立客户端 |
| 前端 | 现有 React 工作台 | `apps/web`，专题写法见 `src/a-share` |
| 知识检索 | knowledge + Qdrant | 已有 `kb_default`、`kb_materials` 和 retrieve |
| 小红书状态 | 新增 `services/xhs` | `content_drafts` 字段不够 |
| 采集 | 先免登录热点，再登录态深度采集 | 尽量免费，不长期维护 Cookie |
| Agent-Reach | 不进入小红书主路径 | Cookie 会失效且需要持续维护 |

------------------------------------------------------------------------

## 18. 第一个开发闭环：MVP-01

第一轮只实现：

**内容中心 → agent-core → 已配置的模型 → kb_xhs → 带来源的回答**

具体步骤：

1.  用 `python scripts/aiw.py start` 拉起现有工作台，并加上 `services/xhs` 的健康检查。
2.  打开 `http://127.0.0.1:5173/content/xhs`。
3.  页面发送 `POST /v1/agent-turns`，`function_id` 为 `xhs_ops`。
4.  `context.knowledge_base_ids` 包含 `kb_xhs`。
5.  agent-core 调用 `POST /api/knowledge/retrieve`。
6.  模型结合摘录生成答案。
7.  页面显示答案和来源。

完成这个闭环后，再加素材池、采集、图文和发布。

### MVP-01 验收示例

预先把选题方法导入 `kb_xhs`：

`data/xhs/knowledge/operation/topic-selection.md`

然后在内容中心提问：

> 根据知识库中的选题方法，告诉我如何判断一个 AI 技术热点是否适合做成小红书图文。

预期结果：页面成功调用 agent-core；检索命中这份 Markdown；回答依据检索内容；答案附来源文档；知识库里没有这份文档时，回答说明没找到。

------------------------------------------------------------------------

## 19. 总结

小红书运营是 AI-workspace 上的一个模块。页面在现有 React 工作台的内容中心，对话用 agent-core，确认后的知识进 knowledge 的 `kb_xhs`，素材池、八步状态和审批放在新增的 `services/xhs`。采集器可以替换，失败结果不能当成热点。发布必须由人确认当前版本。

第一版先打通「内容中心里的一轮带来源回答」，再把八步流程接到同一套服务上。
