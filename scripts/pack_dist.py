#!/usr/bin/env python3
"""打离线 dist，手动拷到 Ubuntu 后用 python3 启动。

    python scripts/pack_dist.py
    python scripts/pack_dist.py --skip-build   # 已有 dist/docker-images/*.tar 时

产出：
    dist/docker-images/*.tar
    dist/scripts/deploy.py
    dist/deploy/docker-compose.yml
    dist/deploy/.env
    dist/skills/
    dist/configs/
    dist/data/xhs/   （设置与登录态，不含 browser-profile）
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def copy_data() -> None:
    src = ROOT / "data" / "xhs"
    dest = DIST / "data" / "xhs"
    dest.mkdir(parents=True, exist_ok=True)
    if not src.is_dir():
        return
    skip = {"browser-profile", "collector-raw", "media"}
    for item in src.iterdir():
        if item.name in skip or item.name.startswith("xhs.sqlite"):
            continue
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true", help="不重新 docker save，沿用已有 tar")
    args = parser.parse_args()

    images = DIST / "docker-images"
    images.mkdir(parents=True, exist_ok=True)
    if not args.skip_build or not any(images.glob("*.tar")):
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "xhs.py"), "pack"], cwd=str(ROOT))
    tars = list(images.glob("*.tar"))
    if len(tars) < 2:
        raise SystemExit("dist/docker-images 里需要 xhs 与 agent-core 两个 tar，当前 %s 个。" % len(tars))

    scripts = DIST / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts" / "offline_deploy.py", scripts / "deploy.py")

    deploy = DIST / "deploy"
    deploy.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "deploy" / "docker-compose.offline.yml", deploy / "docker-compose.yml")
    example = ROOT / "deploy" / ".env.example"
    if example.is_file():
        shutil.copy2(example, deploy / ".env.example")
    env = ROOT / "deploy" / ".env"
    if env.is_file():
        shutil.copy2(env, deploy / ".env")

    copy_tree(ROOT / "services" / "xhs" / "skills", DIST / "skills")
    cfg = DIST / "configs"
    cfg.mkdir(parents=True, exist_ok=True)
    core_cfg = ROOT / "services" / "agent-core" / "configs"
    for name in ("docker.xhs.toml", "agent-routing.yaml"):
        shutil.copy2(core_cfg / name, cfg / name)
    for folder in ("agents", "agent-components"):
        copy_tree(core_cfg / folder, cfg / folder)
    copy_data()

    readme = DIST / "README.txt"
    readme.write_text(
        "把整个 dist 目录拷到 Ubuntu，例如 /home/ubuntu/xhs-dist\n"
        "然后：\n"
        "  cd /home/ubuntu/xhs-dist/scripts\n"
        "  python3 deploy.py start\n"
        "  python3 deploy.py status\n"
        "  python3 deploy.py stop\n"
        "\n"
        "浏览器：http://<服务器IP>/\n"
        "start 会停掉宿主机 nginx（若在跑），用 80 端口提供工作台。\n"
        "登录：未设置 XHS_AUTH_PASSWORD 且没有 data/xhs/auth.json 时为 admin / xhs-admin。\n",
        encoding="utf-8",
    )
    total = sum(p.stat().st_size for p in images.glob("*.tar"))
    print("dist 已就绪：%s" % DIST)
    print("镜像合计 %.0f MB。把 dist 拷到服务器后执行 python3 scripts/deploy.py start" % (total / (1024 * 1024)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
