# -*- coding: utf-8 -*-
"""XHS-workspace 统一入口（推荐）：Docker 编包、启动（对齐 scripts/aiw.py）。

Examples:
  python scripts/xhs.py pack
  python scripts/xhs.py pack --xhs --agent-core
  python scripts/xhs.py start
  python scripts/xhs.py stop
  python scripts/xhs.py stop --down
  python scripts/xhs.py codex-copy
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "deploy" / "docker-compose.yml"
COMPOSE_PROJECT = "xhs-workspace"
IMAGE_DIR = ROOT / "dist" / "docker-images"
ENV_FILE = ROOT / "deploy" / ".env"
ENV_EXAMPLE = ROOT / "deploy" / ".env.example"
LLM_SETTINGS = ROOT / "data" / "xhs" / "settings" / "llm.settings.json"
CODEX_DIR = ROOT / "services" / "agent-core" / "deploy" / "codex-bin"
CODEX_BIN = CODEX_DIR / "codex-linux"
CODEX_STAMP = CODEX_DIR / "codex-linux.stamp"
DEFAULT_AIW_CODEX_DIR = ROOT.parent / "AI-workspace" / "services" / "agent-core" / "deploy" / "codex-bin"

BUILD_TARGETS = {
    "xhs": {
        "service": "xhs",
        "image": "xhs-workspace-xhs:local",
        "tar": "xhs-workspace-xhs-local.tar",
    },
    "agent-core": {
        "service": "agent-core",
        "image": "xhs-workspace-agent-core:local",
        "tar": "xhs-workspace-agent-core-local.tar",
    },
}

DEFAULT_SERVICES = ["xhs", "agent-core"]

SERVICE_PORTS = {
    "xhs": 8097,
}


def agent_core_host_port() -> int:
    raw = os.environ.get("XHS_AGENT_CORE_HOST_PORT", "8082").strip()
    try:
        return int(raw)
    except ValueError:
        return 8082


def host_ports_for_services(services: list[str]) -> list[int]:
    ports: list[int] = []
    for name in services:
        if name == "xhs":
            ports.append(SERVICE_PORTS["xhs"])
        elif name == "agent-core":
            ports.append(agent_core_host_port())
    return sorted(set(ports))

SERVICE_ACCESS = {
    "xhs": {
        "title": "XHS 运营台",
        "url": "http://127.0.0.1:8097/health",
        "open": "http://127.0.0.1:8097",
        "note": "静态页 + /api/xhs",
    },
    "agent-core": {
        "title": "Agent-core",
        "url": "",  # filled in print_access_summary
        "open": "",
        "note": "xhs_ops / Codex（Docker 默认宿主机 8082，容器内 8081）",
    },
}


def log(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.buffer.write((msg + "\n").encode(enc, "replace"))


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    quiet: bool = False,
    stream: bool = False,
) -> tuple[int, str]:
    if not quiet:
        log("  $ " + " ".join(cmd))
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if stream:
        env.setdefault("DOCKER_BUILDKIT", "1")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd or ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    chunks: list[str] = []
    if proc.stdout is not None:
        for line in proc.stdout:
            chunks.append(line)
            if stream and not quiet:
                sys.stdout.write(line)
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
        if not stream and not quiet:
            text = "".join(chunks).rstrip()
            if text:
                log(text)
    code = proc.wait()
    out = "".join(chunks)
    if check and code != 0:
        raise SystemExit("command failed (%s): %s" % (code, " ".join(cmd)))
    return code, out


def run_ok(cmd: list[str], *, quiet: bool = True) -> bool:
    code, _ = run(cmd, check=False, quiet=quiet)
    return code == 0


COMPOSE_PROD = ROOT / "deploy" / "docker-compose.prod.yml"


def docker_cmd(*args: str) -> list[str]:
    """Ubuntu 上的 Docker 套接字需要 root。Windows 和已经是 root 的进程不加 sudo。"""
    cmd = ["docker", *args]
    if os.name != "nt" and getattr(os, "geteuid", lambda: 0)() != 0:
        return ["sudo", *cmd]
    return cmd


def compose_cmd() -> list[str]:
    cmd = docker_cmd("compose", "-p", COMPOSE_PROJECT, "-f", str(COMPOSE_FILE))
    if os.environ.get("XHS_DEPLOY_PROD", "").strip() in {"1", "true", "yes"} and COMPOSE_PROD.is_file():
        cmd += ["-f", str(COMPOSE_PROD)]
    if ENV_FILE.is_file():
        cmd += ["--env-file", str(ENV_FILE)]
    return cmd


def docker_info_ok() -> bool:
    return run_ok(docker_cmd("info"))


def ensure_docker_desktop() -> None:
    if docker_info_ok():
        log("Docker 已就绪。")
        return
    if os.name != "nt":
        raise SystemExit("Docker 未运行，请先启动 Docker。")
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Docker\Docker\Docker Desktop.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Docker", "Docker Desktop.exe"),
    ]
    exe = next((c for c in candidates if c and os.path.isfile(c)), None)
    if not exe:
        raise SystemExit("未找到 Docker Desktop，请手动安装或启动 Docker。")
    log("正在启动 Docker Desktop: %s" % exe)
    subprocess.Popen([exe], cwd=os.path.dirname(exe), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 180
    while time.time() < deadline:
        if docker_info_ok():
            log("Docker Desktop 已就绪。")
            return
        time.sleep(3)
        log("  等待 Docker Desktop…")
    raise SystemExit("等待 Docker Desktop 超时。")


def ensure_image_dir() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def tar_path(name: str) -> Path:
    return IMAGE_DIR / name


def image_exists(image: str) -> bool:
    return run_ok(docker_cmd("image", "inspect", image))


def docker_save(image: str, tar_name: str) -> None:
    ensure_image_dir()
    path = tar_path(tar_name)
    log("Saving %s -> %s" % (image, path))
    code, _ = run(docker_cmd("save", "-o", str(path), image), check=False)
    if code != 0:
        raise SystemExit("docker save 失败: %s" % image)
    if path.is_file():
        log("  wrote %.1f MB" % (path.stat().st_size / (1024.0 * 1024.0)))


def docker_load_file(path: Path) -> None:
    log("Loading %s" % path)
    run(docker_cmd("load", "-i", str(path)))


def load_packed_images() -> None:
    ensure_image_dir()
    files = sorted(IMAGE_DIR.glob("*.tar"))
    if not files:
        log("dist/docker-images/ 下没有 .tar，start 将使用本机已有镜像。")
        return
    for path in files:
        docker_load_file(path)


def codex_bin_ready() -> bool:
    if CODEX_BIN.is_file() and CODEX_BIN.stat().st_size > 0:
        size_mb = CODEX_BIN.stat().st_size / (1024.0 * 1024.0)
        log("  使用本地 codex-linux（%.0f MB），pack 只 COPY 进镜像，不会联网下载。" % size_mb)
        return True
    log(
        "缺少 %s\n"
        "  一次性复制即可：python scripts/xhs.py codex-copy\n"
        "  或手动从 AI-workspace 同路径拷贝 codex-linux（及 codex-linux.stamp）"
        % CODEX_BIN
    )
    return False


def cmd_playwright(_args: argparse.Namespace) -> None:
    """本机（非 Docker）热点采集：安装 playwright 包与 Chromium。"""
    log("==> pip install playwright")
    run([sys.executable, "-m", "pip", "install", "playwright>=1.49.0"], check=True)
    log("==> playwright install chromium")
    run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    log("完成（本机原生排错用）。日常请用 Docker：python scripts/xhs.py pack && start。")


def cmd_browser_login(_args: argparse.Namespace) -> None:
    """本机弹出浏览器登录小红书，写入 browser-storage.json 供 Docker 采集复用。"""
    script = ROOT / "scripts" / "xhs_browser_login.py"
    if not script.is_file():
        raise SystemExit("缺少脚本: %s" % script)
    log("将打开浏览器；登录完成后在终端按 Enter。Docker 部署也请先在本机执行此命令。")
    run([sys.executable, str(script)], check=True)


def cmd_browser_export(_args: argparse.Namespace) -> None:
    """从本机 browser-profile 导出 browser-storage.json（已登录但容器仍失败时用）。"""
    script = ROOT / "scripts" / "xhs_browser_export.py"
    if not script.is_file():
        raise SystemExit("缺少脚本: %s" % script)
    log("从 profile 导出登录态到 data/xhs/browser-storage.json …")
    run([sys.executable, str(script)], check=True)


def cmd_codex_copy(args: argparse.Namespace) -> None:
    src_dir = Path(args.from_dir).resolve()
    src_bin = src_dir / "codex-linux"
    if not src_bin.is_file() or src_bin.stat().st_size == 0:
        raise SystemExit("源目录没有可用的 codex-linux: %s" % src_bin)
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_bin, CODEX_BIN)
    src_stamp = src_dir / "codex-linux.stamp"
    if src_stamp.is_file():
        shutil.copy2(src_stamp, CODEX_STAMP)
    size_mb = CODEX_BIN.stat().st_size / (1024.0 * 1024.0)
    log("已复制 codex-linux -> %s（%.0f MB）" % (CODEX_BIN, size_mb))
    if CODEX_STAMP.is_file():
        log("  stamp: %s" % CODEX_STAMP.read_text(encoding="utf-8").strip())
    log("之后 python scripts/xhs.py pack 仅使用此文件，不会从 GitHub 下载。")


def sync_llm_to_env() -> bool:
    sys.path.insert(0, str(ROOT / "services" / "xhs"))
    from xhs_svc.deploy_env import sync_llm_to_deploy_env

    outcome = sync_llm_to_deploy_env()
    if outcome.written:
        log("已同步设置页 LLM -> deploy/.env（未打印密钥）")
    elif outcome.unchanged:
        log("deploy/.env 已与对话模型配置一致，未改写。")
    elif outcome.warn:
        log("警告: %s" % outcome.warn)
    return outcome.ok


def ensure_env_file() -> None:
    if ENV_FILE.is_file():
        return
    if ENV_EXAMPLE.is_file():
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        log("已创建 deploy/.env（来自 .env.example）")


def _http_ok(url: str, timeout: float = 3) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(getattr(resp, "status", resp.getcode())) < 300
    except Exception:
        return False


def _service_health_url(name: str) -> str:
    if name == "agent-core":
        return "http://127.0.0.1:%s/health" % agent_core_host_port()
    meta = SERVICE_ACCESS.get(name) or {}
    return str(meta.get("url") or "")


def _service_open_url(name: str) -> str:
    if name == "agent-core":
        return "http://127.0.0.1:%s" % agent_core_host_port()
    meta = SERVICE_ACCESS.get(name) or {}
    return str(meta.get("open") or meta.get("url") or "")


def wait_services_ready(services: list[str], timeout_sec: int = 120) -> tuple[bool, list[str]]:
    pending = [s for s in services if s in SERVICE_ACCESS]
    if not pending:
        return True, []
    log("==> 健康检查（最多 %ss）" % timeout_sec)
    deadline = time.time() + timeout_sec
    ok_seen: set[str] = set()
    while time.time() < deadline:
        failed = []
        for name in pending:
            meta = SERVICE_ACCESS[name]
            url = _service_health_url(name)
            ok = _http_ok(url) if url else True
            if ok:
                if name not in ok_seen:
                    log("  OK  %-14s %s" % (meta["title"], url))
                    ok_seen.add(name)
            else:
                failed.append(name)
        if not failed:
            return True, []
        pending = failed
        log("  等待: %s" % ", ".join(failed))
        time.sleep(3)
    return False, pending


def print_access_summary(services: list[str]) -> None:
    log("")
    log("==> 服务已启动")
    for name in services:
        meta = SERVICE_ACCESS.get(name)
        if not meta:
            continue
        log("  %-14s %s" % (meta["title"], _service_open_url(name)))
        log("             %s" % meta["note"])
    log("")
    log("  状态: %s" % " ".join(compose_cmd() + ["ps"]))


def build_service(name: str) -> None:
    meta = BUILD_TARGETS[name]
    if name == "agent-core" and not codex_bin_ready():
        raise SystemExit(1)
    if name == "xhs":
        log("  （xhs 首次约 2–5 分钟：基础镜像 + pip）")
    elif name == "agent-core":
        log("  （agent-core 含大体积 codex COPY，首次可能 5–15 分钟）")
    build_cmd = compose_cmd()
    build_cmd[2:2] = ["--progress", "plain"]
    run(build_cmd + ["build", meta["service"]], stream=True)
    if not image_exists(meta["image"]):
        raise SystemExit("构建完成但镜像不存在: %s" % meta["image"])
    docker_save(meta["image"], meta["tar"])


def pack_default() -> None:
    log("==> pack 默认（xhs + agent-core）")
    for name in ("xhs", "agent-core"):
        log("-- build+save %s" % name)
        build_service(name)
    log("完成。镜像 tar：dist/docker-images/")


def cmd_pack(args: argparse.Namespace) -> None:
    ensure_docker_desktop()
    ensure_image_dir()
    selected: list[str] = []
    if args.xhs:
        selected.append("xhs")
    if args.agent_core:
        selected.append("agent-core")
    if not selected:
        pack_default()
        return
    for name in selected:
        log("==> pack %s" % name)
        build_service(name)
    log("完成。输出: %s" % IMAGE_DIR)


def pids_listening_on(port: int) -> list[int]:
    if os.name != "nt":
        try:
            out = subprocess.check_output(["ss", "-ltnp"], text=True, errors="replace")
        except (OSError, subprocess.CalledProcessError):
            try:
                out = subprocess.check_output(
                    ["lsof", "-i", ":%s" % port, "-sTCP:LISTEN"], text=True, errors="replace"
                )
            except (OSError, subprocess.CalledProcessError):
                return []
        pids: list[int] = []
        for line in out.splitlines():
            if ":%s" % port not in line:
                continue
            for token in line.replace(",", " ").split():
                if token.startswith("pid="):
                    try:
                        pids.append(int(token[4:]))
                    except ValueError:
                        pass
        return sorted(set(pids))

    out = subprocess.check_output(["netstat", "-ano"], text=True, errors="replace")
    pids: list[int] = []
    needle = ":%s" % port
    for line in out.splitlines():
        if "LISTENING" not in line.upper():
            continue
        if needle not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pids.append(int(parts[-1]))
        except ValueError:
            continue
    return sorted(set(pids))


DOCKER_PROTECT = (
    "docker",
    "com.docker",
    "vpnkit",
    "wslrelay",
    "dockerdesktop",
    "vmmem",
    "wsl",
    "limactl",
)
XHS_MARKERS = (
    "xhs-workspace",
    "services/xhs",
    "services\\xhs",
    "services/agent-core",
    "services\\agent-core",
    "redeploy.py",
    "agent-core/server",
    "xhs/server",
)


def process_commandline(pid: int) -> str:
    if os.name != "nt":
        try:
            raw = Path("/proc/%s/cmdline" % pid).read_bytes()
            return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").lower()
        except OSError:
            return ""
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Process -Filter 'ProcessId=%s').CommandLine" % pid,
            ],
            text=True,
            errors="replace",
            timeout=15,
        )
        return (out or "").strip().lower()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def should_kill_listener(pid: int) -> bool:
    if pid in {0, 4}:
        return False
    cmd = process_commandline(pid)
    blob = cmd
    if any(token in blob for token in DOCKER_PROTECT):
        return False
    if "python" not in blob:
        return False
    return any(token in blob for token in XHS_MARKERS) or "server.py" in blob


def wait_ports_clear(ports: list[int], timeout_sec: float = 12.0) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not any(pids_listening_on(port) for port in ports):
            return
        time.sleep(0.5)


def free_host_port(port: int) -> tuple[list[int], list[int]]:
    """只结束本仓库 python 服务，不杀 Docker Desktop / 端口代理进程。"""
    killed: list[int] = []
    skipped: list[int] = []
    for pid in pids_listening_on(port):
        if pid == os.getpid():
            continue
        if not should_kill_listener(pid):
            skipped.append(pid)
            continue
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.3)
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            killed.append(pid)
        except OSError:
            continue
    if killed:
        time.sleep(0.6)
    return killed, skipped


def ensure_host_ports_free(services: list[str]) -> None:
    ports = host_ports_for_services(services)
    wait_ports_clear(ports)
    for port in ports:
        pids = pids_listening_on(port)
        if not pids:
            continue
        log("==> 检查宿主端口 %s（仅结束本机 python xhs/agent-core，不杀 Docker）" % port)
        killed, skipped = free_host_port(port)
        if killed:
            log("  已结束本机服务 PID: %s" % ", ".join(map(str, killed)))
        if skipped:
            log("  保留 PID（Docker/其他）: %s" % ", ".join(map(str, skipped)))
        wait_ports_clear([port], timeout_sec=8.0)
        remaining = pids_listening_on(port)
        if remaining:
            log(
                "  端口 %s 仍被占用（PID %s）。"
                " 请先 `python scripts/xhs.py stop --down`。"
                " agent-core 默认映射宿主机 %s（可用环境变量 XHS_AGENT_CORE_HOST_PORT 修改）。"
                % (port, ", ".join(map(str, remaining)), agent_core_host_port())
            )
            raise SystemExit(1)


def stop_stack(services: list[str]) -> None:
    run(compose_cmd() + ["stop", *services], check=False)


def start_stack(services: list[str]) -> None:
    run(
        compose_cmd()
        + ["up", "-d", "--no-build", "--remove-orphans", "--force-recreate", *services]
    )


def start_services(services: list[str], *, kill_host_ports: bool = True) -> None:
    log("==> ensure Docker")
    ensure_docker_desktop()
    ensure_env_file()
    if sync_llm_to_env():
        log("  （已同步对话模型密钥到 deploy/.env，供容器内 agent-core/Codex 使用）")
    log("==> load image tars")
    load_packed_images()
    log("==> stop if running: %s" % ", ".join(services))
    stop_stack(services)
    run(compose_cmd() + ["down", "--remove-orphans"], check=False)
    if kill_host_ports:
        ensure_host_ports_free(services)
    if not docker_info_ok():
        log("Docker 引擎未响应，正在等待恢复…")
        ensure_docker_desktop()
    log("==> start: %s" % ", ".join(services))
    start_stack(services)
    ok, failed = wait_services_ready(services, timeout_sec=150)
    if not ok:
        raise SystemExit(
            "部分服务未就绪: %s\n检查: %s"
            % (", ".join(failed), " ".join(compose_cmd() + ["ps"]))
        )
    print_access_summary(services)
    log("Done.")


def resolve_services(args: argparse.Namespace) -> list[str]:
    selected: list[str] = []
    if getattr(args, "xhs", False):
        selected.append("xhs")
    if getattr(args, "agent_core", False):
        selected.append("agent-core")
    for raw in getattr(args, "service", None) or []:
        key = raw.strip().lower().replace("_", "-")
        if key in BUILD_TARGETS and key not in selected:
            selected.append(key)
    if not selected:
        selected = list(DEFAULT_SERVICES)
    if "agent-core" in selected and "xhs" not in selected:
        selected.insert(0, "xhs")
    seen: set[str] = set()
    services: list[str] = []
    for name in selected:
        if name not in seen:
            seen.add(name)
            services.append(name)
    return services


def cmd_start(args: argparse.Namespace) -> None:
    start_services(resolve_services(args), kill_host_ports=not args.no_kill_host_ports)


def cmd_stop(args: argparse.Namespace) -> None:
    ensure_docker_desktop()
    services = resolve_services(args)
    if args.down:
        log("==> down（停止并移除容器，保留卷）")
        run(compose_cmd() + ["down", "--remove-orphans"])
        log("Done.")
        return
    log("==> stop: %s" % ", ".join(services))
    stop_stack(services)
    log("Done.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xhs.py", description="XHS-workspace: pack / start / stop")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    pack = sub.add_parser("pack", help="构建镜像并保存 tar 到 dist/docker-images/")
    pack.add_argument("--xhs", action="store_true", help="仅编包 xhs")
    pack.add_argument("--agent-core", action="store_true", dest="agent_core", help="仅编包 agent-core")
    pack.set_defaults(_handler=cmd_pack)

    start = sub.add_parser("start", help="加载 tar 并启动 Docker 服务")
    start.add_argument("--xhs", action="store_true", help="仅启动 xhs")
    start.add_argument("--agent-core", action="store_true", dest="agent_core", help="仅启动 agent-core")
    start.add_argument(
        "--service",
        action="append",
        default=[],
        help="compose 服务名，可重复，例如 --service xhs",
    )
    start.add_argument(
        "--no-kill-host-ports",
        action="store_true",
        help="不尝试释放 8097/8081（默认只结束本机 python xhs/agent-core，不杀 Docker）",
    )
    start.set_defaults(_handler=cmd_start)

    stop = sub.add_parser("stop", help="停止 Docker 服务（默认 compose stop，保留容器）")
    stop.add_argument("--xhs", action="store_true", help="仅停止 xhs")
    stop.add_argument("--agent-core", action="store_true", dest="agent_core", help="仅停止 agent-core")
    stop.add_argument("--service", action="append", default=[], help="compose 服务名，可重复")
    stop.add_argument(
        "--down",
        action="store_true",
        help="compose down（停止并移除全部栈容器，数据卷与 data/xhs 挂载保留）",
    )
    stop.set_defaults(_handler=cmd_stop)

    pw = sub.add_parser(
        "playwright",
        help="本机安装 Playwright + Chromium（手动「热点采集」需要；Docker 用 pack 重建即可）",
    )
    pw.set_defaults(_handler=cmd_playwright)

    login = sub.add_parser(
        "browser-login",
        help="本机登录小红书，导出 browser-storage.json（Docker 热点采集必做一次）",
    )
    login.set_defaults(_handler=cmd_browser_login)

    export = sub.add_parser(
        "browser-export",
        help="从已登录的 browser-profile 导出 browser-storage.json（容器缺文件时用）",
    )
    export.set_defaults(_handler=cmd_browser_export)

    codex = sub.add_parser(
        "codex-copy",
        help="从 AI-workspace（或指定目录）复制 codex-linux，一次性准备 Docker 编包",
    )
    codex.add_argument(
        "--from",
        dest="from_dir",
        default=str(DEFAULT_AIW_CODEX_DIR),
        help="源目录（默认 ../AI-workspace/services/agent-core/deploy/codex-bin）",
    )
    codex.set_defaults(_handler=cmd_codex_copy)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "_handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(2)
    handler(args)


if __name__ == "__main__":
    main()