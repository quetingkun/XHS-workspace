from __future__ import annotations

import json
import re

from xhs_svc.chat import answer
from xhs_svc.config import workspace_root


_QUICK_SKILL_IDS = (
    "xhs-quick-workflow",
    "xhs-content",
    "xhs-writer",
    "xhs-strategy",
    "xhs-analysis",
)


def load_quick_skills() -> str:
    root = workspace_root() / "services" / "xhs" / "skills"
    blocks: list[str] = []
    for skill_id in _QUICK_SKILL_IDS:
        path = root / skill_id / "SKILL.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            blocks.append("### %s\n%s" % (skill_id, text))
    return "\n\n".join(blocks)


def build_quick_draft_prompt(
    topic_title: str,
    prefs: dict,
    *,
    template: str,
    page_count: int,
    material_hint: str = "",
) -> str:
    skill = load_quick_skills()
    persona = str(prefs.get("persona") or "自然写作")
    word_count = int(prefs.get("wordCount") or 800)
    deai = str(prefs.get("deai") or "开启")
    extra = str(prefs.get("extra") or "").strip()
    pages = max(3, min(6, int(page_count or 4)))
    parts = [
        "【一键成文 · 小红书图文草稿】",
        "请按下方运营 Skills（xhs-writer / xhs-strategy / xhs-content 等）与知识库约束，"
        "通过 agent-core xhs_ops 生成可进入改稿阶段的结构化草稿。",
        "禁止抄袭素材中的他人正文；找不到的知识不要编造。",
        "",
        "选题：" + topic_title.strip(),
        "模板倾向：" + (template or "经验分享"),
        "写作人格：" + persona,
        "目标总字数约：" + str(word_count) + "（可 ±15%）",
        "去 AI 味：" + deai,
        "分页数量：" + str(pages) + " 页（必须 3–6 页）",
    ]
    if material_hint:
        parts.extend(["", "背景素材（仅作参考，不可整段抄袭）：", material_hint[:2000]])
    if extra:
        parts.extend(["", "用户补充要求：", extra])
    if skill:
        parts.extend(["", "技能说明：", skill])
    parts.extend(
        [
            "",
            "请只输出一个 JSON 对象，不要 Markdown 代码围栏外的解释。格式：",
            '{"title":"≤20字标题","summary":"一句话摘要","tags":["标签1","标签2"],"pages":[',
            '  {"index":1,"role":"cover","message":"封面信息点","text":"封面页文案≤90字"},',
            '  {"index":2,"role":"body","message":"要点","text":"..."}',
            ']}',
            "pages 每项 text 为口语化小红书笔记用语，单页不超过 120 字。",
        ]
    )
    return "\n".join(parts)


def parse_draft_json(text: str) -> dict:
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("模型返回为空")
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("草稿 JSON 不是对象")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("缺少 pages")
    out_pages = []
    for item in pages:
        if not isinstance(item, dict):
            continue
        text_val = str(item.get("text") or "").strip()
        if not text_val:
            continue
        out_pages.append(
            {
                "index": int(item.get("index") or len(out_pages) + 1),
                "role": str(item.get("role") or "body"),
                "message": str(item.get("message") or ""),
                "text": text_val,
            }
        )
    if not 3 <= len(out_pages) <= 6:
        raise ValueError("分页需 3–6 页，当前 %s 页" % len(out_pages))
    if out_pages:
        out_pages[0]["role"] = "cover"
        out_pages[-1]["role"] = "end"
    title = str(data.get("title") or "").strip()
    if not title:
        raise ValueError("缺少标题")
    tags = data.get("tags")
    if not isinstance(tags, list):
        tags = ["小红书"]
    tags = [str(t).strip() for t in tags if str(t).strip()][:8]
    summary = str(data.get("summary") or "").strip()
    return {"title": title, "summary": summary, "tags": tags, "pages": out_pages}


def generate_quick_draft(db, topic_title: str, prefs: dict, *, template: str, page_count: int, material_hint: str = "") -> dict:
    prompt = build_quick_draft_prompt(
        topic_title,
        prefs,
        template=template,
        page_count=page_count,
        material_hint=material_hint,
    )
    session_id = "xhs-quick-" + re.sub(r"[^a-zA-Z0-9_-]", "", topic_title)[:24]
    result = answer(
        db,
        prompt,
        use_knowledge=True,
        use_web=False,
        mode="general",
        session_id=session_id or "xhs-quick-draft",
    )
    engine = result.get("engine") or ""
    text = str(result.get("answer") or "").strip()
    if not text:
        raise RuntimeError("对话模型未返回内容（引擎 %s）" % (engine or "未知"))
    try:
        parsed = parse_draft_json(text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("无法解析模型草稿 JSON：%s" % exc) from exc
    parsed["engine"] = engine
    return parsed