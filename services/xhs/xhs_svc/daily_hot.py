"""服务内：当日热点自动补采（不依赖外部脚本）。"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta, timezone

from xhs_svc.config import collector_config

TZ = timezone(timedelta(hours=8))
_LOCK = threading.Lock()


def today_key() -> str:
    return datetime.now(TZ).date().isoformat()


def last_successful_hot_collect_day(db) -> str | None:
    row = db.one(
        """SELECT created_at FROM collect_runs
           WHERE capability='hot_list' AND status IN ('ok','partial')
           ORDER BY created_at DESC LIMIT 1"""
    )
    if not row or not row.get("created_at"):
        return None
    return str(row["created_at"])[:10]


def hot_list_fresh_today(db) -> bool:
    return last_successful_hot_collect_day(db) == today_key()


def run_if_stale(store, *, reason: str, force: bool = False) -> dict | None:
    cfg = collector_config().get("hot_daily") or {}
    if not cfg.get("enabled"):
        return None
    if os.environ.get("XHS_SKIP_STARTUP_COLLECT", "").strip().lower() in {"1", "true", "yes"}:
        return None
    if not force and hot_list_fresh_today(store.db):
        return None
    if not _LOCK.acquire(blocking=False):
        return None
    try:
        if not force and hot_list_fresh_today(store.db):
            return None
        print("[xhs] 自动热点采集（%s）…" % reason, flush=True)
        collect_query = {"capability": "hot_list", "category": str(cfg.get("default_category") or "推荐")}
        kw = str(cfg.get("default_keyword") or "").strip()
        if kw:
            collect_query["keyword"] = kw
        result = store.collect(collect_query)
        status = result.get("status")
        n = len(result.get("items") or [])
        if status in {"ok", "partial"}:
            print("[xhs] 自动热点采集完成：%s，%s 条。" % (status, n), flush=True)
        else:
            err = (result.get("error") or {}).get("message") or status
            print("[xhs] 自动热点采集失败：%s" % err, flush=True)
        return result
    finally:
        _LOCK.release()


def start_auto_hot_refresh(store) -> None:
    cfg = collector_config().get("hot_daily") or {}
    if not cfg.get("enabled") or cfg.get("auto_refresh") is False:
        return

    def worker() -> None:
        time.sleep(1.0)
        run_if_stale(store, reason="服务启动")
        minutes = int(cfg.get("refresh_check_minutes") or 0)
        if minutes <= 0:
            return
        while True:
            time.sleep(minutes * 60)
            run_if_stale(store, reason="定时检查")

    thread = threading.Thread(target=worker, name="xhs-daily-hot", daemon=True)
    thread.start()