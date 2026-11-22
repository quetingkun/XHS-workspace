"""按配置注册 HTTP MCP，并在对话里发起 tools/call。"""

from __future__ import annotations

import json
from typing import Any

import httpx


class MCPManager:
    def __init__(self, servers: list[dict], client: httpx.Client | None = None) -> None:
        self.servers = {str(item["name"]): item for item in servers if item.get("name") and item.get("url")}
        self._client = client

    def has(self, name: str) -> bool:
        return name in self.servers

    def health(self) -> list[dict[str, Any]]:
        rows = []
        for name, item in self.servers.items():
            ok, detail = self._ping(str(item["url"]))
            rows.append({"name": name, "url": item["url"], "required": bool(item.get("required")), "ok": ok, "detail": detail})
        return rows

    def call(self, name: str, tool: str, arguments: dict[str, Any]) -> str:
        item = self.servers.get(name)
        if item is None:
            raise RuntimeError("mcp server %s 未注册" % name)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        }
        response = self._http().post(str(item["url"]), json=payload, timeout=30)
        if response.status_code >= 300:
            raise RuntimeError("mcp %s http %s" % (name, response.status_code))
        body = response.json()
        if body.get("error"):
            err = body["error"]
            raise RuntimeError(str(err.get("message") or err))
        return _text(body.get("result"))

    def _ping(self, url: str) -> tuple[bool, str]:
        try:
            response = self._http().get(url, timeout=5)
        except httpx.HTTPError as exc:
            return False, str(exc)
        if response.status_code >= 300:
            return False, "http %s" % response.status_code
        return True, ""

    def _http(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        self._client = httpx.Client(timeout=30)
        return self._client


def handle_mcp(body: dict[str, Any], call_tool) -> dict[str, Any]:
    """JSON-RPC：initialize、tools/list、tools/call。"""
    method = str(body.get("method") or "")
    call_id = body.get("id")
    if method in ("initialize", ""):
        return _ok(call_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "ai-workspace", "version": "python"}})
    if method == "tools/list":
        return _ok(
            call_id,
            {
                "tools": [
                    {
                        "name": "search",
                        "description": "search",
                        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
                    }
                ]
            },
        )
    if method == "tools/call":
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        name = str(params.get("name") or "")
        if name != "search":
            return _err(call_id, "unknown tool")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        try:
            text = call_tool(arguments)
        except Exception as exc:  # noqa: BLE001
            return _err(call_id, str(exc))
        return _ok(call_id, {"content": [{"type": "text", "text": text}], "isError": False})
    return _err(call_id, "unknown method")


def _ok(call_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": call_id, "result": result}


def _err(call_id: Any, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": call_id, "error": {"code": -32000, "message": message}}


def _text(result: Any) -> str:
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
            if parts:
                return "\n".join(parts)
        if result.get("text"):
            return str(result["text"])
    return json.dumps(result, ensure_ascii=False)
