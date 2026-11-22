#!/usr/bin/env python3
"""一次性登录：在专用 Chrome 配置目录里登录小红书，供热点采集复用。"""

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

from xhs_browser import context_kwargs, default_storage_state_path, resolve_profile  # noqa: E402


def main() -> int:
    from playwright.sync_api import sync_playwright

    profile = resolve_profile("")
    print("专用配置目录（勿与日常 Chrome 同时占用）：")
    print(profile)
    print()
    print("将打开探索页。请扫码或手机号登录，确认能看到推荐笔记后，回到终端按 Enter。")

    with sync_playwright() as playwright:
        ctx = playwright.chromium.launch_persistent_context(profile, **context_kwargs(headed=True, channel="chrome"))
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.add_init_script(
            """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
"""
        )
        try:
            page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=120000)
        except Exception as exc:
            print("打开失败：", exc, file=sys.stderr)
        input("\n登录并确认探索页正常后，按 Enter 保存 Cookie（按 Enter 前不要关浏览器）…")
        state_path = default_storage_state_path()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            ctx.storage_state(path=str(state_path))
        except Exception as exc:
            if "closed" in str(exc).lower():
                print("浏览器已关闭，无法保存。请重新 browser-login 并在按 Enter 前保持窗口打开。", file=sys.stderr)
            else:
                print("保存失败：", exc, file=sys.stderr)
            return 1
        size = state_path.stat().st_size if state_path.is_file() else 0
        ctx.close()

    if not state_path.is_file() or size < 64:
        print("未写入 browser-storage.json，请确认已登录并按 Enter。", file=sys.stderr)
        return 1
    print("已关闭。登录态已写入：")
    print(" ", state_path, "（%s 字节，Docker 采集优先复用）" % size)
    print("  ", profile)
    print("若 Docker 仍提示登录，可再执行：python scripts/xhs.py browser-export")
    print("之后采集：页面「热点采集」，或 python services/xhs/scripts/hot_list_cli.py --top 10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())