# 腾讯云部署（Ubuntu + Docker）

公网 IP 示例：`43.156.160.62`  
SSH：`ssh -i ~/.ssh/fortune-ai-deploy ubuntu@43.156.160.62`

## 1. 本机（Windows）

修复 SSH 私钥权限（若提示 `UNPROTECTED PRIVATE KEY`）：

```powershell
icacls $env:USERPROFILE\.ssh\fortune-ai-deploy /inheritance:r
icacls $env:USERPROFILE\.ssh\fortune-ai-deploy /grant:r "$($env:USERNAME):(R)"
```

本机一键（构建镜像、上传、停旧 nginx、启动）。默认主机 `43.156.160.62`，密钥 `~/.ssh/fortune-ai-deploy`：

```bash
python scripts/xhs_deploy_remote.py
```

只同步代码、不重新构建镜像：

```bash
python scripts/xhs_deploy_remote.py --skip-pack
```

或手动：`rsync` / `scp` 整个项目到 `~/XHS-workspace`（勿提交 `deploy/.env` 密钥；可复制后在线编辑）。

**务必同步**（热点采集登录态）：

- `data/xhs/browser-storage.json`（本机 `browser-export` 生成）
- `data/xhs/settings/`、`deploy/.env`（含 `OPENAI_API_KEY`）

在 `deploy/.env` 增加：

```env
XHS_CORS_ORIGINS=http://43.156.160.62,http://127.0.0.1:8097
XHS_SKIP_STARTUP_COLLECT=1
```

## 2. 服务器

```bash
cd ~/XHS-workspace
chmod +x deploy/tencent/bootstrap.sh
# 编辑 deploy/.env 后：
./deploy/tencent/bootstrap.sh
```

脚本会：

- `systemctl stop nginx` 并 `disable`（原站点停掉，**80 端口**给 XHS 容器）
- `docker load` 本地上传的 tar
- `XHS_DEPLOY_PROD=1 python3 scripts/xhs.py start`（映射 **80:8097**，agent-core 仅 127.0.0.1）

访问：`http://43.156.160.62/`

## 3. 安全组

腾讯云控制台放行入站 **TCP 80**（若以后上 HTTPS 再放 443）。

## 4. 仍要 nginx 反代时（可选）

若需 HTTPS / 多站点，可重新 enable nginx，用 `deploy/tencent/nginx-xhs.conf` 反代到 `127.0.0.1:8097`，并把 compose prod 里的 `80:8097` 改回仅 `127.0.0.1:8097:8097`。

## 5. 更新

本机改代码后重新 `pack` + `xhs_deploy_remote.py`，服务器再跑 `bootstrap.sh` 或仅 `XHS_DEPLOY_PROD=1 python3 scripts/xhs.py start`。