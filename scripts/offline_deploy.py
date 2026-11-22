#!/usr/bin/env python3
"""在 Ubuntu 上启动已拷贝的 dist（对应 luoged 的 deploy.sh，只用 python3）。

把整个 dist 目录拷到服务器后：

    cd dist/scripts
    python3 deploy.py start
    python3 deploy.py status
    python3 deploy.py stop
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy" / "docker-compose.yml"
IMAGES = ROOT / "docker-images"
ENV_FILE = ROOT / "deploy" / ".env"


def run(cmd: list[str], *, check: bool = True) -> int:
    print("+", " ".join(cmd))
    proc = subprocess.run(cmd)
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc.returncode


def docker_cmd(*args: str) -> list[str]:
    cmd = ["docker", *args]
    if os.name != "nt" and getattr(os, "geteuid", lambda: 0)() != 0:
        return ["sudo", *cmd]
    return cmd


def compose_base() -> list[str]:
    if shutil.which("docker") is None:
        raise SystemExit("未找到 docker。请先安装 Docker。")
    probe = subprocess.run(docker_cmd("compose", "version"), capture_output=True)
    if probe.returncode != 0:
        raise SystemExit("未找到 docker compose。")
    cmd = docker_cmd("compose", "-p", "xhs-workspace", "-f", str(COMPOSE))
    if ENV_FILE.is_file():
        cmd += ["--env-file", str(ENV_FILE)]
    return cmd


def load_images() -> None:
    tars = sorted(IMAGES.glob("*.tar")) if IMAGES.is_dir() else []
    if not tars:
        raise SystemExit("没有镜像包：%s\n请把本机 dist/docker-images/*.tar 一并拷过来。" % IMAGES)
    for tar in tars:
        print("导入 %s（%.0f MB）" % (tar.name, tar.stat().st_size / (1024 * 1024)))
        run(docker_cmd("load", "-i", str(tar)))


def stop_nginx() -> None:
    if shutil.which("systemctl") is None:
        return
    active = subprocess.run(
        ["systemctl", "is-active", "--quiet", "nginx"],
        capture_output=True,
    )
    if active.returncode != 0:
        return
    print("停止宿主机 nginx，把 80 端口留给工作台")
    run(["sudo", "systemctl", "stop", "nginx"], check=False)
    run(["sudo", "systemctl", "disable", "nginx"], check=False)


def cmd_start() -> None:
    if not COMPOSE.is_file():
        raise SystemExit("缺少 %s" % COMPOSE)
    if not ENV_FILE.is_file():
        example = ROOT / "deploy" / ".env.example"
        if example.is_file():
            ENV_FILE.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print("已从 .env.example 生成 deploy/.env，请填入 OPENAI_API_KEY 与 XHS_AUTH_PASSWORD 后重新 start。")
            raise SystemExit(1)
        raise SystemExit("缺少 deploy/.env")
    load_images()
    stop_nginx()
    (ROOT / "data" / "xhs").mkdir(parents=True, exist_ok=True)
    run(compose_base() + ["up", "-d", "--pull", "never", "--remove-orphans"])
    print("已启动。浏览器打开 http://<服务器IP>/")
    print("默认登录（未改密且没有 auth.json 时）：admin / xhs-admin")


def cmd_stop() -> None:
    run(compose_base() + ["stop"], check=False)


def cmd_status() -> None:
    run(compose_base() + ["ps"], check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="离线启动 XHS dist")
    parser.add_argument("command", nargs="?", default="start", choices=["start", "stop", "status"])
    args = parser.parse_args()
    if args.command == "start":
        cmd_start()
    elif args.command == "stop":
        cmd_stop()
    else:
        cmd_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
