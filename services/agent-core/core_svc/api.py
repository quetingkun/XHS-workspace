from __future__ import annotations

import json
from typing import Any, Iterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from core_svc.approvals import ApprovalGate, needs_approval
from core_svc.codex import CodexError, CodexSession
from core_svc.config import llm_runtime
from core_svc.local_engine import run_local, search_knowledge, system_for
from core_svc.mcpman import MCPManager, handle_mcp
from core_svc.routing import Routing  # noqa: F401
from core_svc.skills import SkillBook
from core_svc.websearch import WebSearch


def create_app(cfg, routing: Routing, codex: CodexSession | None, chat=None, knowledge=None, web: WebSearch | None = None, mcp: MCPManager | None = None, skills: SkillBook | None = None, gate: ApprovalGate | None = None) -> FastAPI:
    app = FastAPI()
    web = web or WebSearch()
    mcp = mcp if mcp is not None else MCPManager(list(getattr(cfg, "mcp_servers", []) or []))
    skills = skills if skills is not None else SkillBook(list(getattr(cfg, "skill_paths", []) or []))
    gate = gate or ApprovalGate()

    @app.middleware("http")
    async def cors(request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response(status_code=204)
        else:
            response = await call_next(request)
        origin = request.headers.get("origin", "")
        allow = ""
        for item in cfg.cors_origins:
            if item == "*":
                allow = origin or "*"
                break
            if origin == item:
                allow = origin
                break
        if allow:
            response.headers["Access-Control-Allow-Origin"] = allow
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Actor-Id, X-Workspace-Id, X-AIW-Engine"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,OPTIONS"
        response.headers["Access-Control-Expose-Headers"] = "X-Engine, X-Engine-Version"
        return response

    @app.get("/health")
    def health():
        return {"ok": True, "model": llm_runtime(cfg)["model"]}

    @app.get("/v1/capabilities")
    def capabilities():
        return {
            "providers": ["openai", "openai-compatible"],
            "sandbox_modes": ["read-only", "workspace-write"],
            "approval_modes": ["never", "on-request", "unless-trusted"],
            "engines": _engines(cfg, routing, codex),
            "features": {"streaming": True, "threads": True, "agents": True},
        }

    @app.api_route("/v1/engine/routing", methods=["GET", "PUT"])
    async def engine_routing(request: Request):
        if request.method == "PUT":
            body = await _json(request)
            if body is None:
                return JSONResponse({"error": {"code": "invalid_input", "message": "invalid json"}}, status_code=400)
            try:
                routing.update(str(body.get("default_engine") or ""), body.get("function_defaults") if isinstance(body.get("function_defaults"), dict) else {})
            except ValueError as exc:
                return JSONResponse({"error": {"code": "invalid_input", "message": str(exc)}}, status_code=400)
        return routing.view(_engines(cfg, routing, codex))

    @app.post("/v1/agent-turns")
    async def agent_turns(request: Request):
        body = await _json(request)
        if body is None or not str(body.get("prompt") or "").strip():
            return JSONResponse({"error": {"code": "invalid_input", "message": "prompt required"}}, status_code=400)
        function_id = str(body.get("function_id") or "general_qa")
        header = request.headers.get("x-aiw-engine", "")
        codex_ok = bool(codex and codex.runnable())
        engine = routing.choose(header, function_id, codex_ok)
        version = cfg.codex_version if engine == "codex" else "python"
        return StreamingResponse(
            _sse(_turn(cfg, codex, chat, knowledge, web, mcp, skills, gate, body, function_id, engine, codex_ok, header)),
            media_type="text/event-stream; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Engine": engine, "X-Engine-Version": version},
        )

    @app.get("/v1/mcp")
    def mcp_health():
        return {"servers": mcp.health()}

    @app.get("/v1/approvals")
    def list_approvals():
        return {"items": gate.pending()}

    @app.post("/v1/approvals/{approval_id}")
    async def decide_approval(approval_id: str, request: Request):
        body = await _json(request)
        if body is None:
            return JSONResponse({"error": {"code": "invalid_input", "message": "invalid json"}}, status_code=400)
        decision = str(body.get("decision") or "")
        if not gate.decide(approval_id, decision):
            return JSONResponse({"error": {"code": "invalid_input", "message": "approval not pending"}}, status_code=404)
        return {"id": approval_id, "decision": decision}

    @app.api_route("/api/internal/mcp/web_search", methods=["GET", "POST"])
    async def web_mcp(request: Request):
        if request.method == "GET":
            return {"ok": True, "tools": ["search"]}
        body = await _json(request) or {}

        def _call(arguments: dict) -> str:
            found = web.search(str(arguments.get("query") or ""))
            if not found.get("ok"):
                raise RuntimeError(str(found.get("error") or "联网搜索不可用"))
            return str(found.get("content") or "")

        return handle_mcp(body, _call)

    return app


def _turn(cfg, codex, chat, knowledge, web: WebSearch, mcp: MCPManager, skills: SkillBook, gate: ApprovalGate, body: dict, function_id: str, engine: str, codex_ok: bool, header: str) -> Iterator[dict]:
    prompt = str(body.get("prompt") or "").strip()
    context = body.get("context") if isinstance(body.get("context"), dict) else {}
    skill_text = skills.select(prompt)
    evidence, prelude = _evidence(cfg, knowledge, web, mcp, gate, prompt, context)
    if skill_text:
        evidence = (evidence + "\n\n" if evidence else "") + "适用技能：\n" + skill_text
    yield from prelude
    if engine == "codex":
        if not codex_ok or codex is None:
            message = codex.unavailable_reason() if codex is not None else "Codex 二进制不可用"
            yield {"type": "error", "payload": {"message": message}}
            yield {"type": "turn.failed", "payload": {"message": message}}
            return
        try:
            yield from codex.turn(
                str(body.get("session_id") or "default"),
                prompt if not evidence else prompt + "\n\n" + evidence,
                system_for(function_id),
                cfg.instructions,
            )
        except (CodexError, Exception) as exc:  # noqa: BLE001
            yield {"type": "error", "payload": {"message": str(exc)}}
            yield {"type": "turn.failed", "payload": {"message": str(exc)}}
        return
    runtime = llm_runtime(cfg)
    yield from run_local(prompt, function_id, evidence, chat, runtime)


def _evidence(cfg, knowledge, web: WebSearch, mcp: MCPManager, gate: ApprovalGate, prompt: str, context: dict) -> tuple[str, list[dict]]:
    events: list[dict] = []
    blocks: list[str] = []
    kb_ids = [str(item) for item in (context.get("knowledge_base_ids") or []) if str(item).strip()]
    want_kb = kb_ids and "[知识库检索:关闭]" not in prompt
    if "[知识库检索:开启]" in prompt and not kb_ids:
        kb_ids = list(cfg.default_kb_ids)
        want_kb = True
    if want_kb:
        allowed, extra = _guard(cfg, gate, "mcp__knowledge__search", _user_text(prompt))
        events.extend(extra)
        if allowed:
            events.append({"type": "tool.call.started", "payload": {"name": "mcp__knowledge__search"}})
            try:
                text = _knowledge_text(cfg, knowledge, mcp, kb_ids, prompt, context)
            except Exception as exc:  # noqa: BLE001
                text = ""
                blocks.append("知识库检索失败：" + str(exc))
            if text:
                blocks.append("知识库摘录：\n" + text)
            events.append({"type": "tool.call.completed", "payload": {"name": "mcp__knowledge__search"}})
    if "[联网搜索:开启]" in prompt:
        allowed, extra = _guard(cfg, gate, "mcp__web_search__search", _user_text(prompt))
        events.extend(extra)
        if allowed:
            events.append({"type": "tool.call.started", "payload": {"name": "mcp__web_search__search"}})
            try:
                if mcp.has("web_search"):
                    content = mcp.call("web_search", "search", {"query": _user_text(prompt)})
                    blocks.append("联网补充：\n" + content)
                else:
                    found = web.search(_user_text(prompt))
                    if found.get("ok"):
                        blocks.append("联网补充：\n" + str(found.get("content") or ""))
                    else:
                        blocks.append("联网补充：\n（联网检索失败。" + str(found.get("error") or "") + "）")
            except Exception as exc:  # noqa: BLE001
                blocks.append("联网补充：\n（联网检索失败。" + str(exc) + "）")
            events.append({"type": "tool.call.completed", "payload": {"name": "mcp__web_search__search"}})
    return "\n\n".join(blocks), events


def _knowledge_text(cfg, knowledge, mcp: MCPManager, kb_ids: list[str], prompt: str, context: dict) -> str:
    if mcp.has("knowledge"):
        return mcp.call(
            "knowledge",
            "search",
            {
                "query": _user_text(prompt),
                "kb_ids": kb_ids,
                "top_k": cfg.knowledge_top_k,
            },
        )
    if knowledge:
        return knowledge(kb_ids, prompt, bool(context.get("knowledge_graph_enhanced")))
    return search_knowledge(cfg.knowledge_url, kb_ids, _user_text(prompt), cfg.knowledge_top_k, bool(context.get("knowledge_graph_enhanced")))


def _guard(cfg, gate: ApprovalGate, name: str, detail: str) -> tuple[bool, list[dict]]:
    mode = str(getattr(cfg, "approval_mode", "unless-trusted") or "unless-trusted")
    trusted = list(getattr(cfg, "trusted_tools", []) or [])
    if not needs_approval(mode, name, trusted):
        return True, []
    approval_id = gate.request(name, detail[:200])
    events = [{"type": "approval.requested", "payload": {"id": approval_id, "name": name}}]
    decision = gate.wait(approval_id)
    if decision != "approve":
        events.append({"type": "approval.denied", "payload": {"id": approval_id, "name": name}})
        return False, events
    events.append({"type": "approval.granted", "payload": {"id": approval_id, "name": name}})
    return True, events


def _user_text(prompt: str) -> str:
    lines = [line for line in prompt.splitlines() if not line.startswith("[知识库检索:") and not line.startswith("[联网搜索:")]
    return "\n".join(lines).strip() or prompt


def _engines(cfg, routing: Routing, codex: CodexSession | None) -> list[dict[str, Any]]:
    codex_ok = bool(cfg.codex_enabled and codex and codex.runnable())
    default = routing.default_engine
    if default == "codex" and not codex_ok:
        default = "agent-core"
    # routing overlay may differ; capabilities still describe availability
    return [
        {"name": "agent-core", "default": default != "codex", "available": True, "enabled": True, "version": "python"},
        {"name": "codex", "default": default == "codex", "available": codex_ok, "enabled": bool(cfg.codex_enabled), "version": cfg.codex_version},
    ]


def _sse(events: Iterator[dict]) -> Iterator[str]:
    for event in events:
        yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


async def _json(request: Request) -> dict | None:
    raw = await request.body()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
