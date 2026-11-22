"""代理本机 agent-core 的引擎路由（/v1/engine/routing）。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


GO_ENGINE = "agent-core"
CODEX_ENGINE = "codex"


def agent_core_base() -> str:
    return os.environ.get("AGENT_CORE_URL", "http://127.0.0.1:8081").rstrip("/")


def routing_fallback(message: str = "") -> dict[str, Any]:
    return {
        "default_engine": GO_ENGINE,
        "function_defaults": {},
        "functions": [
            {
                "function_id": "xhs_ops",
                "name": "小红书运营助手",
                "engine": GO_ENGINE,
                "inherited": True,
            }
        ],
        "engines": [
            {"name": GO_ENGINE, "default": True, "available": False, "enabled": True, "version": "python"},
            {"name": CODEX_ENGINE, "default": False, "available": False, "enabled": False, "version": ""},
        ],
        "allow_override": True,
        "allow_write_turns": False,
        "offline": True,
        "error": message or "agent-core 未启动或不可达",
    }


def fetch_routing() -> dict[str, Any]:
    url = agent_core_base() + "/v1/engine/routing"
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return routing_fallback(str(exc))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return routing_fallback("agent-core 返回无效 JSON")
    if not isinstance(data, dict):
        return routing_fallback("agent-core 路由格式错误")
    data.setdefault("default_engine", GO_ENGINE)
    data["offline"] = False
    return data


def update_routing(body: dict[str, Any]) -> dict[str, Any]:
    default = str(body.get("default_engine") or GO_ENGINE).strip()
    if default not in {GO_ENGINE, CODEX_ENGINE}:
        raise ValueError("default_engine 必须是 agent-core 或 codex")
    payload: dict[str, Any] = {
        "default_engine": default,
        "function_defaults": dict(body.get("function_defaults") or {}),
    }
    payload["function_defaults"]["xhs_ops"] = default
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = agent_core_base() + "/v1/engine/routing"
    request = urllib.request.Request(
        url,
        data=raw,
        method="PUT",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError("agent-core 保存失败：HTTP %s %s" % (exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("agent-core 未启动，无法保存引擎设置：%s" % exc) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("agent-core 返回无效 JSON") from exc
    if not isinstance(data, dict):
        raise RuntimeError("agent-core 路由格式错误")
    data["offline"] = False
    return data


def engine_selectable(routing: dict[str, Any] | None, name: str) -> bool:
    if name == GO_ENGINE:
        return True
    if not routing:
        return False
    for item in routing.get("engines") or []:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("enabled")) and bool(item.get("available"))
    return False