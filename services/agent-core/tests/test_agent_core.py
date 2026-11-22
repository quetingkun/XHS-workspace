import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from core_svc.api import create_app
from core_svc.codex import CodexSession
from core_svc.config import Config
from core_svc.routing import Routing
from core_svc.websearch import WebSearch


FAKE = r'''
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        sys.stdout.write(json.dumps({"id": msg["id"], "result": {"userAgent": "fake"}}) + "\n")
        sys.stdout.flush()
    elif method == "thread/start":
        sys.stdout.write(json.dumps({"id": msg["id"], "result": {"thread": {"id": "thr-1"}, "model": "m"}}) + "\n")
        sys.stdout.flush()
    elif method == "turn/start":
        sys.stdout.write(json.dumps({"id": msg["id"], "result": {"turn": {"id": "turn-1"}}}) + "\n")
        sys.stdout.flush()
        sys.stdout.write(json.dumps({"method": "item/agentMessage/delta", "params": {"delta": "来自 Codex"}}) + "\n")
        sys.stdout.flush()
        sys.stdout.write(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "turn-1", "status": "completed"}}}) + "\n")
        sys.stdout.flush()
'''


def chat(_messages):
    yield "本地回答"


class SilentWeb(WebSearch):
    def search(self, query: str):
        return {"ok": True, "content": "网页摘录"}


class AgentCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = Config()
        self.cfg.cors_origins = ["*"]
        self.cfg.default_engine = "agent-core"
        self.cfg.codex_enabled = True
        self.cfg.state_root = str(root / "state")
        self.cfg.knowledge_url = ""
        self.routing = Routing(self.cfg.state_root, "agent-core", True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_local_turn_and_routing(self) -> None:
        app = create_app(self.cfg, self.routing, None, chat=chat, web=SilentWeb())
        client = TestClient(app)
        health = client.get("/health", headers={"Origin": "http://localhost:5173"})
        self.assertTrue(health.json()["ok"])
        self.assertEqual(health.headers["access-control-allow-origin"], "http://localhost:5173")
        caps = client.get("/v1/capabilities").json()
        names = {item["name"] for item in caps["engines"]}
        self.assertEqual(names, {"agent-core", "codex"})
        missing = client.post("/v1/agent-turns", json={"function_id": "general_qa"})
        self.assertEqual(missing.status_code, 400)
        res = client.post(
            "/v1/agent-turns",
            json={"function_id": "general_qa", "prompt": "[知识库检索:关闭]\n[联网搜索:开启]\n天气", "session_id": "s1"},
            headers={"X-AIW-Engine": "go-agent-core"},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.headers["x-engine"], "agent-core")
        events = [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]
        types = [item["type"] for item in events]
        self.assertIn("tool.call.started", types)
        self.assertIn("model.output.delta", types)
        self.assertEqual(events[-1]["type"], "turn.completed")
        self.assertIn("本地回答", events[-1]["payload"]["final_message"])
        updated = client.put("/v1/engine/routing", json={"default_engine": "go-agent-core", "function_defaults": {"brainstorm": "go-agent-core"}})
        self.assertEqual(updated.json()["default_engine"], "agent-core")
        self.assertEqual(updated.json()["function_defaults"]["brainstorm"], "agent-core")
        again = client.get("/v1/engine/routing")
        self.assertEqual(again.json()["functions"][1]["engine"], "agent-core")

    def test_codex_sidecar_maps_delta(self) -> None:
        script = Path(self.tmp.name) / "fake_codex.py"
        script.write_text(FAKE, encoding="utf-8")
        codex = CodexSession(str(script), str(Path(self.tmp.name) / "home"), str(Path(self.tmp.name) / "work"), "m", "openai-compatible")
        self.cfg.codex_enabled = True
        self.cfg.default_engine = "codex"
        routing = Routing(self.cfg.state_root, "codex", True)
        app = create_app(self.cfg, routing, codex, chat=chat, web=SilentWeb())
        client = TestClient(app)
        self.assertTrue(client.get("/v1/capabilities").json()["engines"][1]["available"])
        res = client.post(
            "/v1/agent-turns",
            json={"function_id": "brainstorm", "prompt": "如何整理笔记", "session_id": "bs1"},
            headers={"X-AIW-Engine": "codex"},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.headers["x-engine"], "codex")
        events = [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]
        deltas = [item["payload"]["delta"] for item in events if item["type"] == "model.output.delta"]
        self.assertEqual(deltas, ["来自 Codex"])
        self.assertEqual(events[-1]["type"], "turn.completed")
        codex.close()

    def test_sha256_rejects_mismatch(self) -> None:
        binary = Path(self.tmp.name) / "codex.bin"
        binary.write_bytes(b"not-the-real-binary")
        digest = hashlib.sha256(b"not-the-real-binary").hexdigest()
        wrong = CodexSession(str(binary), str(Path(self.tmp.name) / "home"), self.tmp.name, "m", "p", expected_sha256="0" * 64)
        self.assertFalse(wrong.runnable())
        self.assertEqual(wrong.unavailable_reason(), "Codex 二进制校验失败")
        matched = CodexSession(str(binary), str(Path(self.tmp.name) / "home"), self.tmp.name, "m", "p", expected_sha256=digest, sandbox="workspace-write")
        self.assertIn("sandbox_mode=workspace-write", matched._argv())
        self.assertIn("features.shell_tool=true", matched._argv())
        blocked = CodexSession(str(binary), str(Path(self.tmp.name) / "home"), self.tmp.name, "m", "p", sandbox="danger-full-access")
        self.assertFalse(blocked.runnable())
        self.assertIn("不受支持", blocked.unavailable_reason())

    def test_skill_reload_and_mcp_and_approval(self) -> None:
        from core_svc.approvals import ApprovalGate
        from core_svc.mcpman import MCPManager
        from core_svc.skills import SkillBook
        import httpx

        root = Path(self.tmp.name) / "skills" / "demo"
        root.mkdir(parents=True)
        skill = root / "SKILL.md"
        skill.write_text("---\nname: demo\ndescription: 用于历史案例\n---\n\n## 适用场景\n\n- 历史案例\n", encoding="utf-8")
        book = SkillBook([str(root.parent)])
        self.assertIn("历史案例", book.select("帮我找历史案例"))
        skill.write_text("---\nname: demo\ndescription: 只谈库存盘点\n---\n\n## 适用场景\n\n- 库存盘点\n", encoding="utf-8")
        os_utime = __import__("os").utime
        os_utime(skill, (skill.stat().st_atime + 5, skill.stat().st_mtime + 5))
        self.assertNotIn("历史案例", book.select("帮我找历史案例"))
        self.assertIn("库存盘点", book.select("做一次库存盘点"))

        def _handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"ok": True})
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "知识库摘录"}]}})

        manager = MCPManager(
            [{"name": "knowledge", "url": "http://knowledge/api/internal/mcp/knowledge", "required": True}],
            client=httpx.Client(transport=httpx.MockTransport(_handler)),
        )
        self.assertTrue(manager.health()[0]["ok"])
        self.assertEqual(manager.call("knowledge", "search", {"query": "案例"}), "知识库摘录")

        gate = ApprovalGate()
        app = create_app(self.cfg, self.routing, None, chat=chat, web=SilentWeb(), gate=gate)
        client = TestClient(app)
        approval_id = gate.request("mcp__web_search__search", "天气")
        denied = client.post("/v1/approvals/" + approval_id, json={"decision": "deny"})
        self.assertEqual(denied.status_code, 200)
        self.assertEqual(gate.wait(approval_id, 1), "deny")
        self.assertEqual(client.get("/api/internal/mcp/web_search").json()["ok"], True)


class EvalTests(unittest.TestCase):
    def test_fixed_cases(self) -> None:
        from core_svc.evalrun import check_events, load_cases

        cases = load_cases(str(Path(__file__).resolve().parents[1] / "evals" / "cases.json"))
        tmp = tempfile.TemporaryDirectory()
        cfg = Config()
        cfg.state_root = str(Path(tmp.name) / "state")
        cfg.default_engine = "agent-core"
        cfg.knowledge_url = ""
        routing = Routing(cfg.state_root, "agent-core", True)
        client = TestClient(create_app(cfg, routing, None, chat=chat, web=SilentWeb()))
        try:
            for case in cases:
                res = client.post("/v1/agent-turns", json={"function_id": "general_qa", "prompt": case["prompt"], "session_id": case["name"]})
                self.assertEqual(res.status_code, 200, res.text)
                events = [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith("data: ")]
                self.assertEqual(check_events(events, case), [], case["name"])
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
