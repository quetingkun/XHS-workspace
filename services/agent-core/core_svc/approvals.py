"""敏感工具调用暂停，等 POST /v1/approvals/{id} 之后继续。"""

from __future__ import annotations

import threading
import uuid
from typing import Any


class ApprovalGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}

    def request(self, name: str, detail: str) -> str:
        approval_id = "ap_" + uuid.uuid4().hex[:12]
        with self._lock:
            self._pending[approval_id] = {
                "id": approval_id,
                "name": name,
                "detail": detail,
                "event": threading.Event(),
                "decision": "",
            }
        return approval_id

    def decide(self, approval_id: str, decision: str) -> bool:
        if decision not in ("approve", "deny"):
            return False
        with self._lock:
            item = self._pending.get(approval_id)
            if item is None or item.get("decision"):
                return False
            item["decision"] = decision
            item["event"].set()
        return True

    def wait(self, approval_id: str, timeout: float = 120) -> str:
        with self._lock:
            item = self._pending.get(approval_id)
        if item is None:
            return "deny"
        item["event"].wait(timeout)
        with self._lock:
            decision = str(item.get("decision") or "deny")
            self._pending.pop(approval_id, None)
        return decision

    def pending(self) -> list[dict[str, str]]:
        with self._lock:
            return [{"id": item["id"], "name": item["name"], "detail": item["detail"]} for item in self._pending.values() if not item.get("decision")]


def needs_approval(mode: str, name: str, trusted: list[str]) -> bool:
    if mode == "never":
        return False
    if mode == "unless-trusted" and name in set(trusted):
        return False
    return mode in ("on-request", "unless-trusted")
