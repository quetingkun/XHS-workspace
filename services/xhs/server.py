#!/usr/bin/env python3
"""小红书运营服务。只监听本机。"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from xhs_svc.api import App, Error, read_json  # noqa: E402
from xhs_svc.auth_gate import AuthGate  # noqa: E402
from xhs_svc.config import data_dir  # noqa: E402
from xhs_svc.daily_hot import start_auto_hot_refresh  # noqa: E402
from xhs_svc.db import DB  # noqa: E402
from xhs_svc.knowledge import import_approved  # noqa: E402
from xhs_svc.video_download import get_video_download_service  # noqa: E402

WEB = ROOT / "apps" / "web"
DATA = data_dir()
DB_PATH = DATA / "xhs.sqlite"
APP = App(DB(DB_PATH), DATA)
AUTH = AuthGate(DATA)

PUBLIC_API = {
    "/health",
    "/api/xhs/health",
    "/api/xhs/auth/login",
    "/api/xhs/auth/logout",
    "/api/xhs/auth/me",
}
import_approved(APP.db, DATA)
VIDEO_DOWNLOAD = get_video_download_service(DATA)


class Handler(BaseHTTPRequestHandler):
    server_version = "xhs/0.1"

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if self._auth_api(method, parsed.path, raw):
            return
        if parsed.path.startswith("/api/video-download"):
            if VIDEO_DOWNLOAD.handle(self, method, parsed.path, parsed.query, raw):
                return
        if parsed.path.startswith("/api/") or parsed.path == "/health":
            try:
                body = read_json(raw)
                status, payload, headers = APP.handle(method, self.path, body)
            except Error as exc:
                status, payload, headers = exc.status, {"error": exc.message}, None
            except Exception as exc:  # noqa: BLE001
                status, payload, headers = 500, {"error": str(exc)}, None
            self._send(status, payload, headers)
            return
        if parsed.path.startswith("/files/"):
            if not AUTH.user_from_cookie_header(self.headers.get("Cookie")):
                self._send(401, {"error": "请先登录"}, None)
                return
            self._media(parsed.path[len("/files/") :])
            return
        self._file(parsed.path)

    def _auth_api(self, method: str, path: str, raw: bytes) -> bool:
        route = urlparse(path).path.rstrip("/") or "/"
        if route == "/api/xhs/auth/login" and method == "POST":
            try:
                body = read_json(raw)
            except Error as exc:
                self._send(exc.status, {"error": exc.message}, None)
                return True
            ok, token = AUTH.login(str(body.get("username") or ""), str(body.get("password") or ""))
            if not ok:
                self._send(401, {"error": "用户名或密码不正确"}, None)
                return True
            self._send(200, {"ok": True, "username": str(body.get("username") or "").strip()}, {"Set-Cookie": AUTH.set_cookie_header(token)})
            return True
        if route == "/api/xhs/auth/logout" and method == "POST":
            self._send(200, {"ok": True}, {"Set-Cookie": AUTH.clear_cookie_header()})
            return True
        if route == "/api/xhs/auth/me" and method == "GET":
            user = AUTH.user_from_cookie_header(self.headers.get("Cookie"))
            if not user:
                self._send(401, {"error": "请先登录"}, None)
                return True
            self._send(200, {"username": user}, None)
            return True
        protected = route.startswith("/api/") or route == "/health"
        if protected and route not in PUBLIC_API:
            if not AUTH.user_from_cookie_header(self.headers.get("Cookie")):
                self._send(401, {"error": "请先登录"}, None)
                return True
        return False

    def _media(self, rel: str) -> None:
        root = DATA.resolve()
        target = (ROOT / rel).resolve()
        if not target.is_file() or not target.is_relative_to(root):
            self._send(404, {"error": "文件不存在"}, None)
            return
        data = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path: str) -> None:
        rel = path.lstrip("/") or "index.html"
        target = (WEB / rel).resolve()
        if WEB.resolve() not in target.parents and target != WEB.resolve():
            self._send(404, {"error": "路径不存在"}, None)
            return
        if not target.is_file():
            target = WEB / "index.html"
        data = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send(self, status: int, payload: dict | None, headers: dict | None) -> None:
        if status == 204:
            self.send_response(204)
            self.end_headers()
            return
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    host = os.environ.get("XHS_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.environ.get("XHS_PORT", "8097"))
    server = ThreadingHTTPServer((host, port), Handler)
    start_auto_hot_refresh(APP.store)
    print("xhs http://%s:%s" % (host, port), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
