"""联网搜索：Tavily，然后百度，然后 Bing。"""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

import httpx

_TAG = re.compile(r"<[^>]+>")
_BING = re.compile(r'(?is)<li class="b_algo"[\s\S]*?<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>')
_BING_SNIP = re.compile(r'(?is)<p class="b_lineclamp[^"]*">([\s\S]*?)</p>')
_BAIDU = re.compile(r'(?is)<h3[^>]*class="[^"]*t[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>')
_BAIDU_SNIP = re.compile(r'(?is)<span class="content-right_[^"]*">([\s\S]*?)</span>')


class WebSearch:
    def __init__(self) -> None:
        self.max_results = 5
        raw = os.environ.get("WEB_SEARCH_MAX_RESULTS", "").strip()
        if raw.isdigit() and 1 <= int(raw) <= 10:
            self.max_results = int(raw)
        self.tavily_key = os.environ.get("TAVILY_API_KEY", "").strip()

    def search(self, query: str) -> dict[str, Any]:
        query = query.strip()
        if not query:
            return {"ok": False, "error": "搜索查询不能为空"}
        if self.tavily_key:
            found = self._tavily(query)
            if found.get("ok"):
                return found
        for source in ("baidu", "bing"):
            found = self._html(source, query)
            if found.get("ok"):
                return found
        return {"ok": False, "error": "联网搜索不可用"}

    def _tavily(self, query: str) -> dict[str, Any]:
        try:
            res = httpx.post("https://api.tavily.com/search", json={"api_key": self.tavily_key, "query": query, "max_results": self.max_results}, timeout=18)
        except httpx.HTTPError as exc:
            return {"ok": False, "error": str(exc)}
        if res.status_code >= 300:
            return {"ok": False, "error": f"http {res.status_code}"}
        data = res.json()
        parts = [str(data.get("answer") or "").strip()]
        for item in (data.get("results") or [])[: self.max_results]:
            parts.append(f"{item.get('title') or ''}\n{item.get('content') or ''}")
        text = "\n\n".join(part for part in parts if part)
        return {"ok": True, "content": text} if text else {"ok": False, "error": "未找到结果"}

    def _html(self, source: str, query: str) -> dict[str, Any]:
        if source == "bing":
            url = "https://cn.bing.com/search?q=" + quote(query) + "&setlang=zh-CN"
            link_re, snip_re = _BING, _BING_SNIP
        else:
            url = "https://www.baidu.com/s?wd=" + quote(query)
            link_re, snip_re = _BAIDU, _BAIDU_SNIP
        try:
            res = httpx.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-CN,zh;q=0.9"}, timeout=18, follow_redirects=True)
        except httpx.HTTPError as exc:
            return {"ok": False, "error": str(exc)}
        if res.status_code >= 300:
            return {"ok": False, "error": f"http {res.status_code}"}
        links = link_re.findall(res.text)[: self.max_results]
        snips = snip_re.findall(res.text)
        if not links:
            return {"ok": False, "error": "未解析到结果"}
        parts = []
        for index, match in enumerate(links):
            snip = _strip(snips[index]) if index < len(snips) else ""
            parts.append(f"[{index + 1}] {_strip(match[1])}\n{snip}")
        return {"ok": True, "content": "\n\n".join(parts)}


def _strip(value: str) -> str:
    return " ".join(_TAG.sub("", value).split())
