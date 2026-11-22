from __future__ import annotations

import os
from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    raw = os.environ.get("XHS_DATA", "").strip()
    path = Path(raw) if raw else workspace_root() / "data" / "xhs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return _parse_yaml(path.read_text(encoding="utf-8"))


def account_config() -> dict:
    data = load_yaml(workspace_root() / "services" / "xhs" / "configs" / "account.yaml")
    account = data.get("account") if isinstance(data.get("account"), dict) else {}
    content = data.get("content") if isinstance(data.get("content"), dict) else {}
    publishing = data.get("publishing") if isinstance(data.get("publishing"), dict) else {}
    style = data.get("style") if isinstance(data.get("style"), dict) else {}
    return {
        "name": str(account.get("name") or ""),
        "positioning": str(account.get("positioning") or "待确定"),
        "target_audience": list(account.get("target_audience") or []),
        "preferred_types": list(content.get("preferred_types") or []),
        "avoid": list(content.get("avoid") or []),
        "tone": str(style.get("tone") or ""),
        "auto_publish": bool(publishing.get("auto_publish")),
    }


def collector_config() -> dict:
    data = load_yaml(workspace_root() / "services" / "xhs" / "configs" / "collectors.yaml")
    collectors = data.get("collectors") if isinstance(data.get("collectors"), dict) else {}
    return collectors


def _parse_yaml(text: str) -> dict:
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            parent = _as_list(stack)
            if isinstance(parent, list):
                parent.append(_scalar(line[2:].strip()))
            continue
        if ":" not in line or not isinstance(parent, dict):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            container: dict = {}
            parent[key] = container
            stack.append((indent, container))
            continue
        parent[key] = _scalar(value)
    return root


def _as_list(stack: list[tuple[int, object]]) -> object:
    container = stack[-1][1]
    if isinstance(container, list) or len(stack) < 2:
        return container
    owner = stack[-2][1]
    if not isinstance(owner, dict):
        return container
    for key, value in owner.items():
        if value is container:
            listed: list = []
            owner[key] = listed
            stack[-1] = (stack[-1][0], listed)
            return listed
    return container


def _scalar(value: str):
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"null", "~", '""', "''"}:
        return "" if value in {'""', "''"} else None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value
