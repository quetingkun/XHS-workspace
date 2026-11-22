#!/usr/bin/env python3
"""一键重启小红书运营台：释放端口 → 可选跑测试 → 后台拉起 server。"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "services" / "xhs" / "server.py"
AGENT_CORE = ROOT / "services" / "agent-core" / "server.py"
LOG_DIR = ROOT / "logs"
DEFAULT_PORT = 8097
AGENT_CORE_PORT = int(os.environ.get("AGENT_CORE_PORT", "8081"))


def pids_listening_on(port: int) -> list[int]:
    if os.name != "nt":
        try:
            out = subprocess.check_output(["ss", "-ltnp"], text=True, errors="replace")
        except (OSError, subprocess.CalledProcessError):
            out = subprocess.check_output(["lsof", "-i", f":{port}", "-sTCP:LISTEN"], text=True, errors="replace")
        pids: list[int] = []
        for line in out.splitlines():
            if f":{port}" not in line:
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
    needle = f":{port}"
    for line in out.splitlines():
        if "LISTENING" not in line or needle not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pids.append(int(parts[-1]))
        except ValueError:
            continue
    return sorted(set(pids))


def stop_listeners(port: int) -> list[int]:
    killed: list[int] = []
    for pid in pids_listening_on(port):
        if pid == os.getpid():
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
    return killed


def run_tests() -> None:
    print("运行测试 tests/test_xhs.py …", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests" / "test_xhs.py"), "-q"],
        cwd=ROOT,
        check=True,
    )


def start_agent_core(port: int) -> int | None:
    if not AGENT_CORE.is_file():
        print("未找到 agent-core，跳过 :%s" % port, flush=True)
        return None
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "agent-core.log"
    print(f"后台启动 agent-core http://127.0.0.1:{port}", flush=True)
    print(f"日志：{log_path}", flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n--- redeploy %s ---\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(
            [
                sys.executable,
                "server.py",
                "--addr",
                ":%s" % port,
                "--workspace-root",
                str(ROOT),
            ],
            cwd=ROOT / "services" / "agent-core",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    deadline = time.time() + 12
    while time.time() < deadline:
        if pids_listening_on(port):
            print("agent-core 端口已监听。", flush=True)
            return proc.pid
        time.sleep(0.25)
    print("agent-core 已启动子进程，但端口尚未就绪，请查看 logs/agent-core.log。", flush=True)
    return proc.pid


def start_server(port: int, foreground: bool) -> int:
    if not SERVER.is_file():
        raise SystemExit(f"找不到服务入口：{SERVER}")
    env = os.environ.copy()
    env["XHS_PORT"] = str(port)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if foreground:
        print(f"前台启动 xhs http://127.0.0.1:{port}", flush=True)
        os.chdir(ROOT)
        os.execve(sys.executable, [sys.executable, str(SERVER)], env)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "xhs-server.log"
    print(f"后台启动 xhs http://127.0.0.1:{port}", flush=True)
    print(f"日志：{log_path}", flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n--- redeploy %s ---\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(
            [sys.executable, str(SERVER)],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    deadline = time.time() + 8
    while time.time() < deadline:
        if pids_listening_on(port):
            print("端口已监听，就绪。", flush=True)
            return proc.pid
        time.sleep(0.25)
    print("已启动子进程，但端口尚未就绪，请查看日志。", flush=True)
    return proc.pid


def main() -> None:
    parser = argparse.ArgumentParser(description="一键重启 XHS-workspace 本机服务")
    parser.add_argument("--port", type=int, default=int(os.environ.get("XHS_PORT", DEFAULT_PORT)))
    parser.add_argument(
        "--no-agent-core",
        action="store_true",
        help="不启动本仓库 services/agent-core（默认与 xhs 一并拉起）",
    )
    parser.add_argument(
        "--agent-core-port",
        type=int,
        default=AGENT_CORE_PORT,
        help="agent-core 监听端口（默认 %s）" % AGENT_CORE_PORT,
    )
    parser.add_argument("--no-stop", action="store_true", help="不结束已占用端口的进程")
    parser.add_argument("--test", action="store_true", help="启动前先跑 pytest")
    parser.add_argument("--foreground", action="store_true", help="前台运行（占用当前终端）")
    args = parser.parse_args()

    os.chdir(ROOT)
    if not args.no_stop:
        stopped = stop_listeners(args.port)
        if stopped:
            print("已结束占用 %s 的进程：%s" % (args.port, ", ".join(map(str, stopped))), flush=True)
        else:
            print("端口 %s 未被占用。" % args.port, flush=True)
        if not args.no_agent_core:
            stopped_ac = stop_listeners(args.agent_core_port)
            if stopped_ac:
                print(
                    "已结束占用 agent-core %s 的进程：%s"
                    % (args.agent_core_port, ", ".join(map(str, stopped_ac))),
                    flush=True,
                )

    if args.test:
        run_tests()

    if args.foreground:
        if not args.no_agent_core:
            print("前台模式仅启动 xhs；agent-core 请另开终端运行 services/agent-core/server.py", flush=True)
        start_server(args.port, args.foreground)
        return
    start_server(args.port, False)
    if not args.no_agent_core:
        start_agent_core(args.agent_core_port)


if __name__ == "__main__":
    main()