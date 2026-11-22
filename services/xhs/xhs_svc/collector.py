from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

import sys

from xhs_svc.config import collector_config, workspace_root
from xhs_svc.db import dumps, new_id, now

_WIN_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0


def _subprocess_run_kwargs() -> dict:
    if os.name != "nt":
        return {}
    return {"creationflags": _WIN_NO_WINDOW}


CAPABILITIES = (
    "hot_list",
    "daily_rank",
    "search",
    "note_detail",
    "comments",
    "media_archive",
)

ROUTES = {
    "hot_list": "hot_daily",
    "daily_rank": "daily_top",
    "search": "media_crawler",
    "note_detail": "media_crawler",
    "comments": "media_crawler",
    "media_archive": "xhs_downloader",
}

NAMES = {
    "hot_daily": "xiaohongshu-hot-daily",
    "daily_top": "xiaohongshu-dailytop",
    "media_crawler": "MediaCrawler",
    "xhs_downloader": "XHS-Downloader",
}

USABLE = {"ok", "partial"}


def collect(query: dict, data: Path, config: dict | None = None) -> dict:
    capability = str(query.get("capability") or "")
    if capability not in CAPABILITIES:
        return _result("", capability, "source_unavailable", query, code="source_unavailable", message="未知能力")
    key = ROUTES[capability]
    cfg = (config if config is not None else collector_config()).get(key) or {}
    if not isinstance(cfg, dict):
        cfg = {}
    probe = str(query.get("probe") or "")
    if probe in {"browser_unavailable", "mock_data"}:
        return _result(
            NAMES[key],
            capability,
            "failed",
            query,
            code=probe,
            message="浏览器不可用" if probe == "browser_unavailable" else "输出是模拟数据",
        )
    if key == "agent_reach" or not cfg.get("enabled"):
        return _result(NAMES[key], capability, "source_unavailable", query, code="source_unavailable", message="采集器未启用")
    if capability == "daily_rank":
        return _daily_top(cfg, query, data)
    if capability == "media_archive":
        return _archive(cfg, query, data)
    return _from_command(NAMES[key], capability, cfg, query, data, collector_key=key)


def usable_items(result: dict) -> list[dict]:
    if result.get("status") not in USABLE:
        return []
    good = []
    for item in result.get("items") or []:
        if item.get("title") and item.get("url"):
            item["login_free"] = result.get("login_free", True)
            good.append(item)
    return good


def _daily_top(cfg: dict, query: dict, data: Path) -> dict:
    hops = []
    by_source: dict[str, dict] = {}
    commands = cfg.get("commands") if isinstance(cfg.get("commands"), dict) else {}
    for source in list(cfg.get("fallback") or ["redfox", "custom_api", "playwright"]):
        hop_query = dict(query)
        hop_query["source"] = source
        hop = _from_command(
            "xiaohongshu-dailytop",
            "daily_rank",
            {"command": str(commands.get(source) or ""), "timeout": cfg.get("timeout") or 60},
            hop_query,
            data,
            source_name=source,
        )
        by_source[source] = hop
        hops.append({"source": source, "status": hop["status"], "error": hop.get("error"), "count": len(hop.get("items") or [])})
    playwright = by_source.get("playwright")
    if playwright and playwright["status"] in USABLE:
        playwright["hops"] = hops
        playwright["login_free"] = True
        return playwright
    for source in list(cfg.get("fallback") or []):
        if source == "playwright":
            continue
        hop = by_source.get(source)
        if hop and hop["status"] in USABLE:
            hop["hops"] = hops
            hop["login_free"] = False
            return hop
    failed = _result(
        "xiaohongshu-dailytop",
        "daily_rank",
        "failed",
        query,
        code="browser_unavailable",
        message="Playwright 没有在免登录条件下返回真实笔记",
    )
    failed["hops"] = hops
    failed["login_free"] = False
    return failed


def _archive(cfg: dict, query: dict, data: Path) -> dict:
    result = _from_command("XHS-Downloader", "media_archive", cfg, query, data)
    if result["status"] not in USABLE:
        return result
    kept = []
    for item in result.get("items") or []:
        files = []
        for media in item.get("media_files") or []:
            rel = str(media.get("relative_path") or "")
            if not rel or rel.startswith("..") or Path(rel).is_absolute():
                continue
            files.append({"type": media.get("type") or "image", "relative_path": rel.replace("\\", "/")})
        if files:
            item["media_files"] = files
            kept.append(item)
    result["items"] = kept
    if not kept:
        result["status"] = "failed"
        result["error"] = {"code": "failed", "message": "没有可保存的相对路径"}
    return result


def _build_argv(collector_key: str, cfg: dict, query: dict | None = None) -> list[str] | None:
    raw = str(cfg.get("command") or "").strip()
    if raw:
        parts = shlex.split(raw, posix=False) if os.name == "nt" else shlex.split(raw)
        if parts and parts[0] in {"python", "python3"}:
            parts[0] = sys.executable
        if len(parts) >= 2 and not Path(parts[1]).is_absolute():
            candidate = workspace_root() / parts[1]
            if candidate.is_file():
                parts[1] = str(candidate)
        return parts
    if not cfg.get("enabled") or collector_key != "hot_daily":
        return None
    script = workspace_root() / "services" / "xhs" / "scripts" / "hot_list_cli.py"
    if not script.is_file():
        return None
    top = int(cfg.get("top_n") or 15)
    channel = str(cfg.get("browser_channel") or "chrome").strip() or "chrome"
    argv = [sys.executable, str(script), "--top", str(top), "--channel", channel]
    user_data = str(cfg.get("user_data_dir") or os.environ.get("XHS_BROWSER_USER_DATA") or "").strip()
    if user_data:
        argv.extend(["--user-data-dir", user_data])
    if cfg.get("use_headed"):
        argv.append("--headed")
    q = query or {}
    keyword = str(q.get("keyword") or cfg.get("default_keyword") or "").strip()
    category = str(q.get("category") or cfg.get("default_category") or "推荐").strip() or "推荐"
    if keyword:
        argv.extend(["--keyword", keyword])
    else:
        argv.extend(["--category", category])
    return argv


def _from_command(collector: str, capability: str, cfg: dict, query: dict, data: Path, source_name: str = "", collector_key: str = "") -> dict:
    args = (
        _build_argv(collector_key, cfg, query)
        if collector_key
        else _build_argv("", {"command": cfg.get("command"), "enabled": True}, query)
    )
    source_name = source_name or str(query.get("source") or "browser")
    if not args:
        return _result(collector, capability, "failed", query, code="browser_unavailable", message="没有可执行的采集命令", source=source_name)
    raw_dir = data / "collector-raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{new_id('raw')}.log"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            args,
            cwd=workspace_root(),
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=int(cfg.get("timeout") or 120),
            check=False,
            **_subprocess_run_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raw_path.write_text(str(exc), encoding="utf-8")
        code = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "browser_unavailable"
        status = "timeout" if code == "timeout" else "failed"
        return _result(collector, capability, status, query, code=code, message=str(exc), source=source_name, raw_ref=str(raw_path))
    raw_path.write_text((completed.stdout or "") + "\n" + (completed.stderr or ""), encoding="utf-8")
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or (completed.stdout or "").strip()
        msg = "采集进程退出码 %s" % completed.returncode
        if detail:
            msg += "：" + detail[:240]
        return _result(collector, capability, "failed", query, code="failed", message=msg, source=source_name, raw_ref=str(raw_path))
    stdout = (completed.stdout or "").strip()
    if not stdout and (completed.stderr or "").strip():
        stdout = completed.stderr.strip()
    return interpret_output(collector, capability, stdout, query, source_name, str(raw_path))


def interpret_output(collector: str, capability: str, stdout: str, query: dict, source: str, raw_ref: str = "") -> dict:
    text = (stdout or "").strip()
    if not text:
        return _result(collector, capability, "empty", query, code="empty", message="没有输出", source=source, raw_ref=raw_ref)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _result(collector, capability, "parse_failed", query, code="parse_failed", message="输出不是 JSON", source=source, raw_ref=raw_ref)
    if not isinstance(payload, dict):
        return _result(collector, capability, "parse_failed", query, code="parse_failed", message="输出不是对象", source=source, raw_ref=raw_ref)
    if _is_mock(payload, text):
        return _result(collector, capability, "failed", query, code="mock_data", message="模拟数据不能当作热点", source=source, raw_ref=raw_ref)
    items = []
    rejected = 0
    for raw in payload.get("items") or []:
        if not isinstance(raw, dict):
            rejected += 1
            continue
        item = _item(raw, collector, source, raw_ref)
        if not item.get("title") or not item.get("url"):
            rejected += 1
            continue
        if query.get("category"):
            item["feed_channel"] = str(query.get("category"))
        if query.get("keyword"):
            item["search_keyword"] = str(query.get("keyword"))
        items.append(item)
    status = str(payload.get("status") or "")
    if status in {"auth_required", "rate_limited", "failed", "timeout", "cancelled", "empty"}:
        code = str((payload.get("error") or {}).get("code") or status)
        message = str((payload.get("error") or {}).get("message") or status)
        mapped = "empty" if status == "empty" else status if status != "failed" else "failed"
        return _result(collector, capability, mapped, query, code=code, message=message, source=source, raw_ref=raw_ref)
    if not items and rejected:
        return _result(collector, capability, "parse_failed", query, code="parse_failed", message="条目缺少标题或链接", source=source, raw_ref=raw_ref)
    if not items:
        return _result(collector, capability, "empty", query, code="empty", message="没有真实条目", source=source, raw_ref=raw_ref)
    result_status = "partial" if rejected else "ok"
    result = _result(collector, capability, result_status, query, source=source)
    result["items"] = items
    if "login_free" in payload:
        result["login_free"] = bool(payload.get("login_free"))
    else:
        result["login_free"] = True
    if rejected:
        result["error"] = {"code": "partial", "message": "丢弃 %s 条缺少标题或链接的记录" % rejected}
    return result


def _is_mock(payload: dict, text: str) -> bool:
    if payload.get("mock") is True:
        return True
    source = str(payload.get("source") or "").lower()
    if source in {"mock", "sample", "fake"}:
        return True
    lowered = text.lower()
    if "mock data" in lowered or "fallback to mock" in lowered:
        return True
    for item in payload.get("items") or []:
        if isinstance(item, dict) and item.get("mock") is True:
            return True
    return False


def _item(raw: dict, collector: str, source: str, raw_ref: str) -> dict:
    metrics = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}
    return {
        "platform": "xiaohongshu",
        "note_id": raw.get("note_id") or None,
        "title": str(raw.get("title") or "").strip(),
        "author": raw.get("author") or None,
        "url": str(raw.get("url") or "").strip(),
        "cover_url": raw.get("cover_url") or None,
        "category": raw.get("category") or None,
        "published_at": raw.get("published_at"),
        "content": None,
        "metrics": {
            "like_count": metrics.get("like_count"),
            "collect_count": metrics.get("collect_count"),
            "comment_count": metrics.get("comment_count"),
            "share_count": metrics.get("share_count"),
        },
        "comments": raw.get("comments") if isinstance(raw.get("comments"), list) else [],
        "media_files": raw.get("media_files") if isinstance(raw.get("media_files"), list) else [],
        "source": {"collector": collector, "source_name": source, "raw_ref": raw_ref},
    }


def _result(collector: str, capability: str, status: str, query: dict, code: str = "", message: str = "", source: str = "", raw_ref: str = "") -> dict:
    error = {"code": code, "message": message} if code else None
    return {
        "task_id": new_id("collect"),
        "collector": collector,
        "capability": capability,
        "source": source or None,
        "status": status,
        "collected_at": now(),
        "query": {
            "keyword": query.get("keyword") or "",
            "category": query.get("category") or "",
            "note_url": query.get("note_url") or "",
            "top_n": query.get("top_n") or 10,
        },
        "error": error,
        "items": [],
        "raw_ref": raw_ref or None,
    }


def store_run(db, result: dict) -> None:
    db.run(
        "INSERT INTO collect_runs (id,capability,collector,source,status,query_json,result_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            result["task_id"],
            result.get("capability") or "",
            result.get("collector"),
            result.get("source"),
            result.get("status"),
            dumps(result.get("query") or {}),
            dumps(result),
            result.get("collected_at") or now(),
        ),
    )
    for item in usable_items(result):
        db.run(
            "INSERT INTO collected_items (id,run_id,note_id,title,url,payload_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (new_id("item"), result["task_id"], item.get("note_id"), item.get("title"), item.get("url"), dumps(item), now()),
        )
