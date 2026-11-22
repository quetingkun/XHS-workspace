"""工作台登录：密码哈希 + 签名 Cookie。"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from pathlib import Path

COOKIE = "xhs_session"
TTL_SEC = 14 * 24 * 3600


class AuthGate:
    def __init__(self, data: Path) -> None:
        self.data = data
        self.data.mkdir(parents=True, exist_ok=True)
        self.user_path = data / "auth.json"
        self.secret_path = data / "auth.secret"
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.secret_path.is_file():
            self.secret_path.write_text(secrets.token_hex(32), encoding="utf-8")
            try:
                self.secret_path.chmod(0o600)
            except OSError:
                pass
        if self.user_path.is_file():
            return
        username = (os.environ.get("XHS_AUTH_USER") or "admin").strip() or "admin"
        password = (os.environ.get("XHS_AUTH_PASSWORD") or "").strip() or "xhs-admin"
        salt = secrets.token_hex(16)
        record = {
            "username": username,
            "salt": salt,
            "password_hash": self._hash(password, salt),
        }
        self.user_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            self.user_path.chmod(0o600)
        except OSError:
            pass
        if not (os.environ.get("XHS_AUTH_PASSWORD") or "").strip():
            print(
                "[xhs] 已创建默认登录 %s / xhs-admin 。公网部署请在 deploy/.env 设置 XHS_AUTH_PASSWORD 后删除 data/xhs/auth.json 再重启。"
                % username,
                flush=True,
            )

    def _secret(self) -> bytes:
        return self.secret_path.read_text(encoding="utf-8").strip().encode("utf-8")

    def _record(self) -> dict:
        return json.loads(self.user_path.read_text(encoding="utf-8"))

    @staticmethod
    def _hash(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()

    def login(self, username: str, password: str) -> tuple[bool, str]:
        rec = self._record()
        user = (username or "").strip()
        if user != str(rec.get("username") or "") or not hmac.compare_digest(
            self._hash(password or "", str(rec.get("salt") or "")),
            str(rec.get("password_hash") or ""),
        ):
            return False, ""
        exp = int(time.time()) + TTL_SEC
        payload = "%s|%s" % (user, exp)
        sig = hmac.new(self._secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        token = "%s|%s" % (payload, sig)
        return True, token

    def user_from_cookie_header(self, header: str | None) -> str:
        if not header:
            return ""
        jar = SimpleCookie()
        try:
            jar.load(header)
        except Exception:
            return ""
        morsel = jar.get(COOKIE)
        if not morsel:
            return ""
        return self._user_from_token(morsel.value)

    def _user_from_token(self, token: str) -> str:
        parts = (token or "").split("|")
        if len(parts) != 3:
            return ""
        user, exp_s, sig = parts
        payload = "%s|%s" % (user, exp_s)
        expect = hmac.new(self._secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, sig):
            return ""
        try:
            exp = int(exp_s)
        except ValueError:
            return ""
        if exp < int(time.time()):
            return ""
        rec = self._record()
        if user != str(rec.get("username") or ""):
            return ""
        return user

    def set_cookie_header(self, token: str) -> str:
        return "%s=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%s" % (COOKIE, token, TTL_SEC)

    def clear_cookie_header(self) -> str:
        return "%s=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0" % COOKIE
