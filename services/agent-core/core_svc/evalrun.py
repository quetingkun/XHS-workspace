"""固定样例检查一轮对话有没有查知识库、联网，以及回答是否命中要点。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cases(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("eval cases must be a list")
    return data


def check_events(events: list[dict[str, Any]], case: dict[str, Any]) -> list[str]:
    errors = []
    names = []
    for event in events:
        if event.get("type") == "tool.call.started":
            names.append(str((event.get("payload") or {}).get("name") or ""))
    final = ""
    for event in events:
        if event.get("type") == "turn.completed":
            final = str((event.get("payload") or {}).get("final_message") or "")
    if case.get("need_kb") and "mcp__knowledge__search" not in names:
        errors.append("未调用知识库")
    if case.get("need_kb") is False and "mcp__knowledge__search" in names:
        errors.append("不该调用知识库")
    if case.get("need_web") and "mcp__web_search__search" not in names:
        errors.append("未调用联网")
    if case.get("need_web") is False and "mcp__web_search__search" in names:
        errors.append("不该调用联网")
    needle = str(case.get("answer_has") or "")
    if needle and needle not in final:
        errors.append("回答未命中要点")
    if events and events[-1].get("type") != "turn.completed":
        errors.append("这一轮没有完成")
    return errors
