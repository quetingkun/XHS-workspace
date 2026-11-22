#!/usr/bin/env python3
"""从已登录的 browser-profile 导出 browser-storage.json（供 Docker Chromium 复用）。"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "xhs" / "scripts"))

from xhs_browser import INIT_SCRIPT, context_kwargs, default_storage_state_path, resolve_profile  # noqa: E402


def page_looks_logged_in(page) -> bool:
    url = page.url or ""
    if "website-login/error" in url:
        return False
    if "login" in url.lower() and "/explore" not in url and "/search_result" not in url:
        try:
            html = (page.content() or "")[:16000]
        except Exception:
            return False
        if "/explore/" not in html and "search_result" not in html:
            return False
    return True


def export_storage(ctx, state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.storage_state(path=str(state_path))


def main() -> int:
    from playwright.sync_api import sync_playwright

    profile = resolve_profile("")
    state_path = default_storage_state_path()
    print("从专用 profile 导出登录态（本机执行，写入挂载目录）：")
    print("  profile:", profile)
    print("  output:", state_path)

    kwargs = context_kwargs(headed=True, channel="chrome")
    kwargs["args"] = list(kwargs["args"]) + [
        "--window-position=80,40",
        "--window-size=1100,800",
    ]

    with sync_playwright() as playwright:
        try:
            ctx = playwright.chromium.launch_persistent_context(profile, **kwargs)
        except Exception as exc:
            print("无法打开 profile：", exc, file=sys.stderr)
            print("请先：python scripts/xhs.py browser-login", file=sys.stderr)
            return 1
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.add_init_script(INIT_SCRIPT)
        page.set_default_timeout(120000)
        try:
            page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(2500)
        except Exception as exc:
            print("打开探索页失败：", exc, file=sys.stderr)
            ctx.close()
            return 1

        if not page_looks_logged_in(page):
            ctx.close()
            print("profile 未登录或已失效，请重新：python scripts/xhs.py browser-login", file=sys.stderr)
            return 1

        print("检测到已打开探索页，正在导出（请勿手动关闭浏览器窗口）…")
        try:
            export_storage(ctx, state_path)
        except Exception as exc:
            text = str(exc)
            if "closed" in text.lower():
                print(
                    "导出时浏览器已关闭。请重新运行本命令，并在整个过程中保持弹出的 Chrome 窗口打开。",
                    file=sys.stderr,
                )
            else:
                print("导出失败：", exc, file=sys.stderr)
            try:
                ctx.close()
            except Exception:
                pass
            return 1
        try:
            ctx.close()
        except Exception:
            pass

    if not state_path.is_file() or state_path.stat().st_size < 64:
        print("导出失败：文件过小或不存在", file=sys.stderr)
        return 1
    print("完成，大小 %s 字节。Docker 内热点采集将自动使用该文件。" % state_path.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())