# 小红书运营

个人单账号的运营台。代码都在这个目录，不往 `AI-workspace` 里加服务。

## 推荐：Docker 启动（默认方案）

需 **Docker Desktop**。日常开发与联调以容器为准；改代码后 `pack` 再 `start`。

```text
copy deploy\.env.example deploy\.env
# 在设置页保存对话模型会自动同步 OPENAI_*（关闭编辑器里的 .env 以免锁文件）
python scripts/xhs.py codex-copy
python scripts/xhs.py pack
python scripts/xhs.py start
```

| 项 | 说明 |
| --- | --- |
| 运营台 | http://127.0.0.1:8097 |
| agent-core（宿主） | http://127.0.0.1:8082（容器内 8081，避免与 AI-workspace 8081 冲突） |
| 数据 | 宿主 `data/xhs/` 挂载进容器，含 `settings/`、`knowledge/`、`browser-profile/` |
| 停止 | `python scripts/xhs.py stop`（`stop --down` 移除容器） |
| 勿与 `redeploy.py` 同占 8097 | Docker 与宿主原生二选一 |

镜像内已安装 **Playwright + Chromium**（热点「手动采集」）。小红书常需登录态：在**宿主机**执行一次 `python scripts/xhs.py browser-login`（或 `python scripts/xhs_browser_login.py`），会写入 `data/xhs/browser-storage.json`（容器优先复用；`browser-profile/` 不能跨 Windows↔Linux 直接共用）。

关闭容器启动时自动补采：`deploy/.env` 里 `XHS_SKIP_STARTUP_COLLECT=1`（默认）或配置 `hot_daily.auto_refresh: false`。

**腾讯云公网**：见 [deploy/tencent/README.md](deploy/tencent/README.md)（停原 nginx、80 端口、远程 `xhs_deploy_remote.py`）。

---

## 本机原生（可选，排错用）

不与 Docker 同时占用 8097 / 8082。

```text
python scripts/redeploy.py
python scripts/redeploy.py --no-agent-core
pip install -r services/xhs/requirements.txt
pip install -r services/agent-core/requirements.txt
python scripts/xhs.py playwright
```

日志：`logs/xhs-server.log`、`logs/agent-core.log`。

---

## 功能要点

页面包括工作台、素材池、选题、一键成文、确认发布和复盘。知识库原文在 `data/xhs/knowledge/`，只有已确认文档进入检索。采集器在 `services/xhs/configs/collectors.yaml`；`hot_daily` 默认开启。浏览器失败和模拟数据记为 `failed`，不能进入选题。

提问走 agent-core（`xhs_ops`，`AGENT_CORE_URL` 在容器内为 `http://agent-core:8081`）。模型读 `data/xhs/settings/llm.settings.json` 与 `deploy/.env`。

发布须先确认当前版本。未设置 `XHS_MCP_URL` 时发布会记为失败，不会假装已发布。

测试：

```text
python -m unittest tests.test_xhs
```