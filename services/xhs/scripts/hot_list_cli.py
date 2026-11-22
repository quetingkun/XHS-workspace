#!/usr/bin/env python3
"""P0 小红书探索页热点：Playwright 真采，失败即 failed/empty，禁止 mock。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from xhs_browser import (
    INIT_SCRIPT,
    context_kwargs,
    ignore_https_errors,
    login_help_message,
    resolve_profile,
    resolve_storage_state,
)


NOTE_IN_HTML = re.compile(r"/(?:explore|search_result)/([a-f0-9]{24})", re.I)

EXPLORE_CHANNELS = (
    "推荐",
    "穿搭",
    "美食",
    "彩妆",
    "影视",
    "职场",
    "情感",
    "家居",
    "游戏",
    "旅行",
    "健身",
    "视频",
)


def emit(payload: dict) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def fail(code: str, message: str) -> int:
    return emit({"status": "failed", "error": {"code": code, "message": message}, "items": []})


def goto_failure_hint(exc: Exception) -> str:
    text = str(exc)
    if "ERR_CERT" in text:
        extra = (
            "。常见于本机杀软/代理对 HTTPS 解密，容器内 Chromium 不信任该证书。"
            "Docker 默认已忽略证书校验；若仍失败请检查容器出网或在 deploy/.env 设 XHS_BROWSER_IGNORE_HTTPS_ERRORS=1 后重启。"
        )
        if not ignore_https_errors():
            extra = "。可在环境变量设 XHS_BROWSER_IGNORE_HTTPS_ERRORS=1 后重试（仅当确认是中间人证书问题）。"
        return extra
    if "ERR_CONNECTION" in text or "ERR_TIMED_OUT" in text or "ERR_NAME_NOT_RESOLVED" in text:
        return "。请确认 Docker 能访问外网（防火墙/代理需对容器放行 xiaohongshu.com）。"
    return ""


def note_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def block_reason(page, item_count: int) -> tuple[str, str] | None:
    if item_count >= 5:
        return None
    url = page.url or ""
    title = (page.title() or "").strip()
    if "website-login/error" in url or title == "安全限制":
        qs = parse_qs(urlparse(url).query)
        msg = unquote(qs.get("error_msg", [""])[0] or "")
        code = qs.get("error_code", [""])[0] or ""
        detail = msg or "小红书拦截了当前访问环境（常见于网络风控或自动化浏览器）"
        if code:
            detail += f"（error_code={code}）"
        return "auth_required", detail
    if "/explore" not in url and "/search_result" not in url and "login" in url:
        return ("auth_required", login_help_message())
    if item_count == 0 and ("登录" in (page.content()[:8000] or "") and "探索" in title):
        return "auth_required", "探索页出现登录引导且未解析到笔记链接，可关闭弹窗后重试或配置 user_data_dir"
    return None


def click_explore_channel(page, category: str) -> None:
    if not category or category == "推荐":
        return
    try:
        for selector in (
            f"#channel-container :text-is('{category}')",
            f"[class*='channel'] :text-is('{category}')",
        ):
            locator = page.locator(selector)
            if locator.count() > 0:
                locator.first.click(timeout=6000)
                page.wait_for_timeout(1200)
                return
        page.get_by_text(category, exact=True).first.click(timeout=6000)
        page.wait_for_timeout(1200)
    except Exception:
        pass


def open_hot_feed(page, keyword: str, category: str) -> None:
    kw = (keyword or "").strip()
    cat = (category or "推荐").strip() or "推荐"
    if kw:
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=%s" % quote(kw),
            wait_until="domcontentloaded",
        )
        page.wait_for_timeout(2500)
        dismiss_login_overlay(page)
        page.wait_for_timeout(800)
        return
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    dismiss_login_overlay(page)
    page.wait_for_timeout(800)
    click_explore_channel(page, cat)


def dismiss_login_overlay(page) -> None:
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception:
        pass
    try:
        page.evaluate(
            """() => {
  const click = (el) => { if (el) { el.dispatchEvent(new MouseEvent("click", { bubbles: true })); return true; } return false; };
  const close =
    document.querySelector('[class*="close-icon"], [class*="closeIcon"], [class*="reds-icon-close"], [class*="icon-close"]') ||
    document.querySelector('svg[class*="close"]')?.closest("div,button,span");
  if (click(close)) return;
  const mask = document.querySelector('[class*="mask"][class*="login"], .login-modal, [class*="login-modal"]');
  if (mask) {
    const inner = mask.querySelector('[class*="close"], button');
    click(inner);
  }
}"""
        )
        page.wait_for_timeout(600)
    except Exception:
        pass


def extract_state_items(page, limit: int) -> list[dict]:
    try:
        raw = page.evaluate(
            """(limit) => {
  const items = [];
  const seen = new Set();
  const skipKeys = new Set(["dep", "computed", "activeLink", "sub", "subs", "effects", "_value", "_rawValue"]);
  const noteIdOk = (id) => {
    const s = String(id || "");
    return s.length >= 16 && /^[a-f0-9]+$/i.test(s);
  };
  const walk = (node, depth) => {
    if (depth > 16 || items.length >= limit) return;
    if (!node || typeof node !== "object") return;
    if (Array.isArray(node)) {
      for (const v of node) walk(v, depth + 1);
      return;
    }
    const noteId = node.noteId || node.note_id;
    const title = node.displayTitle || node.title || node.desc || node.name;
    let url = node.url || node.noteUrl || node.link;
    if (noteIdOk(noteId) && !url) url = `https://www.xiaohongshu.com/explore/${noteId}`;
    if (typeof url === "string" && (url.includes("/explore/") || url.includes("/search_result/"))) {
      url = url.split("?")[0];
      const t = String(title || "").trim();
      if (!seen.has(url) && (t.length >= 2 || noteIdOk(noteId))) {
        seen.add(url);
        items.push({ href: url, title: t, note_id: String(noteId || "") });
      }
    }
    for (const key of Object.keys(node)) {
      if (skipKeys.has(key)) continue;
      try { walk(node[key], depth + 1); } catch (_) {}
    }
  };
  if (window.__INITIAL_STATE__) walk(window.__INITIAL_STATE__, 0);
  return items;
}""",
            limit,
        )
    except Exception:
        return []
    return _rows_to_items(raw, limit)


def extract_dom_items(page, limit: int) -> list[dict]:
    raw_links = page.evaluate(
        """() => {
  const out = [];
  const seen = new Set();
  const nodes = document.querySelectorAll('a[href*="/explore/"], section a[href*="/search_result/"]');
  for (const a of nodes) {
    let href = a.href || "";
    if (!href.includes("/explore/") && !href.includes("/search_result/")) continue;
    href = href.split("?")[0];
    if (seen.has(href)) continue;
    seen.add(href);
    const card = a.closest("section, article, [class*='note'], [class*='feed']") || a;
    let title = (card.querySelector(".title, [class*='title'], footer span")?.textContent || a.innerText || "").replace(/\\s+/g, " ").trim();
    if ((!title || title.length < 2) && a.getAttribute("title")) title = a.getAttribute("title");
    const img = a.querySelector("img[alt]");
    if ((!title || title.length < 2) && img) title = (img.getAttribute("alt") || "").trim();
    out.push({ href, title });
  }
  return out;
}"""
    )
    return _rows_to_items(raw_links, limit)


def extract_html_items(html: str, limit: int) -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    for match in NOTE_IN_HTML.finditer(html):
        note_id = match.group(1)
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if url in seen:
            continue
        seen.add(url)
        items.append(
            {
                "platform": "xiaohongshu",
                "note_id": note_id,
                "title": f"探索笔记 {note_id[:8]}",
                "url": url,
            }
        )
        if len(items) >= limit:
            break
    return items


def _rows_to_items(rows, limit: int) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for row in rows or []:
        url = str(row.get("href") or row.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        title = str(row.get("title") or "").strip()
        note_id = str(row.get("note_id") or "") or note_from_url(url)
        if len(title) < 2:
            title = f"探索笔记 {note_id[:8]}"
        items.append({"platform": "xiaohongshu", "note_id": note_id, "title": title[:200], "url": url})
        if len(items) >= limit:
            break
    return items


def merge_items(*groups: list[dict], limit: int) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for group in groups:
        for row in group:
            if row["url"] in seen:
                continue
            seen.add(row["url"])
            out.append(row)
            if len(out) >= limit:
                return out
    return out


def save_debug(page, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    html = page.content()
    (data_dir / "hot-last-title.txt").write_text(f"title={page.title()}\nurl={page.url}", encoding="utf-8")
    (data_dir / "hot-last.html").write_text(html[:800000], encoding="utf-8")
    page.screenshot(path=str(data_dir / "hot-last.png"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--channel", default="chrome", help="Playwright channel：chrome / msedge")
    parser.add_argument("--headed", action="store_true", help="有头模式，便于本地调试")
    parser.add_argument("--user-data-dir", default="", help="专用配置目录，默认 data/xhs/browser-profile")
    parser.add_argument("--ephemeral", action="store_true", help="不使用 profile，仅测试免登录（易被风控）")
    parser.add_argument("--debug", action="store_true", help="保存最后一次页面到 data/xhs/collector-raw/")
    parser.add_argument("--keyword", default="", help="非空时走搜索页采集，忽略频道 Tab")
    parser.add_argument(
        "--category",
        default="推荐",
        help="探索页频道 Tab（默认推荐），无关键词时生效",
    )
    args = parser.parse_args()
    top_n = max(5, min(args.top, 30))
    profile_dir = "" if args.ephemeral else resolve_profile(args.user_data_dir)
    debug_dir = Path(__file__).resolve().parents[3] / "data" / "xhs" / "collector-raw"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return fail(
            "browser_unavailable",
            "未安装 playwright。本机：python scripts/xhs.py playwright；Docker：python scripts/xhs.py pack && start",
        )

    def launch_profile(playwright, profile: str):
        kwargs = context_kwargs(headed=args.headed, channel=args.channel)
        try:
            return playwright.chromium.launch_persistent_context(profile, **kwargs)
        except Exception as exc:
            if args.headed:
                raise
            text = str(exc)
            if "Executable doesn't exist" in text or "playwright install" in text.lower():
                off = context_kwargs(headed=True, channel=args.channel)
                off["args"] = list(off["args"]) + [
                    "--headless=new",
                    "--window-position=-32000,-32000",
                    "--window-size=900,700",
                ]
                return playwright.chromium.launch_persistent_context(profile, **off)
            raise

    page = None
    browser = None
    context = None
    storage_state = resolve_storage_state() if not args.ephemeral else None
    if not args.ephemeral and not storage_state:
        from xhs_browser import running_in_docker

        hint = login_help_message()
        if running_in_docker():
            hint = (
                "容器内未找到 data/xhs/browser-storage.json。"
                "请在本机项目根执行：python scripts/xhs.py browser-export"
                "（若未登录则先 browser-login），再重试热点采集。"
            )
        return fail("auth_required", hint)
    try:
        with sync_playwright() as playwright:
            kwargs = context_kwargs(headed=args.headed, channel=args.channel)
            if storage_state:
                try:
                    browser = playwright.chromium.launch(
                        headless=not args.headed,
                        channel=kwargs.get("channel"),
                        ignore_default_args=kwargs["ignore_default_args"],
                        args=kwargs["args"],
                    )
                except Exception as exc:
                    return fail(
                        "browser_unavailable",
                        f"{exc}。请安装 Chrome/Edge，或执行 python -m playwright install chromium",
                    )
                context = browser.new_context(
                    viewport=kwargs["viewport"],
                    locale=kwargs["locale"],
                    user_agent=kwargs["user_agent"],
                    ignore_https_errors=kwargs.get("ignore_https_errors", False),
                    storage_state=storage_state,
                )
                page = context.new_page()
            elif profile_dir:
                context = launch_profile(playwright, profile_dir)
                page = context.pages[0] if context.pages else context.new_page()
            else:
                try:
                    browser = playwright.chromium.launch(
                        headless=not args.headed,
                        channel=kwargs.get("channel"),
                        ignore_default_args=kwargs["ignore_default_args"],
                        args=kwargs["args"],
                    )
                except Exception as exc:
                    return fail(
                        "browser_unavailable",
                        f"{exc}。请安装 Chrome/Edge，或执行 python -m playwright install chromium",
                    )
                context = browser.new_context(
                    viewport=kwargs["viewport"],
                    locale=kwargs["locale"],
                    user_agent=kwargs["user_agent"],
                    ignore_https_errors=kwargs.get("ignore_https_errors", False),
                )
                page = context.new_page()
            page.add_init_script(INIT_SCRIPT)

            page.set_default_timeout(120000)
            category = (args.category or "推荐").strip() or "推荐"
            if category not in EXPLORE_CHANNELS:
                category = "推荐"
            keyword = (args.keyword or "").strip()
            try:
                open_hot_feed(page, keyword, category)
                for _ in range(5):
                    page.mouse.wheel(0, 1400)
                    page.wait_for_timeout(1000)
            except Exception as exc:
                if args.debug and page:
                    save_debug(page, debug_dir)
                label = "搜索页" if (keyword or "").strip() else "探索页"
                return fail("failed", f"无法打开小红书{label}：{exc}{goto_failure_hint(exc)}")

            html = page.content()
            items = merge_items(
                extract_state_items(page, top_n),
                extract_dom_items(page, top_n),
                extract_html_items(html, top_n),
                limit=top_n,
            )
            blocked = block_reason(page, len(items))
            if blocked:
                if args.debug:
                    save_debug(page, debug_dir)
                code, message = blocked
                return fail(code, message)
            if args.debug:
                save_debug(page, debug_dir)
            if browser:
                browser.close()
            elif context:
                context.close()
    except Exception as exc:
        return fail("failed", str(exc))

    if len(items) < 5:
        return fail(
            "empty",
            "只解析到 %s 条（需要 ≥5）。若浏览器能手动打开探索页但仍失败，可配置 user_data_dir 复用已登录 Chrome。"
            % len(items),
        )
    return emit(
        {
            "status": "ok",
            "source": "browser",
            "session_kind": "ephemeral" if args.ephemeral else "profile",
            "login_free": True,
            "query": {"keyword": keyword, "category": category},
            "items": items[:top_n],
        }
    )


if __name__ == "__main__":
    sys.exit(main())