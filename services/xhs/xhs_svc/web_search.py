"""联网检索摘要（可选依赖 duckduckgo-search）。"""

from __future__ import annotations


def web_search_text(query: str, limit: int = 5) -> tuple[str, str | None]:
    text = str(query or "").strip()
    if not text:
        return "", "查询为空"
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "", "未安装 duckduckgo-search，联网不可用（pip install duckduckgo-search）"
    lines: list[str] = []
    try:
        with DDGS() as ddgs:
            for row in ddgs.text(text, max_results=limit):
                title = str(row.get("title") or "").strip()
                body = str(row.get("body") or "").strip()
                href = str(row.get("href") or "").strip()
                if title or body:
                    lines.append("- %s\n  %s\n  %s" % (title, body[:280], href))
    except Exception as exc:  # noqa: BLE001
        return "", "联网检索失败：%s" % str(exc)[:200]
    if not lines:
        return "", "没有检索到结果"
    return "\n".join(lines), None