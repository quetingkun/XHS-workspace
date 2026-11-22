"""官方 Codex app-server：stdio JSON-RPC，只走 initialize / thread / turn。"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Iterator

ALLOWED_SANDBOX = ("read-only", "workspace-write")


class CodexError(RuntimeError):
    pass


class CodexSession:
    def __init__(
        self,
        binary: str,
        home: str,
        cwd: str,
        model: str,
        provider: str,
        expected_sha256: str = "",
        sandbox: str = "read-only",
        approval_mode: str = "never",
    ) -> None:
        self.binary = binary
        self.home = home
        self.cwd = cwd or "."
        self.model = model
        self.provider = provider
        self.expected_sha256 = expected_sha256.strip().lower()
        self.sandbox = (sandbox or "read-only").strip()
        self.approval_mode = (approval_mode or "never").strip()
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self.pending: dict[int, queue.Queue] = {}
        self.notes: queue.Queue = queue.Queue()
        self.next_id = 1
        self.threads: dict[str, str] = {}
        self.ready = False

    def unavailable_reason(self) -> str:
        if self.sandbox not in ALLOWED_SANDBOX:
            return "sandbox_mode %s 不受支持" % self.sandbox
        mismatch = self.sha_error()
        if mismatch:
            return mismatch
        if not self._file_ok():
            return "Codex 二进制不可用"
        return ""

    def sha_error(self) -> str:
        if not self.expected_sha256:
            return ""
        path = Path(self.binary)
        if not path.is_file() or path.stat().st_size == 0:
            return ""
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != self.expected_sha256:
            return "Codex 二进制校验失败"
        return ""

    def runnable(self) -> bool:
        if self.unavailable_reason():
            return False
        return True

    def _file_ok(self) -> bool:
        path = Path(self.binary)
        if not path.is_file() or path.stat().st_size == 0:
            return False
        if path.suffix.lower() == ".py":
            return True
        if os.name == "nt":
            try:
                head = path.read_bytes()[:4]
            except OSError:
                return False
            return not head.startswith(b"\x7fELF")
        return True

    def turn(self, session_id: str, prompt: str, base: str, developer: str) -> Iterator[dict[str, Any]]:
        with self.lock:
            self._ensure()
            thread_id = self.threads.get(session_id)
            if not thread_id:
                started = self._call(
                    "thread/start",
                    {
                        "model": self.model,
                        "modelProvider": self.provider,
                        "cwd": self.cwd,
                        "approvalPolicy": _approval_policy(self.approval_mode),
                        "sandbox": self.sandbox,
                        "baseInstructions": base,
                        "developerInstructions": developer,
                    },
                )
                thread_id = str(((started.get("thread") or {}).get("id")) or "")
                if not thread_id:
                    raise CodexError("codex thread id is empty")
                self.threads[session_id] = thread_id
            while True:
                try:
                    self.notes.get_nowait()
                except queue.Empty:
                    break
            self._call("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": prompt}]})
            answer: list[str] = []
            while True:
                note = self.notes.get(timeout=180)
                method = str(note.get("method") or "")
                params = note.get("params") or {}
                if method == "item/agentMessage/delta":
                    delta = str(params.get("delta") or "")
                    if delta:
                        answer.append(delta)
                        yield {"type": "model.output.delta", "payload": {"delta": delta}}
                elif method == "item/started":
                    yield {"type": "tool.call.started", "payload": {"name": _item_name(params)}}
                elif method == "turn/completed":
                    yield {"type": "turn.completed", "payload": {"final_message": "".join(answer)}}
                    return
                elif method == "error":
                    message = str(params.get("message") or "codex error")
                    yield {"type": "error", "payload": {"message": message}}
                    yield {"type": "turn.failed", "payload": {"message": message}}
                    return

    def close(self) -> None:
        proc = self.proc
        self.proc = None
        self.ready = False
        if proc is None:
            return
        if proc.stdin:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        if proc.stdout:
            proc.stdout.close()

    def _ensure(self) -> None:
        if self.proc and self.proc.poll() is None and self.ready:
            return
        reason = self.unavailable_reason()
        if reason:
            raise CodexError(reason)
        self.close()
        Path(self.home).mkdir(parents=True, exist_ok=True)
        Path(self.cwd).mkdir(parents=True, exist_ok=True)
        argv = _argv(self.binary, self.sandbox, self.approval_mode)
        env = os.environ.copy()
        env["CODEX_HOME"] = str(Path(self.home).resolve())
        env["PYTHONIOENCODING"] = "utf-8"
        self.proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=self.cwd,
            env=env,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        threading.Thread(target=self._read, daemon=True).start()
        self._call("initialize", {"clientInfo": {"name": "ai-workspace-agent-core", "version": "dev"}, "capabilities": {"experimentalApi": False}})
        self._notify("initialized", {})
        self.ready = True

    def _argv(self) -> list[str]:
        return _argv(self.binary, self.sandbox, self.approval_mode)

    def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.proc is None or self.proc.stdin is None:
            raise CodexError("codex process is not running")
        call_id = self.next_id
        self.next_id += 1
        box: queue.Queue = queue.Queue(maxsize=1)
        self.pending[call_id] = box
        self.proc.stdin.write(json.dumps({"id": call_id, "method": method, "params": params}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        try:
            message = box.get(timeout=30)
        except queue.Empty as exc:
            raise CodexError(f"codex {method} timed out") from exc
        finally:
            self.pending.pop(call_id, None)
        if message.get("error"):
            err = message["error"]
            raise CodexError(str(err.get("message") or err))
        result = message.get("result") or {}
        return result if isinstance(result, dict) else {"result": result}

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise CodexError("codex process is not running")
        self.proc.stdin.write(json.dumps({"method": method, "params": params}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _read(self) -> None:
        proc = self.proc
        if proc is None or proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in message and "method" not in message:
                box = self.pending.get(message.get("id"))
                if box is not None:
                    box.put(message)
                continue
            if message.get("method") and "id" in message:
                self._reply(message.get("id"), {})
                continue
            if message.get("method"):
                self.notes.put(message)

    def _reply(self, call_id: Any, result: dict[str, Any]) -> None:
        if self.proc is None or self.proc.stdin is None:
            return
        self.proc.stdin.write(json.dumps({"id": call_id, "result": result}) + "\n")
        self.proc.stdin.flush()


def _approval_policy(mode: str) -> str:
    if mode == "never":
        return "never"
    return "on-request"


def _argv(binary: str, sandbox: str = "read-only", approval_mode: str = "never") -> list[str]:
    shell = "true" if sandbox == "workspace-write" else "false"
    flags = [
        "-c", "approval_policy=%s" % _approval_policy(approval_mode),
        "-c", "sandbox_mode=%s" % sandbox,
        "-c", "shell_environment_policy.inherit=none",
        "-c", "skills.bundled.enabled=false",
        "-c", "features.goals=false",
        "-c", "features.shell_tool=%s" % shell,
        "-c", "features.unified_exec=false",
        "app-server", "--listen", "stdio://", "--strict-config",
    ]
    if binary.lower().endswith(".py"):
        return [sys.executable, binary, *flags]
    return [binary, *flags]


def _item_name(params: dict[str, Any]) -> str:
    item = params.get("item") if isinstance(params.get("item"), dict) else {}
    return str(item.get("name") or item.get("type") or params.get("itemId") or "tool")
