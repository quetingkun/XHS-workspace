from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from xhs_svc import collector
from xhs_svc.config import account_config, workspace_root
from xhs_svc.db import DB, dumps, loads, new_id, now
from xhs_svc.knowledge import retrieve


class Error(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class Store:
    def __init__(self, db: DB, data: Path) -> None:
        self.db = db
        self.data = data

    def materials(self) -> list[dict]:
        rows = self.db.all("SELECT * FROM materials ORDER BY created_at DESC")
        return [self._material_view(row) for row in rows]

    def add_manual(self, payload: dict) -> dict:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise Error("标题不能为空")
        platform = str(payload.get("platform") or "人工")
        kind = str(payload.get("kind") or "文案")
        if platform not in PLATFORMS:
            raise Error("平台只能是小红书、抖音、哔哩哔哩、微博、知乎或人工")
        if kind not in KINDS:
            raise Error("进入方式只能是链接、截图说明、文案或竞品账号")
        item = {
            "platform": platform,
            "title": title,
            "url": str(payload.get("url") or "").strip(),
            "body": str(payload.get("body") or "").strip(),
            "kind": kind,
            "note_id": str(payload.get("note_id") or "").strip(),
        }
        existing = self._find_duplicate(item["url"], item)
        if existing:
            return self._merge_material(existing, title, item["url"], "ok", None, None, item)
        return self._insert_material("manual", title, item["url"], "ok", None, None, item)

    def delete_material(self, material_id: str) -> None:
        if not self.db.one("SELECT id FROM materials WHERE id=?", (material_id,)):
            raise Error("素材不存在", 404)
        self.db.run("DELETE FROM materials WHERE id=?", (material_id,))

    def purge_collect_failures(self) -> dict:
        rows = self.db.all(
            "SELECT id FROM materials WHERE origin='collect' AND ifnull(url,'')='' AND status NOT IN ('ok','partial')"
        )
        for row in rows:
            self.db.run("DELETE FROM materials WHERE id=?", (row["id"],))
        return {"deleted": len(rows)}

    def collect(self, query: dict) -> dict:
        result = collector.collect(query, self.data)
        collector.store_run(self.db, result)
        if str(query.get("probe") or ""):
            return result
        items = collector.usable_items(result)
        if items:
            for item in items:
                existing = self._find_duplicate(item.get("url") or "", item)
                if existing:
                    self._merge_material(existing, item["title"], item.get("url") or "", "ok", None, result["task_id"], item)
                else:
                    self._insert_material("collect", item["title"], item["url"], "ok", None, result["task_id"], item)
            if result.get("status") == "partial" and result.get("error"):
                self._insert_material(
                    "collect",
                    "本次采集有未采用的条目",
                    "",
                    "partial",
                    "partial",
                    result["task_id"],
                    {"error": result.get("error")},
                )
        else:
            error = result.get("error") or {}
            capability = str(query.get("capability") or result.get("capability") or "")
            platform = "小红书" if capability in {"hot_list", "daily_rank", "search", "note_detail", "comments"} else ""
            payload = {
                "error": error,
                "hops": result.get("hops"),
                "platform": platform,
                "kind": capability,
                "collector": result.get("collector"),
            }
            collector_name = str(result.get("collector") or result.get("capability") or "")
            titles = {
                "xiaohongshu-hot-daily": "小红书日榜",
                "MediaCrawler": "MediaCrawler",
                "XHS-Downloader": "XHS-Downloader",
            }
            title = "%s · %s" % (titles.get(collector_name, collector_name), result.get("status"))
            status = result.get("status") or "failed"
            code = error.get("code") or ""
            existing = None
            for row in self.db.all("SELECT * FROM materials WHERE origin='collect' AND ifnull(url,'')='' AND status=? AND ifnull(error_code,'')=?", (status, code)):
                payload_old = loads(row["payload_json"], {})
                if payload_old.get("collector") == collector_name:
                    existing = row
                    break
            if existing:
                self.db.run(
                    "UPDATE materials SET run_id=?, payload_json=?, platform=?, updated_at=? WHERE id=?",
                    (result["task_id"], dumps(payload), platform, now(), existing["id"]),
                )
            else:
                self._insert_material("collect", title, "", status, code, result["task_id"], payload)
        return result

    def run(self, run_id: str) -> dict:
        row = self.db.one("SELECT result_json FROM collect_runs WHERE id=?", (run_id,))
        if not row:
            raise Error("采集记录不存在", 404)
        return loads(row["result_json"], {})

    def workflows(self) -> list[dict]:
        return [self._workflow_view(row) for row in self.db.all("SELECT * FROM workflow_runs ORDER BY created_at DESC")]

    def workflow(self, workflow_id: str) -> dict:
        row = self.db.one("SELECT * FROM workflow_runs WHERE id=?", (workflow_id,))
        if not row:
            raise Error("任务不存在", 404)
        view = self._workflow_view(row)
        view["topics"] = self.topics(workflow_id)
        view["notes"] = [note for note in self.notes() if note["workflow_id"] == workflow_id]
        return view

    def open_workflow(self, material_ids: list[str]) -> dict:
        if not material_ids:
            raise Error("先选择至少一条可用素材")
        usable = []
        for material_id in material_ids:
            row = self.db.one("SELECT * FROM materials WHERE id=?", (material_id,))
            if not row:
                raise Error("素材不存在", 404)
            if row["status"] == "partial" and row["url"]:
                pass
            elif row["status"] != "ok":
                raise Error("失败或未完成的采集不能进入分析")
            payload = loads(row["payload_json"], {})
            if payload.get("login_free") is False:
                raise Error("这一条不是免登录结果，不能当作热点主路径")
            usable.append(row)
        workflow_id = new_id("wf")
        stamp = now()
        self.db.run(
            "INSERT INTO workflow_runs (id,step,state,artifacts_json,error,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (workflow_id, "analyze", "WAITING_INPUT", dumps({"material_ids": material_ids, "title": usable[0]["title"]}), None, stamp, stamp),
        )
        account = account_config()
        history = self._own_history()
        strategy = _strategy_line(self.db)
        facts = []
        for row in usable:
            payload = loads(row["payload_json"], {})
            heat, fit, reason, dimensions = _fit(payload, account, history, strategy)
            facts.append("%s：热度%s，平台 %s。" % (row["title"], heat, row["platform"] or payload.get("platform") or "未标"))
            for template, angle in CANDIDATES:
                self.db.run(
                    """INSERT INTO topics
                    (id,workflow_id,material_id,title,fit,fit_reason,status,plan_json,script,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        new_id("topic"),
                        workflow_id,
                        row["id"],
                        "%s｜%s" % (row["title"], angle),
                        fit,
                        "%s 切入：%s。" % (reason, angle),
                        "candidate",
                        dumps({"heat": heat, "dimensions": dimensions, "template": template, "angle_hint": angle}),
                        "",
                        stamp,
                        stamp,
                    ),
                )
        hits = retrieve(self.db, "选题方法 复盘 策略")
        report = {
            "facts": facts,
            "knowledge": ["《%s》" % item["title"] for item in hits] or ["知识库里还没有已确认的策略或复盘"],
            "judgment": "定位仍是待确定。适配标为中，是这一轮实验，不是长期方向。",
        }
        artifacts = {"material_ids": material_ids, "title": usable[0]["title"], "report": report}
        self.db.run("UPDATE workflow_runs SET artifacts_json=? WHERE id=?", (dumps(artifacts), workflow_id))
        return self.workflow(workflow_id)

    def open_workflow_quick(self, title: str) -> dict:
        title = str(title or "").strip()
        if not title:
            raise Error("文章主题不能为空")
        workflow_id = new_id("wf")
        topic_id = new_id("topic")
        stamp = now()
        self.db.run(
            "INSERT INTO workflow_runs (id,step,state,artifacts_json,error,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (workflow_id, "plan", "WAITING_INPUT", dumps({"title": title, "quick": True}), None, stamp, stamp),
        )
        account = account_config()
        self.db.run(
            """INSERT INTO topics
            (id,workflow_id,material_id,title,fit,fit_reason,status,plan_json,script,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                topic_id,
                workflow_id,
                "",
                title,
                "中",
                "一键成文：未绑定热点素材，按主题直接创作实验稿。",
                "candidate",
                dumps({"template": "经验分享", "angle_hint": title, "quick": True}),
                "",
                stamp,
                stamp,
            ),
        )
        self._touch_workflow(workflow_id, "plan", "WAITING_INPUT", {"topic_id": topic_id, "title": title})
        return self.workflow(workflow_id)

    def topics(self, workflow_id: str | None = None) -> list[dict]:
        if workflow_id:
            rows = self.db.all("SELECT * FROM topics WHERE workflow_id=? ORDER BY created_at", (workflow_id,))
        else:
            rows = self.db.all("SELECT * FROM topics ORDER BY created_at DESC")
        return [self._topic_view(row) for row in rows]

    def select_topic(self, topic_id: str) -> dict:
        row = self._topic_row(topic_id)
        if row.get("status") == "rejected":
            raise Error("已否决的选题不能直接选定")
        stamp = now()
        self.db.run(
            "UPDATE topics SET status='candidate', updated_at=? WHERE workflow_id=? AND status='selected'",
            (stamp, row["workflow_id"]),
        )
        self.db.run("UPDATE topics SET status='selected', updated_at=? WHERE id=?", (stamp, topic_id))
        self._touch_workflow(row["workflow_id"], "plan", "WAITING_INPUT", {"topic_id": topic_id, "title": row["title"]})
        return self._topic_view(self._topic_row(topic_id))

    def reject_topic(self, topic_id: str) -> dict:
        row = self._topic_row(topic_id)
        self.db.run("UPDATE topics SET status='rejected', updated_at=? WHERE id=?", (now(), topic_id))
        return self._topic_view(self._topic_row(topic_id))

    def rename_topic(self, topic_id: str, title: str) -> dict:
        title = title.strip()
        if not title:
            raise Error("标题不能为空")
        row = self._topic_row(topic_id)
        plan = loads(row["plan_json"], {})
        plan["title"] = title[:18]
        self.db.run(
            "UPDATE topics SET title=?, plan_json=?, updated_at=? WHERE id=?",
            (title, dumps(plan), now(), topic_id),
        )
        return self._topic_view(self._topic_row(topic_id))

    def latest_report(self) -> dict:
        row = self.db.one("SELECT artifacts_json FROM workflow_runs ORDER BY created_at DESC LIMIT 1")
        if not row:
            return {}
        report = loads(row["artifacts_json"], {}).get("report")
        return report if isinstance(report, dict) else {}

    def plan_topic(self, topic_id: str, template: str = "", page_count: int = 0) -> dict:
        row = self._topic_row(topic_id)
        account = account_config()
        chosen = template.strip() or str(loads(row["plan_json"], {}).get("template") or "") or _default_template(account)
        if chosen not in TEMPLATES:
            raise Error("模板只能是知识科普、教程步骤、观点分析或经验分享")
        spec = TEMPLATES[chosen]
        count = int(page_count or spec.get("page_count") or 4)
        if not 3 <= count <= 6:
            raise Error("图文需要 3 到 6 页")
        structure, messages = _sized(spec, count)
        existing = loads(row["plan_json"], {})
        title = (existing.get("title") or row["title"] or "未命名选题")[:18]
        plan = {
            "heat": existing.get("heat"),
            "dimensions": existing.get("dimensions") or {},
            "template": chosen,
            "audience": "会因为这个问题停下来的读者",
            "angle": row["title"],
            "view": "先看热度，再看是否符合当前账号，最后看自己做不做得出来",
            "difference": "只写自己的判断和步骤，不把别人的正文放进稿子",
            "title": title,
            "structure": structure,
            "page_count": count,
            "page_messages": messages,
            "page_texts": _page_texts(title, structure, messages, spec["cta"]),
            "cta": spec["cta"],
            "preferred_types": account["preferred_types"],
            "avoid": account["avoid"],
        }
        script = "\n".join(
            [
                "模板：%s" % chosen,
                "受众：%s" % plan["audience"],
                "角度：%s" % plan["angle"],
                "核心观点：%s" % plan["view"],
                "差异点：%s" % plan["difference"],
                "标题：%s" % plan["title"],
                "结构：" + " / ".join(plan["structure"]),
                "行动号召：%s" % plan["cta"],
            ]
        )
        self.db.run(
            "UPDATE topics SET plan_json=?, script=?, updated_at=? WHERE id=?",
            (dumps(plan), script, now(), topic_id),
        )
        self._touch_workflow(row["workflow_id"], "plan", "RUNNING", {"topic_id": topic_id})
        return self._topic_view(self._topic_row(topic_id))

    def draft_topic(
        self,
        topic_id: str,
        template: str = "",
        page_count: int = 0,
        *,
        use_llm: bool = False,
        quick_prefs: dict | None = None,
    ) -> dict:
        row = self._topic_row(topic_id)
        if (row.get("status") or "candidate") != "selected":
            raise Error("先选定这个选题，再生成草稿")
        if use_llm:
            return self._draft_topic_llm(row, template, page_count, quick_prefs or {})
        plan = loads(row["plan_json"], {})
        if template and template != plan.get("template") or page_count or not plan.get("page_texts"):
            self.plan_topic(topic_id, template, page_count)
            row = self._topic_row(topic_id)
            plan = loads(row["plan_json"], {})
        messages = list(plan.get("page_messages") or [])
        texts = list(plan.get("page_texts") or [])
        roles = list((TEMPLATES.get(plan.get("template") or "") or {}).get("roles") or [])
        while len(roles) < len(texts):
            roles.insert(-1 if roles else 0, "body")
        roles = roles[: len(texts)]
        if roles:
            roles[0] = "cover"
            roles[-1] = "end"
        pages = []
        for index, text in enumerate(texts):
            pages.append(
                {
                    "index": index + 1,
                    "role": roles[index] if index < len(roles) else "body",
                    "message": messages[index] if index < len(messages) else "",
                    "text": text,
                }
            )
        if not 3 <= len(pages) <= 6:
            raise Error("图文需要 3 到 6 页")
        note_id = new_id("note")
        stamp = now()
        body = "\n\n".join(page["text"] for page in pages)
        tags = ["小红书", plan.get("template") or "选题实验"]
        self.db.run(
            """INSERT INTO notes
            (id,topic_id,workflow_id,title,body,summary,tags_json,pages_json,version,publish_status,error,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                note_id,
                topic_id,
                row["workflow_id"],
                plan.get("title") or row["title"],
                body,
                plan.get("view") or "",
                dumps(tags),
                dumps(pages),
                1,
                "DRAFT",
                None,
                stamp,
                stamp,
            ),
        )
        self._touch_workflow(row["workflow_id"], "draft", "WAITING_INPUT", {"note_id": note_id})
        return self.note(note_id)

    def _draft_topic_llm(self, row: dict, template: str, page_count: int, prefs: dict) -> dict:
        from xhs_svc.quick_draft import generate_quick_draft

        topic_id = row["id"]
        count = max(3, min(6, int(page_count or 4)))
        chosen = template or loads(row.get("plan_json"), {}).get("template") or "经验分享"
        title = str(row.get("title") or "").split("｜")[0].strip()
        material_hint = ""
        material_id = str(row.get("material_id") or "")
        if material_id:
            mat = self.db.one("SELECT * FROM materials WHERE id=?", (material_id,))
            if mat:
                payload = loads(mat["payload_json"], {})
                bits = [str(mat["title"] or ""), str(payload.get("body") or "")]
                material_hint = "\n".join(b for b in bits if b).strip()
        generated = generate_quick_draft(
            self.db,
            title,
            prefs,
            template=chosen,
            page_count=count,
            material_hint=material_hint,
        )
        pages = generated["pages"]
        note_id = new_id("note")
        stamp = now()
        body = "\n\n".join(str(p.get("text") or "") for p in pages)
        tags = list(generated.get("tags") or ["小红书", chosen])
        note_title = str(generated.get("title") or title)
        summary = str(generated.get("summary") or "")
        self.db.run(
            """INSERT INTO notes
            (id,topic_id,workflow_id,title,body,summary,tags_json,pages_json,version,publish_status,error,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                note_id,
                topic_id,
                row["workflow_id"],
                note_title,
                body,
                summary,
                dumps(tags),
                dumps(pages),
                1,
                "DRAFT",
                None,
                stamp,
                stamp,
            ),
        )
        plan = loads(row.get("plan_json"), {})
        plan["llm_engine"] = generated.get("engine") or ""
        plan["quick_prefs"] = prefs
        self.db.run(
            "UPDATE topics SET plan_json=?, updated_at=? WHERE id=?",
            (dumps(plan), stamp, topic_id),
        )
        self._touch_workflow(
            row["workflow_id"],
            "draft",
            "WAITING_INPUT",
            {"note_id": note_id, "engine": generated.get("engine") or "llm"},
        )
        return self.note(note_id)

    def notes(self) -> list[dict]:
        return [self._note_view(row) for row in self.db.all("SELECT * FROM notes ORDER BY updated_at DESC")]

    def note(self, note_id: str) -> dict:
        row = self.db.one("SELECT * FROM notes WHERE id=?", (note_id,))
        if not row:
            raise Error("笔记不存在", 404)
        return self._note_view(row)

    def update_note(self, note_id: str, payload: dict) -> dict:
        current = self.note(note_id)
        pages = payload.get("pages") if isinstance(payload.get("pages"), list) else current["pages"]
        if not 3 <= len(pages) <= 6:
            raise Error("图文需要 3 到 6 页")
        title = str(payload.get("title") or current["title"]).strip()
        body = str(payload.get("body") or "\n\n".join(str(page.get("text") or "") for page in pages))
        version = int(current["version"]) + 1
        self.db.run(
            """UPDATE notes SET title=?, body=?, summary=?, tags_json=?, pages_json=?, version=?, publish_status='DRAFT', error=NULL, updated_at=?
               WHERE id=?""",
            (
                title,
                body,
                str(payload.get("summary") if "summary" in payload else current["summary"] or ""),
                dumps(payload.get("tags") if isinstance(payload.get("tags"), list) else current["tags"]),
                dumps(pages),
                version,
                now(),
                note_id,
            ),
        )
        self.db.run("UPDATE notes SET review_json=NULL WHERE id=?", (note_id,))
        self.db.run(
            "UPDATE approvals SET status='invalidated', updated_at=? WHERE note_id=? AND status='approved'",
            (now(), note_id),
        )
        return self.note(note_id)

    def render_visual(self, note_id: str) -> dict:
        current = self.note(note_id)
        if current["publish_status"] != "DRAFT":
            self.db.run(
                "UPDATE notes SET version=version+1, publish_status='DRAFT', review_json=NULL, updated_at=? WHERE id=?",
                (now(), note_id),
            )
            self.db.run(
                "UPDATE approvals SET status='invalidated', updated_at=? WHERE note_id=? AND status='approved'",
                (now(), note_id),
            )
            current = self.note(note_id)
        folder = self.data / "media" / note_id
        folder.mkdir(parents=True, exist_ok=True)
        pages = current["pages"]
        checks = []
        if len(current["title"]) > 20:
            checks.append({"item": "标题", "issue": "超过 20 个字"})
        cover = ""
        for page in pages:
            text = str(page.get("text") or "")
            if len(text) > 90:
                checks.append({"item": "第 %s 页" % page.get("index"), "issue": "文字可能溢出"})
            if not text.strip():
                checks.append({"item": "第 %s 页" % page.get("index"), "issue": "没有文字"})
            name = "cover.svg" if page.get("role") == "cover" or page.get("index") == 1 else "page-%s.svg" % page.get("index")
            (folder / name).write_text(_card_svg(page, current["title"]), encoding="utf-8")
            relative = "data/xhs/media/%s/%s" % (note_id, name)
            page["image"] = relative
            if name == "cover.svg":
                cover = relative
        if pages and not cover:
            cover = pages[0]["image"]
        direction = {
            "concept": "标题放在上三分之一，左侧一条色标区分封面和正文",
            "layout": "1080×1440，封面和正文同一套边框",
            "style": "工作台配色，无衬线。视觉方案和卡片是两步，卡片按页面数据套固定模板",
        }
        self.db.run(
            "UPDATE notes SET pages_json=?, updated_at=? WHERE id=?",
            (dumps(pages), now(), note_id),
        )
        self._touch_workflow(
            current["workflow_id"],
            "visual",
            "WAITING_INPUT",
            {"note_id": note_id, "checks": checks, "direction": direction},
        )
        view = self.note(note_id)
        view["checks"] = checks
        view["cover"] = cover
        view["direction"] = direction
        return view

    def generate_images(self, payload: dict) -> dict:
        theme = str(payload.get("theme") or "").strip()
        prompt = str(payload.get("prompt") or "").strip()
        if not prompt and theme:
            prompt = theme
        if not prompt:
            raise Error("请填写图片主题或画面提示词")
        if len(prompt) > 1000:
            raise Error("提示词不超过 1000 字")
        count = max(1, min(4, int(payload.get("count") or 1)))
        aspect = str(payload.get("aspect") or "3:4")
        sizes = {"3:4": (1080, 1440), "1:1": (1080, 1080), "4:3": (1440, 1080), "16:9": (1920, 1080)}
        width, height = sizes.get(aspect, (1080, 1440))
        batch = "gen-" + new_id()
        folder = self.data / "media" / batch
        folder.mkdir(parents=True, exist_ok=True)
        has_ref = bool(str(payload.get("reference") or "").strip().startswith("data:image"))
        images = []
        for index in range(count):
            name = "image-%s.svg" % (index + 1)
            svg = _prompt_svg(prompt, width, height, index + 1, count, has_ref, aspect, theme)
            (folder / name).write_text(svg, encoding="utf-8")
            images.append({"index": index + 1, "path": "data/xhs/media/%s/%s" % (batch, name)})
        return {"batch": batch, "images": images, "credits": count * 2, "aspect": aspect}

    def submit_note(self, note_id: str, checks: dict | None = None) -> dict:
        current = self.note(note_id)
        if current["publish_status"] not in {"DRAFT", "REVIEW", "REJECTED"}:
            raise Error("当前状态不能提交审核")
        if not current["title"].strip():
            raise Error("标题为空")
        if not 3 <= len(current["pages"]) <= 6:
            raise Error("图文需要 3 到 6 页")
        for page in current["pages"]:
            if not str(page.get("text") or "").strip():
                raise Error("还有空白页")
        incoming = checks if isinstance(checks, dict) else {}
        missing = [label for key, label in REVIEW if incoming.get(key) is not True]
        if missing:
            raise Error("审核还没通过：" + "、".join(missing))
        if not any(page.get("image") for page in current["pages"]):
            raise Error("先生成卡片，再确认图片这一项")
        self.db.run(
            "UPDATE notes SET publish_status='WAITING_APPROVAL', review_json=?, updated_at=? WHERE id=?",
            (dumps({key: True for key, _label in REVIEW}), now(), note_id),
        )
        self._touch_workflow(current["workflow_id"], "review", "WAITING_APPROVAL", {"note_id": note_id, "version": current["version"]})
        return self.note(note_id)

    def decide(self, note_id: str, version: int, decision: str) -> dict:
        current = self.note(note_id)
        if current["publish_status"] != "WAITING_APPROVAL":
            raise Error("只有待确认的笔记可以审批")
        if int(version) != int(current["version"]):
            raise Error("确认必须绑定当前版本")
        if decision not in {"approve", "reject"}:
            raise Error("决定只能是 approve 或 reject")
        status = "approved" if decision == "approve" else "rejected"
        stamp = now()
        self.db.run(
            "INSERT INTO approvals (id,note_id,version,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
            (new_id("apr"), note_id, int(version), status, stamp, stamp),
        )
        if decision == "reject":
            self.db.run("UPDATE notes SET publish_status='REJECTED', updated_at=? WHERE id=?", (stamp, note_id))
            self._touch_workflow(current["workflow_id"], "review", "REJECTED", {"note_id": note_id})
        return self.note(note_id)

    def publish(self, note_id: str) -> dict:
        current = self.note(note_id)
        approval = self.db.one(
            "SELECT * FROM approvals WHERE note_id=? AND version=? AND status='approved' ORDER BY created_at DESC LIMIT 1",
            (note_id, current["version"]),
        )
        if current["publish_status"] != "WAITING_APPROVAL" or not approval:
            raise Error("发布需要当前版本的人工确认")
        stamp = now()
        self.db.run("UPDATE notes SET publish_status='PUBLISHING', updated_at=? WHERE id=?", (stamp, note_id))
        status, detail = _call_mcp(current)
        self.db.run("UPDATE notes SET publish_status=?, error=?, updated_at=? WHERE id=?", (status, detail if status == "FAILED" else None, now(), note_id))
        self.db.run(
            "INSERT INTO publish_log (id,note_id,version,status,detail,created_at) VALUES (?,?,?,?,?,?)",
            (new_id("pub"), note_id, current["version"], status, detail, now()),
        )
        self._touch_workflow(current["workflow_id"], "publish", "COMPLETED" if status == "PUBLISHED" else "FAILED", {"note_id": note_id, "detail": detail})
        return self.note(note_id)

    def add_metrics(self, note_id: str, payload: dict) -> dict:
        self.note(note_id)
        numbers = {}
        for key in ("exposure", "reads", "likes", "collects", "comments", "followers"):
            value = payload.get(key)
            numbers[key] = None if value is None or value == "" else int(value)
        self.db.run(
            """INSERT INTO note_metrics
            (id,note_id,exposure,reads,likes,collects,comments,followers,recorded_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                new_id("metric"),
                note_id,
                numbers["exposure"],
                numbers["reads"],
                numbers["likes"],
                numbers["collects"],
                numbers["comments"],
                numbers["followers"],
                now(),
            ),
        )
        return {"note_id": note_id, "metrics": self.metrics(note_id)}

    def metrics(self, note_id: str) -> list[dict]:
        return self.db.all(
            "SELECT exposure,reads,likes,collects,comments,followers,recorded_at FROM note_metrics WHERE note_id=? ORDER BY recorded_at DESC",
            (note_id,),
        )

    def top_collects(self, limit: int = 10) -> list[dict]:
        return self.db.all(
            """SELECT n.id, n.title, m.collects, m.likes, m.reads, m.exposure, m.recorded_at
               FROM note_metrics m JOIN notes n ON n.id=m.note_id
               WHERE m.collects IS NOT NULL
               ORDER BY m.collects DESC, m.recorded_at DESC LIMIT ?""",
            (limit,),
        )

    def library_videos(self) -> dict:
        items: list[dict] = []
        seen: set[str] = set()

        def add_video(rel: str, title: str, source: str, url: str = "", created_at: str = "") -> None:
            rel = str(rel or "").replace("\\", "/").lstrip("/")
            if not rel or rel in seen or ".." in rel.split("/"):
                return
            target = (workspace_root() / rel).resolve()
            if not target.is_file() or target.suffix.lower() not in VIDEO_SUFFIXES:
                return
            if not target.is_relative_to(self.data.resolve()):
                return
            seen.add(rel)
            stat = target.stat()
            items.append(
                {
                    "title": str(title or target.stem),
                    "path": rel,
                    "source": source,
                    "url": str(url or ""),
                    "size_bytes": stat.st_size,
                    "created_at": str(created_at or ""),
                    "name": target.name,
                }
            )

        for row in self.db.all("SELECT title, url, payload_json, created_at FROM materials ORDER BY created_at DESC"):
            payload = loads(row["payload_json"], {})
            base_title = str(row.get("title") or "")
            material_url = str(row.get("url") or "")
            stamp = str(row.get("created_at") or "")
            for media in payload.get("media_files") or []:
                rel = str(media.get("relative_path") or "")
                mtype = str(media.get("type") or "").lower()
                if mtype == "video" or Path(rel).suffix.lower() in VIDEO_SUFFIXES:
                    add_video(rel, base_title, "archive", material_url, stamp)

        for path in self.data.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES:
                rel = "data/xhs/" + path.relative_to(self.data).as_posix()
                add_video(rel, path.stem, "disk")

        items.sort(key=lambda row: (row.get("created_at") or "", row.get("name") or ""), reverse=True)
        return {"videos": items, "total": len(items)}

    def write_review(self, note_id: str) -> dict:
        current = self.note(note_id)
        rows = self.metrics(note_id)
        if not rows:
            raise Error("先录入这篇笔记自己的指标")
        latest = rows[0]
        folder = self.data / "knowledge" / "inbox" / "pending"
        folder.mkdir(parents=True, exist_ok=True)
        rel = "inbox/pending/review-%s.md" % note_id
        path = self.data / "knowledge" / rel
        path.write_text(
            "\n".join(
                [
                    "---",
                    "id: review-%s" % note_id,
                    "type: review",
                    "title: \"%s 的复盘\"" % str(current["title"]).replace('"', ""),
                    "created_at: %s" % now()[:10],
                    "status: pending",
                    "tags:",
                    "  - 复盘",
                    "---",
                    "",
                    "# 复盘",
                    "",
                    "这篇笔记的曝光 %s，阅读 %s，点赞 %s，收藏 %s，评论 %s，涨粉 %s。"
                    % (latest["exposure"], latest["reads"], latest["likes"], latest["collects"], latest["comments"], latest.get("followers")),
                    "",
                    _compare(current, latest, self.top_collects(10)),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self._touch_workflow(current["workflow_id"], "retro", "WAITING_INPUT", {"review": rel})
        return {"path": rel, "status": "pending"}

    def write_case(self, note_id: str) -> dict:
        current = self.note(note_id)
        folder = self.data / "knowledge" / "inbox" / "pending"
        folder.mkdir(parents=True, exist_ok=True)
        rel = "inbox/pending/case-%s.md" % note_id
        metrics = current["metrics"][0] if current["metrics"] else {}
        (self.data / "knowledge" / rel).write_text(
            "\n".join(
                [
                    "---",
                    "id: case-%s" % note_id,
                    "type: case",
                    "title: \"%s 的案例\"" % str(current["title"]).replace('"', ""),
                    "created_at: %s" % now()[:10],
                    "status: pending",
                    "tags:",
                    "  - 案例",
                    "---",
                    "",
                    "# 案例",
                    "",
                    "标题：%s" % current["title"],
                    "摘要：%s" % (current["summary"] or "还没有摘要"),
                    "标签：%s" % "、".join(current["tags"] or []),
                    "收藏：%s" % metrics.get("collects", "未录入"),
                    "",
                    "这是本账号这篇笔记的结构记录。不收录他人正文。",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {"path": rel, "status": "pending"}

    def write_cycle(self) -> dict:
        lines = ["# 周期报告", "", "下面是观察，不是规律。依据只包括本账号已经录入指标的笔记。", ""]
        count = 0
        for note in self.notes():
            if not note["metrics"]:
                continue
            count += 1
            latest = note["metrics"][0]
            lines.append("- 《%s》收藏 %s，点赞 %s，模板 %s。" % (note["title"], latest["collects"], latest["likes"], "、".join(note["tags"] or [])))
        if not count:
            raise Error("还没有本账号指标，写不出周期报告")
        folder = self.data / "knowledge" / "inbox" / "pending"
        folder.mkdir(parents=True, exist_ok=True)
        rel = "inbox/pending/cycle.md"
        (self.data / "knowledge" / rel).write_text(
            "\n".join(
                [
                    "---",
                    "id: cycle",
                    "type: report",
                    "title: \"本账号周期报告\"",
                    "created_at: %s" % now()[:10],
                    "status: pending",
                    "tags:",
                    "  - 复盘",
                    "---",
                    "",
                    *lines,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {"path": rel, "status": "pending"}

    def turns(self) -> list[dict]:
        return self.db.all("SELECT role, text, engine, href, created_at FROM turns ORDER BY created_at")

    def add_turn(self, role: str, text: str, engine: str = "", href: str = "") -> None:
        self.db.run(
            "INSERT INTO turns (id,role,text,engine,href,created_at) VALUES (?,?,?,?,?,?)",
            (new_id("turn"), role, text, engine or None, href or None, now()),
        )

    def _find_duplicate(self, url: str, payload: dict):
        url = str(url or "").strip()
        if url:
            found = self.db.one("SELECT * FROM materials WHERE url=?", (url,))
            if found:
                return found
        note_id = str((payload or {}).get("note_id") or "").strip()
        if not note_id:
            return None
        for row in self.db.all("SELECT * FROM materials"):
            if str(loads(row["payload_json"], {}).get("note_id") or "") == note_id:
                return row
        return None

    def _merge_material(self, existing: dict, title: str, url: str, status: str, error_code, run_id, payload: dict) -> dict:
        if existing["status"] == "ok" and status != "ok":
            return self._material_view(existing)
        self.db.run(
            """UPDATE materials SET origin=?, platform=?, title=?, url=?, body=?, status=?, error_code=?, run_id=?, payload_json=?, updated_at=?
               WHERE id=?""",
            (
                existing["origin"] if status == "ok" and existing["origin"] == "manual" else existing["origin"],
                payload.get("platform") or existing["platform"],
                title,
                url,
                payload.get("body") if isinstance(payload, dict) else existing["body"],
                status,
                error_code,
                run_id,
                dumps(payload),
                now(),
                existing["id"],
            ),
        )
        row = self.db.one("SELECT * FROM materials WHERE id=?", (existing["id"],))
        return self._material_view(row)

    def _own_history(self) -> str:
        rows = self.top_collects(3)
        if not rows:
            return "指标表里还没有本账号样本，不套用别人的爆款"
        bits = ["《%s》收藏 %s" % (row["title"], row["collects"]) for row in rows]
        return "本账号已有记录：" + "，".join(bits)

    def _direction(self, workflow_id: str | None) -> dict:
        if not workflow_id:
            return {}
        row = self.db.one("SELECT artifacts_json FROM workflow_runs WHERE id=?", (workflow_id,))
        artifacts = loads(row["artifacts_json"], {}) if row else {}
        direction = artifacts.get("direction")
        return direction if isinstance(direction, dict) else {}

    def _insert_material(self, origin, title, url, status, error_code, run_id, payload) -> dict:
        stamp = now()
        material_id = new_id("mat")
        platform = payload.get("platform") if isinstance(payload, dict) else ""
        if platform in {"xiaohongshu", "xhs"}:
            platform = "小红书"
        self.db.run(
            """INSERT INTO materials
            (id,origin,platform,title,url,body,status,error_code,run_id,payload_json,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                material_id,
                origin,
                platform,
                title,
                url,
                payload.get("body") if isinstance(payload, dict) else "",
                status,
                error_code,
                run_id,
                dumps(payload),
                stamp,
                stamp,
            ),
        )
        row = self.db.one("SELECT * FROM materials WHERE id=?", (material_id,))
        return self._material_view(row)

    def _topic_row(self, topic_id: str) -> dict:
        row = self.db.one("SELECT * FROM topics WHERE id=?", (topic_id,))
        if not row:
            raise Error("选题不存在", 404)
        return row

    def _touch_workflow(self, workflow_id: str | None, step: str, state: str, artifact: dict) -> None:
        if not workflow_id:
            return
        row = self.db.one("SELECT artifacts_json FROM workflow_runs WHERE id=?", (workflow_id,))
        artifacts = loads(row["artifacts_json"], {}) if row else {}
        artifacts.update(artifact)
        artifacts["step"] = step
        self.db.run(
            "UPDATE workflow_runs SET step=?, state=?, artifacts_json=?, updated_at=? WHERE id=?",
            (step, state, dumps(artifacts), now(), workflow_id),
        )

    def _material_view(self, row: dict) -> dict:
        payload = loads(row["payload_json"], {})
        return {
            "id": row["id"],
            "origin": row["origin"],
            "title": row["title"],
            "url": row["url"],
            "status": row["status"],
            "error_code": row["error_code"],
            "run_id": row["run_id"],
            "platform": row["platform"] or payload.get("platform") or "",
            "kind": payload.get("kind") or "",
            "note_id": payload.get("note_id") or "",
            "error": (
                (payload.get("error") or {}).get("message")
                if isinstance(payload.get("error"), dict)
                else str(payload.get("error") or "")
            ),
            "login_free": payload.get("login_free", True) if row["status"] == "ok" else False,
            "collector": payload.get("collector") or "",
            "feed_channel": payload.get("feed_channel") or "",
            "search_keyword": payload.get("search_keyword") or "",
            "created_at": row["created_at"],
        }

    def _topic_view(self, row: dict) -> dict:
        source = self.db.one("SELECT title, url, platform FROM materials WHERE id=?", (row["material_id"],)) if row["material_id"] else None
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "material_id": row["material_id"],
            "title": row["title"],
            "status": row.get("status") or "candidate",
            "fit": row["fit"],
            "fit_reason": row["fit_reason"],
            "plan": loads(row["plan_json"], {}),
            "script": row["script"],
            "source": {"title": source["title"], "url": source["url"], "platform": source["platform"]} if source else {},
            "created_at": row["created_at"],
        }

    def _note_view(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "topic_id": row["topic_id"],
            "workflow_id": row["workflow_id"],
            "title": row["title"],
            "body": row["body"],
            "summary": row["summary"],
            "tags": loads(row["tags_json"], []),
            "pages": loads(row["pages_json"], []),
            "version": row["version"],
            "publish_status": row["publish_status"],
            "error": row["error"],
            "metrics": self.metrics(row["id"]),
            "review": loads(row.get("review_json"), {}),
            "direction": self._direction(row["workflow_id"]),
            "publish_log": self.db.all(
                "SELECT version, status, detail, created_at FROM publish_log WHERE note_id=? ORDER BY created_at DESC",
                (row["id"],),
            ),
            "updated_at": row["updated_at"],
        }

    def _workflow_view(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "step": row["step"],
            "state": row["state"],
            "artifacts": loads(row["artifacts_json"], {}),
            "error": row["error"],
            "updated_at": row["updated_at"],
        }


def _call_mcp(note: dict) -> tuple[str, str]:
    url = os.environ.get("XHS_MCP_URL", "").strip()
    if not url:
        return "FAILED", "本机小红书 MCP 未配置，发布没有执行"
    body = json.dumps(
        {"note_id": note["id"], "version": note["version"], "title": note["title"], "pages": note["pages"]},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return "FAILED", "发布失败：%s" % exc
    link = ""
    try:
        parsed = json.loads(raw) if raw else {}
        if isinstance(parsed, dict):
            link = str(parsed.get("url") or parsed.get("note_url") or "")
    except json.JSONDecodeError:
        link = ""
    detail = "已交给本机 MCP"
    if link:
        detail += "。链接：" + link
    return "PUBLISHED", detail


def _xml(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TEMPLATES = {
    "知识科普": {
        "structure": ["问题", "判断标准", "一个例子", "下一步"],
        "messages": ["抛出要讲的问题", "给出可判断的标准", "用自己的例子说明", "留一个可执行的下一步"],
        "roles": ["cover", "body", "body", "end"],
        "cta": "评论区留一个你正在判断的具体问题",
        "extras": [("常见误解", "写一个容易看错的点"), ("不适用", "写明什么时候不要用这个判断")],
    },
    "教程步骤": {
        "structure": ["要完成的事", "第一步", "第二步", "如何检查"],
        "messages": ["先说做成什么样", "这一步只做一件事", "下一步只做一件事", "做完后怎么判断对了"],
        "roles": ["cover", "body", "body", "end"],
        "cta": "按这两步做完，把结果留在评论区",
        "extras": [("准备", "开始前要有什么"), ("卡住时", "这一步失败了怎么退回")],
    },
    "观点分析": {
        "structure": ["观点", "依据", "边界", "结论"],
        "messages": ["先写自己的判断", "依据来自这次观察", "这个判断不覆盖什么", "读者可以怎么用"],
        "roles": ["cover", "body", "body", "end"],
        "cta": "如果判断不同，评论区补一条你的依据",
        "extras": [("反例", "写一个不成立的情况"), ("怎么用", "读者下一步可以做什么")],
    },
    "经验分享": {
        "structure": ["场景", "做法", "结果", "可复用的一点"],
        "messages": ["当时遇到什么", "自己实际做了什么", "结果是什么", "别人能直接拿走的一点"],
        "roles": ["cover", "body", "body", "end"],
        "cta": "下次遇到同类场景，先用这一点",
        "extras": [("当时没做的", "写一个刻意没做的选择"), ("下次", "下一次先改哪一件")],
    },
}

REVIEW = (
    ("facts", "事实"),
    ("originality", "原创"),
    ("quality", "内容质量"),
    ("images", "图片"),
    ("layout", "排版"),
    ("title", "标题"),
    ("rules", "平台规则"),
)

PREFERRED = {"教程": "教程步骤", "经验分享": "经验分享", "知识科普": "知识科普", "工具测评": "观点分析"}


def _default_template(account: dict) -> str:
    for name in account.get("preferred_types") or []:
        if name in PREFERRED:
            return PREFERRED[name]
    return "知识科普"


def _page_texts(title: str, structure: list[str], messages: list[str], cta: str) -> list[str]:
    texts = [title]
    for index in range(1, len(structure) - 1):
        texts.append("%s。%s" % (structure[index], messages[index]))
    texts.append(cta)
    return texts


def _sized(spec: dict, count: int) -> tuple[list[str], list[str]]:
    structure = list(spec["structure"])
    messages = list(spec["messages"])
    extras = list(spec.get("extras") or [])
    while len(structure) < count and extras:
        name, message = extras.pop(0)
        structure.insert(-1, name)
        messages.insert(-1, message)
    return structure[:count], messages[:count]


def _strategy_line(db) -> str:
    hits = retrieve(db, "运营策略 复盘")
    if not hits:
        return "还没有已确认的策略"
    return "已确认：《%s》" % hits[0]["title"]


def _compare(note: dict, latest: dict, rows: list[dict]) -> str:
    others = [row for row in rows if row["id"] != note["id"]]
    if not others:
        return "观察：指标表里还没有其他本账号笔记，这里只描述这一篇，不推断成通用规律。"
    other = others[0]
    left = latest.get("collects") or 0
    right = other.get("collects") or 0
    relation = "更高" if left > right else "不高"
    return "假设：这篇收藏相对《%s》%s。依据只是这两篇已录入的收藏数，标签是 %s。" % (
        other["title"],
        relation,
        "、".join(note.get("tags") or []) or "未标模板",
    )


def _prompt_svg(prompt: str, width: int, height: int, index: int, total: int, has_ref: bool, aspect: str, theme: str = "") -> str:
    snippet = _xml(prompt[:220] + ("…" if len(prompt) > 220 else ""))
    ref_note = "已挂参考图 · 主体一致" if has_ref else "提示词生图"
    theme_line = _svg_lines(_xml(theme), 40, 88, 160, "#1f6f62", 22) if theme else ""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%%" stop-color="#e8f0ec"/><stop offset="100%%" stop-color="#f6f5f1"/></linearGradient></defs>
<rect width="%s" height="%s" fill="url(#bg)"/>
<rect x="48" y="48" width="%s" height="%s" rx="24" fill="#ffffff" stroke="#c5d6cf"/>
<rect x="48" y="48" width="14" height="%s" fill="#1f6f62"/>
<text x="88" y="120" fill="#1f6f62" font-size="26" font-family="sans-serif">%s · %s · %s/%s</text>
%s
%s
</svg>""" % (
        width,
        height,
        width,
        height,
        width,
        height,
        width - 96,
        height - 96,
        height - 96,
        ref_note,
        _xml(aspect),
        index,
        total,
        theme_line,
        _svg_lines(snippet, 34, 88, theme and 260 or 200, "#24332c", 28),
    )


def _card_svg(page: dict, title: str) -> str:
    role = {"cover": "封面", "end": "结尾"}.get(page.get("role"), "正文")
    headline = title if page.get("role") == "cover" else str(page.get("message") or role)
    body = str(page.get("text") or "")
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">
<rect width="1080" height="1440" fill="#f6f5f1"/>
<rect x="64" y="64" width="952" height="1312" rx="28" fill="#ffffff" stroke="#d9e3df"/>
<rect x="64" y="64" width="18" height="1312" fill="#1f6f62"/>
<text x="120" y="180" fill="#1f6f62" font-size="28" font-family="sans-serif">%s · 第 %s 页</text>
%s
%s
</svg>""" % (
        _xml(role),
        page.get("index") or "",
        _svg_lines(headline, 56, 120, 300, "#24332c", 14),
        _svg_lines(body, 36, 120, 520, "#3d4a46", 18),
    )


def _svg_lines(text: str, size: int, x: int, y: int, fill: str, width: int) -> str:
    raw = str(text)
    lines = [raw[i : i + width] for i in range(0, len(raw), width)] or [""]
    gap = int(size * 1.35)
    return "\n".join(
        '<text x="%s" y="%s" fill="%s" font-size="%s" font-family="sans-serif">%s</text>'
        % (x, y + index * gap, fill, size, _xml(line))
        for index, line in enumerate(lines[:8])
    )


PLATFORMS = ("小红书", "抖音", "哔哩哔哩", "微博", "知乎", "人工")
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v", ".mkv", ".avi"}
KINDS = ("链接", "截图说明", "文案", "竞品账号")
CANDIDATES = (
    ("知识科普", "用判断标准讲清楚"),
    ("教程步骤", "拆成可以照做的步骤"),
    ("观点分析", "先写判断再写边界"),
    ("经验分享", "用自己的一次经历"),
    ("观点分析", "对比两种做法"),
)


def _fit(payload: dict, account: dict, history: str, strategy: str) -> tuple[str, str, str, dict]:
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    likes = metrics.get("like_count")
    if likes is None:
        heat = "未知"
    elif likes >= 1000:
        heat = "高"
    elif likes >= 100:
        heat = "中"
    else:
        heat = "低"
    positioning = account.get("positioning") or "待确定"
    fit = "中"
    reason = "热度%s。账号定位是「%s」，这一轮只做小规模实验，稿子不使用素材里的他人正文。" % (heat, positioning)
    dimensions = {
        "heat": heat,
        "account_match": "待验证" if positioning == "待确定" else "按配置匹配",
        "own_history": history,
        "strategy": strategy,
        "difference": "用自己的判断重写",
        "cost": "图文 4 页，可在一次编辑里完成",
    }
    return heat, fit, reason, dimensions
