# 热点自动采集路线（与外部项目对照）

日期：2026-11-21  
本仓库 **不接入 Agent-Reach**（仅作架构参考）。采集只走 `collector.py` + `collectors.yaml`。

## 阶段与项目

| 阶段 | 项目 | 本仓库状态 | 通过标准 |
|------|------|------------|----------|
| **P0** | xiaohongshu-hot-daily | 内置 `services/xhs/scripts/hot_list_cli.py`（Playwright，**禁止 mock**） | 免登录 ≥5 条真实标题+可打开链接；失败 `failed`/`empty`，不进选题 |
| **P1** | xiaohongshu-dailytop | `daily_top` 仍关闭；保留三级 `fallback` 配置 | 仅验证 Playwright 最后一级免登录稳定 |
| **P2** | MediaCrawler | `media_crawler` 关闭 | 登录态有效时的搜索/详情/评论 PoC |
| **P3** | XHS-Downloader | `xhs_downloader` 关闭 | 选定笔记素材归档到 `data/xhs/` |

## P0 与 hot-daily 技能的关系

上游 [xiaohongshu-hot-daily](https://github.com/openclaw/xiaohongshu-hot-daily) 类技能在浏览器不可用时会 **fallback 模拟数据**，不能直接用于运营。

本仓库做法：

1. **默认**：`hot_list_cli.py` 自研包装，失败只返回 `failed`/`empty` JSON。
2. **可选**：在 `collectors.yaml` 的 `hot_daily.command` 填写外部进程（例如你自行改掉 mock 的 `fetch_hot.py`），由 `collector.py` 解析 stdout；`_is_mock` 仍会拒绝 `mock: true` 输出。
3. 上游若用 **agent-browser**：需本机 `npm i -g agent-browser && agent-browser install`，命令写在 `command` 字段，**不要**把 mock 分支当成功。

## 配置

`services/xhs/configs/collectors.yaml`：

```yaml
hot_daily:
  enabled: true
  command: ""          # 空 = 内置 hot_list_cli.py
  top_n: 15
  timeout: 120
  browser_channel: chrome   # 或 msedge
```

## 触发采集

- 页面：当日热点 → 手动导入 / 采集探测 → **热点采集**
- API：`POST /api/xhs/collect` body `{"capability":"hot_list"}`
- 定时（Windows 任务计划）：`python scripts/run_hot_collect.py`

## 探索页有 feed 但弹登录窗

人工浏览器里常见：**背后已加载推荐笔记，中间弹出「登录后推荐更懂你的笔记」**。  
这不等于 P0 已通过，但若 DOM/HTML 里已有 ≥5 条探索链接，采集器可记 `ok`（`login_free` 是否成立需你人工判断能否不登录点开链接）。

脚本会尝试 `Esc` 与关闭按钮；仍失败时先用 `python scripts/xhs_browser_login.py` 登录专用 profile。

## 常见问题：0 条 / 安全限制

若页面跳到 `website-login/error` 且 `error_code=300012`，文案多为 **「当前网络存在风险」**——这是小红书对自动化/网络环境的拦截，不是解析 bug。

可选应对（仍须诚实入库，禁止 mock）：

1. 换稳定网络或本机代理后再跑 CLI。
2. 在浏览器里手动打开探索页确认能看 feed。
3. **推荐（单账号工作台）**：`python scripts/xhs_browser_login.py` 在 `data/xhs/browser-profile` 登录一次；采集默认复用该目录。**不要**指向正在使用的 `%LOCALAPPDATA%\Google\Chrome\User Data`（需关 Chrome 且易被识别为自动化）。
4. 免登录 PoC 用 `hot_list_cli.py --ephemeral`（`session_kind: ephemeral`）；默认 profile 采集为 `session_kind: profile`，笔记仍可进选题，但 P0 验收以 ephemeral 成功为准。
5. 加 `--debug` 会在 `data/xhs/collector-raw/` 生成 `hot-last.png` / `hot-last.html` 便于对照。

## 验收 checklist（P0）

- [ ] `python services/xhs/scripts/hot_list_cli.py --top 10` stdout 为 `status: ok` 且 ≥5 items
- [ ] 素材池出现多条 `小红书`、可点「分析选题」
- [ ] 断网或关浏览器时 `status: failed`，且 **无** mock 条目进选题
- [ ] 重复失败在池内合并为一条采集记录