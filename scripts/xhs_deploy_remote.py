#!/usr/bin/env python3
"""本机打包并同步 XHS-workspace 到腾讯云，远程执行 bootstrap。"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIR_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".cursor",
    "browser-profile",
}
EXCLUDE_SUFFIX = {".pyc", ".tar"}


def should_skip(rel: Path) -> bool:
    parts = rel.parts
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    if "logs" in parts or "collector-raw" in parts:
        return True
    if rel.name in {".env"} and "deploy" in parts:
        return False
    if rel.suffix in EXCLUDE_SUFFIX and "dist/docker-images" not in parts:
        return rel.suffix == ".pyc"
    if "dist" in parts and "docker-images" in parts:
        return True
    return False


def make_bundle(path: Path) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for item in ROOT.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(ROOT)
            if should_skip(rel):
                continue
            tar.add(item, arcname=str(rel).replace("\\", "/"))


def ssh_opts(key: Path) -> list[str]:
    return [
        "-i",
        str(key),
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=40",
        "-o",
        "TCPKeepAlive=yes",
    ]


def run_retry(cmd: list[str], *, attempts: int = 3) -> None:
    last = 1
    for n in range(1, attempts + 1):
        print("  尝试 %s/%s" % (n, attempts))
        last = subprocess.call(cmd)
        if last == 0:
            return
        print("  命令失败（%s），稍后重试" % last, file=sys.stderr)
    raise SystemExit("command failed (%s): %s" % (last, " ".join(cmd)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="43.156.160.62")
    parser.add_argument("--user", default="ubuntu")
    parser.add_argument("--key", default=str(Path.home() / ".ssh" / "fortune-ai-deploy"))
    parser.add_argument("--app-dir", default="XHS-workspace")
    parser.add_argument("--skip-pack", action="store_true", help="跳过 docker 镜像构建，只同步代码与数据")
    parser.add_argument("--no-bootstrap", action="store_true", help="只上传，不在服务器启动")
    parser.add_argument("--no-env", action="store_true", help="不上传本机 deploy/.env")
    args = parser.parse_args()

    key = Path(os.path.expanduser(args.key))
    if not key.is_file():
        print("找不到 SSH 私钥:", key, file=sys.stderr)
        return 1

    ssh_base = ["ssh", *ssh_opts(key), f"{args.user}@{args.host}"]
    scp_base = ["scp", *ssh_opts(key)]

    if not args.skip_pack:
        print("==> 本机构建镜像（python scripts/xhs.py pack）")
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "xhs.py"), "pack"], cwd=str(ROOT))

    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "xhs-workspace.tgz"
        print("==> 打包项目…")
        make_bundle(bundle)
        print("  大小 %.1f MB" % (bundle.stat().st_size / (1024 * 1024)))
        remote_tgz = f"/home/{args.user}/{args.app_dir}.tgz"
        print("==> 上传代码包…")
        run_retry(scp_base + [str(bundle), f"{args.user}@{args.host}:{remote_tgz}"])

    remote_dir = f"/home/{args.user}/{args.app_dir}"
    remote_cmds = [
        f"mkdir -p {remote_dir}",
        f"tar -xzf {remote_tgz} -C {remote_dir}",
        f"rm -f {remote_tgz}",
    ]
    print("==> 远程解压…")
    subprocess.check_call(ssh_base + [" && ".join(remote_cmds)])

    image_dir = ROOT / "dist" / "docker-images"
    tars = sorted(image_dir.glob("*.tar")) if image_dir.is_dir() else []
    if tars:
        print("==> 上传镜像 tar（分开传输，避免单包过大被断开）")
        subprocess.check_call(ssh_base + [f"mkdir -p {remote_dir}/dist/docker-images"])
        for tar in tars:
            print("  %s（%.0f MB）" % (tar.name, tar.stat().st_size / (1024 * 1024)))
            remote_tar = f"{remote_dir}/dist/docker-images/{tar.name}"
            run_retry(scp_base + [str(tar), f"{args.user}@{args.host}:{remote_tar}"], attempts=4)

    if not args.no_env:
        local_env = ROOT / "deploy" / ".env"
        if local_env.is_file():
            print("==> 上传 deploy/.env …")
            subprocess.check_call(
                scp_base + [str(local_env), f"{args.user}@{args.host}:{remote_dir}/deploy/.env"]
            )
        else:
            print("本机没有 deploy/.env，服务器将使用已有文件或 .env.example。", file=sys.stderr)
    storage = ROOT / "data" / "xhs" / "browser-storage.json"
    if storage.is_file():
        print("==> 上传 browser-storage.json …")
        subprocess.check_call(
            ssh_base + [f"mkdir -p {remote_dir}/data/xhs"]
        )
        subprocess.check_call(
            scp_base + [str(storage), f"{args.user}@{args.host}:{remote_dir}/data/xhs/browser-storage.json"]
        )

    if not args.no_bootstrap:
        print("==> 远程 bootstrap…")
        subprocess.check_call(
            ssh_base + [f"cd {remote_dir} && chmod +x deploy/tencent/bootstrap.sh && ./deploy/tencent/bootstrap.sh"]
        )

    print("完成: http://%s/" % args.host)
    print("若未配置 deploy/.env，请 SSH 登录编辑后再次运行 bootstrap。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())