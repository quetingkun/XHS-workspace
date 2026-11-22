#!/usr/bin/env python3
"""可选：从外部 HTTP 触发采集（服务内已按日自动补采，一般不必跑）。"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "xhs"))

HOST = os.environ.get("XHS_HOST", "127.0.0.1")
PORT = int(os.environ.get("XHS_PORT", "8097"))


def post_hot_collect(
    host: str | None = None,
    port: int | None = None,
    timeout: float = 300,
    *,
    print_json: bool = True,
) -> tuple[int, dict | None]:
    host = host or HOST
    port = port if port is not None else PORT
    url = f"http://{host}:{port}/api/xhs/collect"
    body = json.dumps({"capability": "hot_list"}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(detail or exc, file=sys.stderr)
        return 1, None
    except OSError as exc:
        print("无法连接 %s，请先 python scripts/redeploy.py" % url, file=sys.stderr)
        print(exc, file=sys.stderr)
        return 1, None
    if print_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    status = str(data.get("status") or "")
    if status in {"ok", "partial"}:
        return 0, data
    return 2, data


def main() -> int:
    code, _ = post_hot_collect()
    return code


if __name__ == "__main__":
    sys.exit(main())