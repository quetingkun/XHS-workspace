把整个 dist 目录拷到 Ubuntu，例如 /home/ubuntu/xhs-dist
然后：
  cd /home/ubuntu/xhs-dist/scripts
  python3 deploy.py start
  python3 deploy.py status
  python3 deploy.py stop

浏览器：http://<服务器IP>/
start 会停掉宿主机 nginx（若在跑），用 80 端口提供工作台。
登录：未设置 XHS_AUTH_PASSWORD 且没有 data/xhs/auth.json 时为 admin / xhs-admin。
