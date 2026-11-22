from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from xhs_svc.agent_engine import fetch_routing, update_routing
from xhs_svc.chat import answer, step_href, test_llm
import os

from xhs_svc.config import account_config, collector_config, data_dir
from xhs_svc.db import DB
from xhs_svc.embedder import embed_texts
from xhs_svc.knowledge import add_document, confirm_file, import_approved, index_vectors, list_docs, retrieve
from xhs_svc.deploy_env import sync_llm_to_deploy_env
from xhs_svc.settings_store import SettingsStore, public_settings
from xhs_svc.workflow import Error, Store


class App:
    def __init__(self, db: DB, data: Path) -> None:
        self.store = Store(db, data)
        self.db = db
        self.data = data

    def handle(self, method: str, path: str, body: dict | None) -> tuple[int, dict | None, dict | None]:
        parsed = urlparse(path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        try:
            return self._handle(method, route, body or {}, query)
        except Error as exc:
            return exc.status, {"error": exc.message}, None
        except FileNotFoundError:
            return 404, {"error": "文稿不存在"}, None
        except ValueError as exc:
            return 400, {"error": str(exc)}, None

    def _handle(self, method: str, route: str, body: dict, query: dict) -> tuple[int, dict | None, dict | None]:
        if method == "GET" and route == "/api/xhs/account":
            return 200, account_config(), None
        if method == "GET" and route == "/api/xhs/system":
            collectors = collector_config()
            enabled = sorted(name for name, cfg in collectors.items() if isinstance(cfg, dict) and cfg.get("enabled"))
            routing = fetch_routing()
            return 200, {
                "data_dir": str(data_dir()),
                "collectors_enabled": enabled,
                "collectors_total": len(collectors),
                "auto_publish": account_config().get("auto_publish"),
                "agent_core": not routing.get("offline"),
                "agent_engine_default": routing.get("default_engine") or "agent-core",
                "xhs_mcp": bool(os.environ.get("XHS_MCP_URL", "").strip()),
                "configs": {
                    "account": "services/xhs/configs/account.yaml",
                    "collectors": "services/xhs/configs/collectors.yaml",
                },
            }, None
        if method == "GET" and route in {"/health", "/api/xhs/health"}:
            return 200, {"ok": True, "service": "xhs"}, None
        if method == "GET" and route == "/api/xhs/materials":
            return 200, {"materials": self.store.materials()}, None
        if method == "POST" and route == "/api/xhs/materials":
            return 201, self.store.add_manual(body), None
        if method == "POST" and route == "/api/xhs/materials/purge-failures":
            return 200, self.store.purge_collect_failures(), None
        if method == "DELETE" and route.startswith("/api/xhs/materials/"):
            self.store.delete_material(route.rsplit("/", 1)[-1])
            return 204, None, None
        if method == "POST" and route == "/api/xhs/collect":
            return 200, self.store.collect(body), None
        if method == "GET" and route.startswith("/api/xhs/collect/"):
            return 200, self.store.run(route.rsplit("/", 1)[-1]), None
        if method == "GET" and route == "/api/xhs/workflows":
            return 200, {"workflows": self.store.workflows()}, None
        if method == "POST" and route == "/api/xhs/workflows":
            return 201, self.store.open_workflow(list(body.get("material_ids") or [])), None
        if method == "POST" and route == "/api/xhs/workflows/quick":
            return 201, self.store.open_workflow_quick(str(body.get("title") or "")), None
        if method == "GET" and route.startswith("/api/xhs/workflows/"):
            return 200, self.store.workflow(route.rsplit("/", 1)[-1]), None
        if method == "GET" and route == "/api/xhs/topics":
            return 200, {"topics": self.store.topics(), "report": self.store.latest_report()}, None
        if method == "POST" and route.startswith("/api/xhs/topics/") and route.endswith("/plan"):
            return 200, self.store.plan_topic(route.split("/")[4], str(body.get("template") or ""), int(body.get("page_count") or 0)), None
        if method == "POST" and route.startswith("/api/xhs/topics/") and route.endswith("/draft"):
            topic_id = route.split("/")[4]
            use_llm = body.get("use_llm") in (True, "true", "1", 1, "yes", "on")
            quick_prefs = body.get("quick_prefs") if isinstance(body.get("quick_prefs"), dict) else None
            return 201, self.store.draft_topic(
                topic_id,
                str(body.get("template") or ""),
                int(body.get("page_count") or 0),
                use_llm=use_llm,
                quick_prefs=quick_prefs,
            ), None
        if method == "POST" and route.startswith("/api/xhs/topics/") and route.endswith("/select"):
            return 200, self.store.select_topic(route.split("/")[4]), None
        if method == "POST" and route.startswith("/api/xhs/topics/") and route.endswith("/reject"):
            return 200, self.store.reject_topic(route.split("/")[4]), None
        if method == "PUT" and route.startswith("/api/xhs/topics/") and route.count("/") == 4:
            return 200, self.store.rename_topic(route.split("/")[4], str(body.get("title") or "")), None
        if method == "GET" and route == "/api/xhs/notes":
            return 200, {"notes": self.store.notes()}, None
        if method == "GET" and route.startswith("/api/xhs/notes/") and route.endswith("/metrics") is False and route.count("/") == 4:
            return 200, self.store.note(route.split("/")[4]), None
        if method == "PUT" and route.startswith("/api/xhs/notes/") and route.count("/") == 4:
            return 200, self.store.update_note(route.split("/")[4], body), None
        if method == "POST" and route == "/api/xhs/images/generate":
            return 200, self.store.generate_images(body), None
        if method == "POST" and route.endswith("/visual") and route.startswith("/api/xhs/notes/"):
            return 200, self.store.render_visual(route.split("/")[4]), None
        if method == "POST" and route.endswith("/submit") and route.startswith("/api/xhs/notes/"):
            return 200, self.store.submit_note(route.split("/")[4], body.get("checks") or {}), None
        if method == "POST" and route.endswith("/publish") and route.startswith("/api/xhs/notes/"):
            return 200, self.store.publish(route.split("/")[4]), None
        if method == "POST" and route.endswith("/metrics") and route.startswith("/api/xhs/notes/"):
            return 201, self.store.add_metrics(route.split("/")[4], body), None
        if method == "POST" and route.endswith("/review") and route.startswith("/api/xhs/notes/"):
            return 201, self.store.write_review(route.split("/")[4]), None
        if method == "POST" and route.endswith("/case") and route.startswith("/api/xhs/notes/"):
            return 201, self.store.write_case(route.split("/")[4]), None
        if method == "POST" and route == "/api/xhs/reviews/cycle":
            return 201, self.store.write_cycle(), None
        if method == "GET" and route == "/api/xhs/metrics/top":
            return 200, {"notes": self.store.top_collects()}, None
        if method == "GET" and route == "/api/xhs/library/videos":
            return 200, self.store.library_videos(), None
        if method == "POST" and route == "/api/xhs/approvals":
            return 200, self.store.decide(str(body.get("note_id") or ""), int(body.get("version") or 0), str(body.get("decision") or "")), None
        if method == "GET" and route == "/api/xhs/knowledge/docs":
            return 200, {"docs": list_docs(self.db)}, None
        if method == "POST" and route == "/api/xhs/knowledge/documents":
            return 201, add_document(self.db, self.data, str(body.get("title") or ""), str(body.get("body") or "")), None
        if method == "POST" and route == "/api/xhs/knowledge/reindex":
            count, error = index_vectors(self.db, self.data)
            if error:
                raise Error(error)
            return 200, {"embedded": count}, None
        if method == "POST" and route == "/api/xhs/knowledge/import":
            return 200, import_approved(self.db, self.data), None
        if method == "GET" and route == "/api/xhs/settings/llm":
            return 200, public_settings(self._settings().load_llm()), None
        if method == "PUT" and route == "/api/xhs/settings/llm":
            store = self._settings()
            saved = store.save_llm(store.load_llm(), body)
            sync_out = sync_llm_to_deploy_env()
            payload = public_settings(saved)
            payload["deployEnvSynced"] = sync_out.ok
            if sync_out.warn:
                payload["deployEnvSyncWarn"] = sync_out.warn
            return 200, payload, None
        if method == "POST" and route == "/api/xhs/settings/llm/test":
            store = self._settings()
            try:
                merged = store.merge_llm(store.load_llm(), body or {})
                return 200, test_llm(merged), None
            except RuntimeError as exc:
                raise Error(str(exc)) from exc
        if method == "GET" and route == "/api/xhs/settings/embedding":
            return 200, public_settings(self._settings().load_embedding()), None
        if method == "PUT" and route == "/api/xhs/settings/embedding":
            store = self._settings()
            saved = store.save_embedding(store.load_embedding(), body)
            return 200, public_settings(saved), None
        if method == "POST" and route == "/api/xhs/settings/embedding/test":
            try:
                vector = embed_texts(self._settings().load_embedding(), ["连通测试"])[0]
            except RuntimeError as exc:
                raise Error(str(exc)) from exc
            return 200, {"ok": True, "dimension": len(vector)}, None
        if method == "GET" and route == "/api/xhs/settings/agent-engine":
            return 200, fetch_routing(), None
        if method == "PUT" and route == "/api/xhs/settings/agent-engine":
            try:
                return 200, update_routing(body), None
            except ValueError as exc:
                raise Error(str(exc)) from exc
            except RuntimeError as exc:
                raise Error(str(exc)) from exc
        if method == "POST" and route == "/api/xhs/knowledge/confirm":
            return 200, confirm_file(self.db, self.data, str(body.get("path") or "")), None
        if method == "GET" and route == "/api/xhs/knowledge/retrieve":
            q = (query.get("q") or [""])[0]
            return 200, {"sources": retrieve(self.db, q)}, None
        if method == "GET" and route == "/api/xhs/turns":
            return 200, {"turns": self.store.turns()}, None
        if method == "POST" and route == "/api/xhs/turns":
            prompt = str(body.get("prompt") or "").strip()
            if not prompt:
                raise Error("prompt 不能为空")
            note = str(body.get("workflow_note") or "")
            use_knowledge = body.get("use_knowledge", True)
            if isinstance(use_knowledge, str):
                use_knowledge = use_knowledge.lower() not in {"0", "false", "off", "no"}
            use_web = body.get("use_web", False)
            if isinstance(use_web, str):
                use_web = use_web.lower() in {"1", "true", "on", "yes"}
            mode = str(body.get("mode") or "general").strip() or "general"
            session_id = str(body.get("session_id") or "").strip()
            history = body.get("history")
            if not isinstance(history, list):
                history = None
            self.store.add_turn("user", prompt, "", "")
            result = answer(
                self.db,
                prompt,
                note,
                use_knowledge=bool(use_knowledge),
                use_web=bool(use_web),
                mode=mode,
                session_id=session_id,
                history=history,
            )
            href = step_href(prompt)
            result["href"] = href
            self.store.add_turn("assistant", result["answer"], result["engine"], href)
            return 200, result, {"X-Engine": result["engine"]}
        return 404, {"error": "路径不存在"}, None

    def _settings(self) -> SettingsStore:
        return SettingsStore(self.data / "settings")


def read_json(raw: bytes) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise Error("请求不是 JSON") from exc
    if not isinstance(data, dict):
        raise Error("请求不是对象")
    return data
