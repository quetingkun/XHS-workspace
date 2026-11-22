import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "xhs"))

from xhs_svc.agent_engine import routing_fallback, update_routing  # noqa: E402
from xhs_svc.api import App  # noqa: E402
from xhs_svc.chat import answer  # noqa: E402
from xhs_svc.collector import collect, interpret_output  # noqa: E402
from xhs_svc.config import account_config, collector_config  # noqa: E402
from xhs_svc.daily_hot import hot_list_fresh_today, today_key  # noqa: E402
from xhs_svc.db import DB, dumps, now  # noqa: E402
from xhs_svc.knowledge import import_approved, retrieve  # noqa: E402
from xhs_svc.workflow import Error, Store  # noqa: E402


QUESTION = "根据知识库中的选题方法，告诉我如何判断一个 AI 技术热点是否适合做成小红书图文。"


class XhsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.db = DB(self.data / "xhs.sqlite")
        self.store = Store(self.db, self.data)
        os.environ["AGENT_CORE_URL"] = "http://127.0.0.1:9"
        os.environ["XHS_LLM_SETTINGS"] = str(self.data / "missing-llm.json")
        os.environ["XHS_EMBEDDING_SETTINGS"] = str(self.data / "missing-embedding.json")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_agent_engine_offline_routing(self):
        os.environ["AGENT_CORE_URL"] = "http://127.0.0.1:9"
        fallback = routing_fallback("down")
        self.assertTrue(fallback["offline"])
        self.assertEqual(fallback["default_engine"], "agent-core")
        app = App(self.db, self.data)
        status, payload, _ = app.handle("GET", "/api/xhs/settings/agent-engine", {})
        self.assertEqual(status, 200)
        self.assertTrue(payload["offline"])
        status, payload, _ = app.handle("PUT", "/api/xhs/settings/agent-engine", {"default_engine": "codex"})
        self.assertEqual(status, 400)
        self.assertIn("agent-core", str(payload.get("error") or ""))

    def test_hot_list_fresh_today_from_collect_runs(self):
        self.assertFalse(hot_list_fresh_today(self.db))
        self.db.run(
            "INSERT INTO collect_runs (id,capability,collector,source,status,query_json,result_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
            ("collect-test", "hot_list", "xiaohongshu-hot-daily", "browser", "ok", "{}", dumps({}), now()),
        )
        self.assertTrue(hot_list_fresh_today(self.db))
        self.assertEqual(today_key(), now()[:10])

    def test_account_and_collectors_stay_closed(self):
        account = account_config()
        self.assertEqual(account["positioning"], "待确定")
        self.assertFalse(account["auto_publish"])
        collectors = collector_config()
        self.assertTrue(collectors["hot_daily"]["enabled"] is True)
        self.assertTrue(collectors["hot_daily"].get("auto_refresh"))
        self.assertEqual(collectors["daily_top"]["fallback"], ["redfox", "custom_api", "playwright"])
        self.assertIn("教程", account["preferred_types"])

    def test_disabled_collector_does_not_invent_notes(self):
        closed = {"hot_daily": {"enabled": False, "command": ""}}
        result = collect({"capability": "hot_list"}, self.data, closed)
        self.assertEqual(result["status"], "source_unavailable")
        self.assertEqual(result["items"], [])

    def test_browser_and_mock_never_enter_topics(self):
        browser = self.store.collect({"capability": "hot_list", "probe": "browser_unavailable"})
        mock = self.store.collect({"capability": "hot_list", "probe": "mock_data"})
        self.assertEqual(browser["error"]["code"], "browser_unavailable")
        self.assertEqual(mock["error"]["code"], "mock_data")
        self.assertEqual(browser["items"], [])
        enabled = {"hot_daily": {"enabled": True, "command": ""}}
        failed = collect({"capability": "hot_list"}, self.data, enabled)
        self.assertIn(failed["error"]["code"], {"browser_unavailable", "empty", "failed"})
        self.store.collect({"capability": "hot_list"})
        bad = [item for item in self.store.materials() if item["status"] not in {"ok", "partial"}]
        self.assertTrue(bad)
        with self.assertRaises(Error):
            self.store.open_workflow([bad[0]["id"]])

    def test_mock_json_and_partial_links(self):
        mocked = interpret_output(
            "xiaohongshu-hot-daily",
            "hot_list",
            json.dumps({"mock": True, "items": [{"title": "看起来像真的", "url": "https://example.com/a"}]}),
            {},
            "browser",
        )
        self.assertEqual(mocked["status"], "failed")
        self.assertEqual(mocked["error"]["code"], "mock_data")
        partial = interpret_output(
            "xiaohongshu-hot-daily",
            "hot_list",
            json.dumps({"items": [{"title": "有链接", "url": "https://example.com/a"}, {"title": "没链接"}]}),
            {},
            "browser",
        )
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(len(partial["items"]), 1)
        self.assertIsNone(partial["items"][0]["content"])

    def test_daily_top_keeps_hops_when_playwright_missing(self):
        result = collect(
            {"capability": "daily_rank"},
            self.data,
            {"daily_top": {"enabled": True, "fallback": ["redfox", "custom_api", "playwright"], "commands": {}}},
        )
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["login_free"])
        self.assertEqual([hop["source"] for hop in result["hops"]], ["redfox", "custom_api", "playwright"])

    def test_draft_does_not_copy_other_people(self):
        material = self.store.add_manual({"title": "AI 代理能写周报吗", "url": "https://example.com/note", "body": "这是别人的正文，不能进草稿。"})
        workflow = self.store.open_workflow([material["id"]])
        self.assertEqual(len(workflow["topics"]), 5)
        topic = workflow["topics"][0]
        self.assertEqual(topic["fit"], "中")
        with self.assertRaises(Error):
            self.store.draft_topic(topic["id"])
        self.store.select_topic(topic["id"])
        note = self.store.draft_topic(topic["id"])
        self.assertGreaterEqual(len(note["pages"]), 3)
        self.assertLessEqual(len(note["pages"]), 6)
        self.assertNotIn("这是别人的正文", note["body"])
        visual = self.store.render_visual(note["id"])
        self.assertTrue(str(visual["cover"]).endswith("cover.svg"))

    def test_approval_is_bound_to_version(self):
        material = self.store.add_manual({"title": "本地模型怎么选", "body": "自己的观察"})
        topic = self.store.open_workflow([material["id"]])["topics"][0]
        self.store.select_topic(topic["id"])
        note = self.store.draft_topic(topic["id"])
        note = self.store.render_visual(note["id"])
        note = self.store.submit_note(note["id"], _checks())
        self.store.decide(note["id"], note["version"], "approve")
        changed = self.store.update_note(note["id"], {"title": "改过的标题"})
        self.assertEqual(changed["version"], note["version"] + 1)
        self.assertEqual(changed["publish_status"], "DRAFT")
        self.assertEqual(changed["review"], {})
        with self.assertRaises(Error):
            self.store.publish(changed["id"])
        again = self.store.submit_note(changed["id"], _checks())
        self.store.decide(again["id"], again["version"], "approve")
        published = self.store.publish(again["id"])
        self.assertEqual(published["publish_status"], "FAILED")
        self.assertIn("MCP", published["error"])

    def test_metrics_and_pending_review_are_not_searchable_until_confirmed(self):
        material = self.store.add_manual({"title": "收藏实验", "body": "自己的记录"})
        topic = self.store.open_workflow([material["id"]])["topics"][0]
        self.store.select_topic(topic["id"])
        note = self.store.draft_topic(topic["id"])
        self.store.add_metrics(note["id"], {"exposure": 100, "reads": 40, "likes": 3, "collects": 9, "comments": 1})
        review = self.store.write_review(note["id"])
        self.assertIn("观察", (self.data / "knowledge" / review["path"]).read_text(encoding="utf-8"))
        case = self.store.write_case(note["id"])
        cycle = self.store.write_cycle()
        self.assertTrue(case["path"].endswith(".md"))
        self.assertTrue(cycle["path"].endswith("cycle.md"))
        imported = import_approved(self.db, self.data)
        self.assertGreaterEqual(imported["skipped"], 1)
        self.assertEqual(retrieve(self.db, "复盘"), [])
        self.assertEqual(self.store.top_collects()[0]["collects"], 9)
        from xhs_svc.knowledge import confirm_file

        confirm_file(self.db, self.data, review["path"])
        found = retrieve(self.db, "复盘")
        self.assertTrue(found)
        self.assertEqual(found[0]["path"], review["path"])

    def test_question_cites_topic_selection_without_model(self):
        import_approved(self.db, ROOT / "data" / "xhs")
        found = retrieve(self.db, QUESTION)
        self.assertTrue(any(item["path"].endswith("topic-selection.md") for item in found))
        turn = answer(self.db, QUESTION)
        self.assertIn("topic-selection.md", turn["answer"])
        self.assertEqual(turn["engine"], "local-excerpt")
        self.assertTrue(turn["sources"])

    def test_template_cards_and_review_use_this_account(self):
        first = self.store.add_manual({"title": "已有笔记", "body": "自己的记录"})
        earlier_topic = self.store.open_workflow([first["id"]])["topics"][0]
        self.store.select_topic(earlier_topic["id"])
        earlier = self.store.draft_topic(earlier_topic["id"])
        self.store.add_metrics(earlier["id"], {"exposure": 80, "reads": 30, "likes": 2, "collects": 12, "comments": 0})
        material = self.store.add_manual({"title": "新热点", "url": "https://example.com/new", "body": "别人写的整段。"})
        topic = self.store.open_workflow([material["id"]])["topics"][0]
        self.store.select_topic(topic["id"])
        self.assertIn("已有笔记", topic["plan"]["dimensions"]["own_history"])
        self.assertIn("12", topic["plan"]["dimensions"]["own_history"])
        planned = self.store.plan_topic(topic["id"], "教程步骤")
        self.assertEqual(planned["plan"]["template"], "教程步骤")
        self.assertEqual(planned["plan"]["dimensions"]["heat"], topic["plan"]["dimensions"]["heat"])
        drafted = self.store.draft_topic(topic["id"], "教程步骤")
        self.assertNotIn("别人写的整段", drafted["body"])
        self.assertIn("第一步", drafted["body"])
        with self.assertRaises(Error):
            self.store.submit_note(drafted["id"], {})
        visual = self.store.render_visual(drafted["id"])
        self.assertTrue(visual["cover"].endswith("cover.svg"))
        self.assertGreaterEqual(sum(1 for page in visual["pages"] if page.get("image")), 3)
        self.assertIn("concept", visual["direction"])
        submitted = self.store.submit_note(drafted["id"], _checks())
        self.assertEqual(submitted["publish_status"], "WAITING_APPROVAL")
        self.assertTrue(submitted["review"]["images"])
        with self.assertRaises(Error):
            self.store.plan_topic(topic["id"], "不存在的模板")

    def test_same_link_merges_and_chat_points_at_a_step(self):
        from xhs_svc.chat import step_href

        self.assertEqual(step_href("看看今天的热点"), "/hot/today")
        self.assertEqual(step_href("记一下这篇的指标"), "/tools/metrics")
        first = self.store.add_manual({"title": "第一次", "url": "https://example.com/same", "platform": "抖音", "kind": "链接"})
        second = self.store.add_manual({"title": "第二次", "url": "https://example.com/same", "platform": "抖音", "kind": "链接"})
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["title"], "第二次")
        self.assertEqual(sum(1 for item in self.store.materials() if item["url"] == "https://example.com/same"), 1)

    def test_settings_keep_secret_and_mock_embedding_retrieves(self):
        from xhs_svc.knowledge import import_approved
        from xhs_svc.settings_store import SettingsStore, public_settings

        os.environ["XHS_EMBEDDING_SETTINGS"] = str(self.data / "settings" / "embedding.settings.json")
        store = SettingsStore(self.data / "settings")
        saved = store.save_llm(store.load_llm(), {"baseUrl": "http://127.0.0.1:9/v1", "model": "m", "apiKey": "sk-test-key99"})
        shown = public_settings(saved)
        self.assertTrue(shown["apiKey"].endswith("ey99"))
        self.assertNotIn("sk-test", shown["apiKey"])
        again = store.save_llm(saved, {"apiKey": shown["apiKey"], "model": "m2"})
        self.assertEqual(again["apiKey"], "sk-test-key99")
        self.assertEqual(again["model"], "m2")
        store.save_embedding(store.load_embedding(), {"provider": "mock", "defaultModel": "mock", "dimension": 8})
        folder = self.data / "knowledge" / "operation"
        folder.mkdir(parents=True)
        (folder / "note.md").write_text("---\nid: note\ntitle: 向量笔记\nstatus: approved\n---\n\n复盘要看收藏数\n", encoding="utf-8")
        result = import_approved(self.db, self.data)
        self.assertGreaterEqual(result["embedded"], 1)
        found = retrieve(self.db, "向量笔记 复盘要看收藏数")
        self.assertEqual(found[0]["match"], "embedding")
        self.assertEqual(found[0]["path"], "operation/note.md")


def _checks():
    return {key: True for key in ("facts", "originality", "quality", "images", "layout", "title", "rules")}


if __name__ == "__main__":
    unittest.main()
