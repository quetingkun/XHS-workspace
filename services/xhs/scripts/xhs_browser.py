"""小红书采集用浏览器配置（专用 profile，勿用正在运行的 Chrome User Data）。"""

from __future__ import annotations

import os
from pathlib import Path

STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]
IGNORE_DEFAULT_ARGS = ["--enable-automation"]

INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
"""


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def running_in_docker() -> bool:
    return Path("/.dockerenv").is_file()


def ignore_https_errors() -> bool:
    """Docker/本机 HTTPS 扫描常导致 Chromium 不信任中间人证书；可用环境变量覆盖。"""
    raw = (os.environ.get("XHS_BROWSER_IGNORE_HTTPS_ERRORS") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return running_in_docker()


def default_profile_dir() -> Path:
    return workspace_root() / "data" / "xhs" / "browser-profile"


def default_storage_state_path() -> Path:
    return workspace_root() / "data" / "xhs" / "browser-storage.json"


def resolve_storage_state(raw: str | None = None) -> str | None:
    """Playwright storage_state（Cookie 等），可在本机登录后给 Docker Chromium 复用。"""
    text = (raw or os.environ.get("XHS_BROWSER_STORAGE_STATE") or "").strip()
    if text:
        path = Path(os.path.expandvars(text))
        if not path.is_absolute():
            path = workspace_root() / path
    else:
        path = default_storage_state_path()
    if path.is_file() and path.stat().st_size > 32:
        return str(path)
    return None


def login_help_message() -> str:
    base = (
        "被重定向到登录页且未抓到笔记。请在项目根执行：python scripts/xhs_browser_login.py "
        "（或 python scripts/xhs.py browser-login），用浏览器完成小红书登录。"
    )
    if running_in_docker():
        return (
            base
            + " 登录后会写入 data/xhs/browser-storage.json，容器内采集自动复用；"
            "勿只复制 Windows Chrome 的 browser-profile 目录给 Linux 容器。"
        )
    return base + " 登录态写入 data/xhs/browser-profile 与 browser-storage.json。"


def resolve_profile(raw: str) -> str:
    text = os.path.expandvars((raw or os.environ.get("XHS_BROWSER_USER_DATA") or "").strip())
    if not text:
        return str(default_profile_dir())
    path = Path(text)
    if not path.is_absolute():
        path = workspace_root() / path
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def effective_channel(*, headed: bool, channel: str | None) -> str | None:
    """Playwright：指定 channel（本机 Chrome）时不能无头；后台采集用内置 Chromium + 同一 profile。"""
    if headed:
        return (channel or "chrome").strip() or "chrome"
    return None


def context_kwargs(*, headed: bool, channel: str | None) -> dict:
    ch = effective_channel(headed=headed, channel=channel)
    args = list(STEALTH_ARGS)
    if not headed:
        args.append("--headless=new")
    if ignore_https_errors():
        args.extend(
            [
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
            ]
        )
    return {
        "headless": not headed,
        "channel": ch,
        "viewport": {"width": 1366, "height": 900},
        "locale": "zh-CN",
        "user_agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            if running_in_docker()
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "ignore_default_args": IGNORE_DEFAULT_ARGS,
        "args": args,
        "ignore_https_errors": ignore_https_errors(),
    }