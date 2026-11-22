from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TZ = timezone(timedelta(hours=8))


def now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class DB:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS materials (
              id TEXT PRIMARY KEY,
              origin TEXT NOT NULL,
              platform TEXT,
              title TEXT,
              url TEXT,
              body TEXT,
              status TEXT NOT NULL,
              error_code TEXT,
              run_id TEXT,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS collect_runs (
              id TEXT PRIMARY KEY,
              capability TEXT NOT NULL,
              collector TEXT,
              source TEXT,
              status TEXT NOT NULL,
              query_json TEXT NOT NULL,
              result_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS collected_items (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              note_id TEXT,
              title TEXT,
              url TEXT,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS topics (
              id TEXT PRIMARY KEY,
              workflow_id TEXT,
              material_id TEXT,
              title TEXT NOT NULL,
              fit TEXT NOT NULL,
              fit_reason TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'candidate',
              plan_json TEXT,
              script TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notes (
              id TEXT PRIMARY KEY,
              topic_id TEXT,
              workflow_id TEXT,
              title TEXT NOT NULL,
              body TEXT NOT NULL,
              summary TEXT,
              tags_json TEXT NOT NULL,
              pages_json TEXT NOT NULL,
              version INTEGER NOT NULL,
              publish_status TEXT NOT NULL,
              review_json TEXT,
              error TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS note_metrics (
              id TEXT PRIMARY KEY,
              note_id TEXT NOT NULL,
              exposure INTEGER,
              reads INTEGER,
              likes INTEGER,
              collects INTEGER,
              comments INTEGER,
              followers INTEGER,
              recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workflow_runs (
              id TEXT PRIMARY KEY,
              step TEXT NOT NULL,
              state TEXT NOT NULL,
              artifacts_json TEXT NOT NULL,
              error TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
              id TEXT PRIMARY KEY,
              note_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS knowledge_docs (
              id TEXT PRIMARY KEY,
              path TEXT NOT NULL UNIQUE,
              title TEXT NOT NULL,
              status TEXT NOT NULL,
              body TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
              id TEXT PRIMARY KEY,
              doc_id TEXT NOT NULL,
              path TEXT NOT NULL,
              title TEXT NOT NULL,
              text TEXT NOT NULL,
              vector_json TEXT,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS turns (
              id TEXT PRIMARY KEY,
              role TEXT NOT NULL,
              text TEXT NOT NULL,
              engine TEXT,
              href TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publish_log (
              id TEXT PRIMARY KEY,
              note_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              status TEXT NOT NULL,
              detail TEXT,
              created_at TEXT NOT NULL
            );
            """
        )
        self._add_column("notes", "review_json", "ALTER TABLE notes ADD COLUMN review_json TEXT")
        self._add_column("topics", "status", "ALTER TABLE topics ADD COLUMN status TEXT NOT NULL DEFAULT 'candidate'")
        self._add_column("note_metrics", "followers", "ALTER TABLE note_metrics ADD COLUMN followers INTEGER")
        self.conn.commit()

    def _add_column(self, table: str, column: str, sql: str) -> None:
        columns = [row[1] for row in self.conn.execute("PRAGMA table_info(%s)" % table)]
        if column not in columns:
            self.conn.execute(sql)

    def one(self, sql: str, args: tuple = ()) -> dict[str, Any] | None:
        with self.lock:
            row = self.conn.execute(sql, args).fetchone()
        return dict(row) if row else None

    def all(self, sql: str, args: tuple = ()) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.conn.execute(sql, args).fetchall()
        return [dict(row) for row in rows]

    def run(self, sql: str, args: tuple = ()) -> None:
        with self.lock:
            self.conn.execute(sql, args)
            self.conn.commit()

    def close(self) -> None:
        with self.lock:
            self.conn.close()


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback
