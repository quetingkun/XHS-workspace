from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from xhs_svc.config import workspace_root
from xhs_svc.knowledge import retrieve


SYSTEM = """你是个人小红书账号的运营助手。
知识库摘录、本次采集结果和你自己的判断要分开说。
采集状态不是 ok 或 partial 的内容不能说成热点。模拟数据不能说成真实笔记。
找不到资料时直接说明没找到，不要编造选题方法或数据。
不要建议绕过验证码、维护 Cookie，也不要把别人的正文写进待发布稿。
发布必须等这个版本被人工确认。"""


def step_href(prompt: str) -> str:
    rules = (
        (("打开设置", "模型设置", "配置模型", "配置向量", "模型配置"), "/settings"),
        (("系统设置", "采集配置"), "/system"),
        (("打开知识库", "去知识库", "书架"), "/library/shelf"),
        (("视频库", "看视频", "归档视频"), "/library/videos"),
        (("AI助手", "问询", "助手", "问答"), "/tools/ask"),
        (("复盘",), "/tools/review"),
        (("指标", "收藏", "涨粉", "数据跟踪"), "/tools/metrics"),
        (("发布",), "/create/article?step=6"),
        (("封面", "视觉", "配图", "卡片", "成图", "生图"), "/create/visual"),
        (("草稿", "草稿箱"), "/library/drafts"),
        (("一键成文", "成文"), "/create/article"),
        (("文案", "选题", "适配"), "/create/article"),
        (("热点", "素材", "采集", "当日热点"), "/hot/today"),
        (("新闻", "爆点"), "/hot/news"),
    )
    for words, href in rules:
        if any(word in prompt for word in words):
            return href
    return ""


def _history_block(history: list[dict] | None) -> str:
    if not history:
        return ""
    lines: list[str] = []
    for row in history[-8:]:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "")
        content = str(row.get("content") or row.get("text") or "").strip()
        if not content:
            continue
        label = "用户" if role == "user" else "助手"
        lines.append("%s：%s" % (label, content[:1200]))
    if not lines:
        return ""
    return "【同一会话此前几轮】\n" + "\n".join(lines) + "\n\n"


def answer(
    db,
    prompt: str,
    workflow_note: str = "",
    *,
    use_knowledge: bool = True,
    use_web: bool = False,
    mode: str = "general",
    session_id: str = "",
    history: list[dict] | None = None,
) -> dict:
    events: list[str] = []
    sources = retrieve(db, prompt) if use_knowledge else []
    skills = _skills(prompt)
    excerpt = _excerpt_block(sources) if use_knowledge else ""
    user = prompt.strip()
    hist = _history_block(history)
    if hist:
        user = hist + "【本轮问题】\n" + user
    if workflow_note:
        user += "\n\n当前任务：\n" + workflow_note
    if use_knowledge:
        if excerpt:
            user += "\n\n知识库摘录：\n" + excerpt
            events.append("mcp__knowledge__search")
        else:
            user += "\n\n知识库摘录：没有命中。请说明没找到，不要编造。"
    else:
        user += "\n\n【本轮未启用知识库检索】请基于常识作答，并标明不确定之处。"
    if use_web:
        from xhs_svc.web_search import web_search_text

        web_body, web_err = web_search_text(prompt)
        if web_body:
            user += "\n\n联网检索摘要（需人工核实，不可当作已确认事实）：\n" + web_body
            events.append("mcp__web_search__search")
        else:
            user += "\n\n联网检索：" + (web_err or "无结果")
    if mode == "xhs_soft":
        user += (
            "\n\n【输出要求 · 小红书软文】"
            "请输出：1）标题建议（≤20字）；2）一句话摘要；3）3–6 页分镜要点（每页口语化，单页≤90字）；"
            "4）3–5个标签。语气自然、适合图文笔记，不整段抄袭知识库原文，不确定的事实标注「待核实」。"
        )
    if skills:
        user += "\n\n适用技能：\n" + skills

    remote = _agent_core(user, use_knowledge=use_knowledge, use_web=use_web, session_id=session_id)
    if remote:
        merged_events = list(dict.fromkeys(events + list(remote.get("events") or [])))
        return {
            "answer": remote["answer"],
            "sources": sources,
            "engine": remote["engine"],
            "events": merged_events,
            "mode": mode,
            "use_knowledge": use_knowledge,
            "use_web": use_web,
        }
    direct, model_note = _direct_model(user)
    if direct:
        if use_knowledge and "mcp__knowledge__search" not in events:
            events.append("mcp__knowledge__search")
        return {
            "answer": direct,
            "sources": sources,
            "engine": "workspace-model",
            "events": events,
            "mode": mode,
            "use_knowledge": use_knowledge,
            "use_web": use_web,
        }
    if not use_knowledge or not sources:
        text = "知识库未启用或没有找到相关文档。" if not use_knowledge else "知识库里没有找到与这个问题相关的文档。"
        if model_note:
            text = model_note + "\n\n" + text
    else:
        hint = model_note or (
            "agent-core 未响应或对话模型未成功调用。请在设置页点「连接测试」；"
            "若用 Docker，请确认 deploy/.env 的 OPENAI_* 与容器可访问外网。"
            "下面只根据已确认的知识库原文整理。"
        )
        lines = [hint, ""]
        for source in sources:
            lines.append("《%s》" % source["title"])
            lines.append(source["excerpt"])
            kind = "向量" if source.get("match") == "embedding" else "关键词"
            lines.append("来源：%s（%s）" % (source["path"], kind))
            lines.append("")
        text = "\n".join(lines).strip()
        events.append("mcp__knowledge__search")
    return {
        "answer": text,
        "sources": sources,
        "engine": "local-excerpt",
        "events": events,
        "mode": mode,
        "use_knowledge": use_knowledge,
        "use_web": use_web,
    }


def _excerpt_block(sources: list[dict]) -> str:
    blocks = []
    for source in sources:
        blocks.append("文档：%s\n路径：%s\n%s" % (source["title"], source["path"], source["excerpt"]))
    return "\n\n".join(blocks)


def _skills(prompt: str) -> str:
    root = workspace_root() / "services" / "xhs" / "skills"
    catalog = [
        ("xhs-research", ("热点", "素材", "采集")),
        ("xhs-analysis", ("适配", "选题", "分析")),
        ("xhs-strategy", ("选题", "标题", "策略", "定位")),
        ("xhs-content", ("文案", "标题", "脚本", "正文")),
        ("xhs-writer", ("成文", "草稿", "软文", "笔记")),
        ("xhs-quick-workflow", ("一键", "成文", "创作", "工作流")),
        ("xhs-design", ("封面", "视觉", "配图", "卡片")),
        ("xhs-review", ("复盘", "审核", "发布", "指标")),
    ]
    picked = []
    for name, words in catalog:
        if any(word in prompt for word in words):
            path = root / name / "SKILL.md"
            if path.is_file():
                picked.append(path.read_text(encoding="utf-8")[:2000])
        if len(picked) >= 3:
            break
    return "\n\n".join(picked)


def _agent_core(user: str, use_knowledge: bool = True, use_web: bool = False, session_id: str = "") -> dict | None:
    base = os.environ.get("AGENT_CORE_URL", "http://127.0.0.1:8081").rstrip("/")
    flags = ""
    if use_knowledge:
        flags += "[知识库检索:开启]\n"
    else:
        flags += "[知识库检索:关闭]\n"
    if use_web:
        flags += "[联网搜索:开启]\n"
    kb_ids = ["kb_xhs"] if use_knowledge else []
    payload = {
        "function_id": "xhs_ops",
        "prompt": SYSTEM + "\n\n" + flags + user,
        "context": {"knowledge_base_ids": kb_ids},
    }
    sid = str(session_id or "").strip()
    if sid:
        payload["session_id"] = sid
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + "/v1/agent-turns",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    try:
        with urllib.request.urlopen(request, timeout=_agent_turn_timeout()) as response:
            engine = response.headers.get("X-Engine") or "agent-core"
            raw = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None  # 回落 workspace 直连模型
    chunks = []
    failed = ""
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        payload = event.get("payload") or {}
        if kind == "model.output.delta":
            chunks.append(str(payload.get("delta") or ""))
        elif kind == "turn.completed" and not chunks:
            chunks.append(str(payload.get("final_message") or ""))
        elif kind in {"error", "turn.failed"}:
            failed = str(payload.get("message") or failed)
    text = "".join(chunks).strip()
    if not text:
        return None
    if failed and not text:
        return None
    out_events = ["mcp__knowledge__search"] if use_knowledge else []
    if use_web:
        out_events.append("mcp__web_search__search")
    return {"answer": text, "engine": engine, "events": out_events}


def _openai_base_url(base: str) -> str:
    base = str(base or "").rstrip("/")
    if not base:
        return base
    if base.endswith("/v1"):
        return base
    if base.endswith("/compatible-mode/v1") or base.endswith("/compatible-mode"):
        return base if base.endswith("/v1") else base + "/v1"
    return base + "/v1"


def _agent_turn_timeout() -> int:
    raw = os.environ.get("XHS_AGENT_TURN_TIMEOUT", "120").strip()
    try:
        return max(8, min(300, int(raw)))
    except ValueError:
        return 120


def _llm_effective() -> dict | None:
    settings = _llm_settings()
    if not settings:
        return None
    merged = dict(settings)
    if not str(merged.get("apiKey") or "").strip():
        env_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if env_key:
            merged["apiKey"] = env_key
    if not str(merged.get("baseUrl") or "").strip():
        env_base = os.environ.get("OPENAI_BASE_URL", "").strip()
        if env_base:
            merged["baseUrl"] = env_base
    if not str(merged.get("model") or "").strip():
        env_model = os.environ.get("AGENTX_MODEL", "").strip()
        if env_model:
            merged["model"] = env_model
    return merged


def _direct_model(user: str) -> tuple[str | None, str]:
    settings = _llm_effective()
    if not settings:
        return None, "未找到模型配置文件（data/xhs/settings/llm.settings.json）。"
    base = _openai_base_url(str(settings.get("baseUrl") or ""))
    key = str(settings.get("apiKey") or "").strip()
    model = str(settings.get("model") or "").strip()
    if not base or not key or not model:
        return None, (
            "对话模型未就绪：请在设置页「对话模型」Tab 保存地址、模型名和密钥，并点连接测试。"
            "Docker 用户另需 deploy/.env 含 OPENAI_*（保存模型会自动同步），然后重启 agent-core 容器。"
        )
    body = json.dumps(
        {
            "model": model,
            "temperature": settings.get("temperature", 0.3),
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return None, "工作台里保存的模型密钥无效或已过期，所以这次只使用知识库原文。"
        return None, "工作台模型没有返回内容，所以这次只使用知识库原文。"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, "对话模型请求失败（网络或服务不可达）：%s" % exc
    except json.JSONDecodeError:
        return None, "对话模型返回了无法解析的内容。"
    try:
        return str(payload["choices"][0]["message"]["content"]).strip(), ""
    except (KeyError, IndexError, TypeError):
        return None, "工作台模型没有返回内容，所以这次只使用知识库原文。"


def test_llm(settings: dict) -> dict:
    base = _openai_base_url(str(settings.get("baseUrl") or ""))
    key = str(settings.get("apiKey") or "").strip()
    if not key:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = str(settings.get("model") or "").strip()
    if not model:
        model = os.environ.get("AGENTX_MODEL", "").strip()
    if not base or not key or not model:
        raise RuntimeError("请先填写地址、模型和密钥")
    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [{"role": "user", "content": "只回复一个字：好"}],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        reply = str(payload["choices"][0]["message"]["content"]).strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:180]
        raise RuntimeError("模型请求失败：HTTP %s %s" % (exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("模型请求失败：%s" % exc) from exc
    return {"ok": True, "reply": reply[:200]}


def _llm_settings() -> dict | None:
    if os.environ.get("XHS_LLM_SETTINGS"):
        path = Path(os.environ["XHS_LLM_SETTINGS"])
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None
    from xhs_svc.config import data_dir
    from xhs_svc.settings_store import SettingsStore

    return SettingsStore(data_dir() / "settings").load_llm()
