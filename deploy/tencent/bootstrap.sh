#!/usr/bin/env bash
# 在腾讯云 Ubuntu 上首次/更新部署（项目已上传到 ~/XHS-workspace）
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/XHS-workspace}"
cd "$APP_DIR"

echo "==> 停止并禁用旧 nginx（释放 80 端口给 XHS）"
if systemctl is-active --quiet nginx 2>/dev/null; then
  sudo systemctl stop nginx
fi
if systemctl is-enabled --quiet nginx 2>/dev/null; then
  sudo systemctl disable nginx || true
fi

echo "==> 检查 Docker"
if ! command -v docker >/dev/null 2>&1; then
  echo "请先安装 Docker： https://docs.docker.com/engine/install/ubuntu/"
  exit 1
fi
sudo systemctl enable --now docker 2>/dev/null || true

echo "==> 加载镜像 tar（若存在）"
mkdir -p dist/docker-images
for f in dist/docker-images/*.tar; do
  [ -f "$f" ] || continue
  echo "  docker load -i $f"
  docker load -i "$f"
done

export XHS_DEPLOY_PROD=1
export XHS_CORS_ORIGINS="${XHS_CORS_ORIGINS:-http://43.156.160.62,http://127.0.0.1:8097}"

if [ ! -f deploy/.env ]; then
  cp deploy/.env.example deploy/.env
  echo "请编辑 deploy/.env 填入 OPENAI_API_KEY 后再次运行本脚本。"
  exit 1
fi

echo "==> 启动 XHS 栈（80 -> 8097）"
python3 scripts/xhs.py stop --down 2>/dev/null || true
XHS_DEPLOY_PROD=1 python3 scripts/xhs.py start

echo "==> 完成。浏览器: http://$(curl -s ifconfig.me 2>/dev/null || echo 43.156.160.62)/"
echo "热点采集：将本机 data/xhs/browser-storage.json 同步到此服务器同路径（Linux 容器无法读本机 Chrome profile）。"