"""本地引擎：知识库和联网先取证，再走 OpenAI 兼容流式补全。"""

from __future__ import annotations

import json
from typing import Any, Callable, Iterator

import httpx

Chat = Callable[[list[dict[str, str]]], Iterator[str]]

GENERAL = """你是 AI-workspace 个人知识工作台的问询助手。优先使用中文，语气自然简洁。
下面如果附有知识库摘录或联网补充，回答时点名来源。没有摘录就不要编造文献。
联网失败时用训练知识作答，并写「模型常识（联网不可用）」。"""

BRAINSTORM = """你是 AI-workspace 个人知识工作台的头脑风暴助手。优先使用中文。
明确区分知识库依据、推断和待验证问题。输出 Markdown：
## 澄清
## 基于知识库的要点（带来源文档名）
## 推断与命题
## 知识增量（可写入 Wiki 的短句列表，用 `- ` 项目符号）
## 下一步需回答（用 `- ` 项目符号）
未命中不要编造文献。"""

XHS_OPS = """你是个人小红书账号的运营助手（XHS-workspace）。
知识库摘录、素材/采集结果和你自己的判断要分开说。
采集状态不是 ok 或 partial 的内容不能说成热点；模拟数据不能说成真实笔记。
找不到资料时直接说明没找到，不要编造选题方法或数据。
不要建议绕过验证码、维护 Cookie，也不要把别人的正文写进待发布稿。
发布必须等这个版本被人工确认。
下面如果附有知识库摘录或联网补充，回答时点名来源。"""


def system_for(function_id: str) -> str:
    if function_id == "brainstorm":
        return BRAINSTORM
    if function_id == "xhs_ops":
        return XHS_OPS
    return GENERAL


def run_local(
    prompt: str,
    function_id: str,
    evidence: str,
    chat: Chat,
    runtime: dict[str, str],
) -> Iterator[dict[str, Any]]:
    messages = [
        {"role": "system", "content": system_for(function_id)},
        {"role": "user", "content": prompt if not evidence else prompt + "\n\n" + evidence},
    ]
    answer: list[str] = []
    try:
        stream = chat(messages) if chat else openai_stream(runtime, messages)
        for delta in stream:
            if not delta:
                continue
            answer.append(delta)
            yield {"type": "model.output.delta", "payload": {"delta": delta}}
    except Exception as exc:  # noqa: BLE001
        yield {"type": "error", "payload": {"message": str(exc)}}
        yield {"type": "turn.failed", "payload": {"message": str(exc)}}
        return
    yield {"type": "turn.completed", "payload": {"final_message": "".join(answer)}}


def openai_stream(runtime: dict[str, str], messages: list[dict[str, str]]) -> Iterator[str]:
    if not runtime.get("apiKey"):
        raise RuntimeError("LLM API Key 未配置")
    url = runtime["baseUrl"].rstrip("/") + "/chat/completions"
    payload = {"model": runtime.get("model") or "qwen3.6-plus", "messages": messages, "temperature": 0.3, "stream": True}
    with httpx.Client(timeout=180) as client:
        with client.stream("POST", url, json=payload, headers={"Authorization": "Bearer " + runtime["apiKey"], "Accept": "text/event-stream"}) as response:
            if response.status_code >= 300:
                body = response.read().decode("utf-8", errors="replace")[:400]
                raise RuntimeError(f"llm http {response.status_code}: {body}")
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = (choices[0].get("delta") or {}).get("content") or ""
                if delta:
                    yield delta


def search_knowledge(base_url: str, kb_ids: list[str], query: str, top_k: int, merge: bool) -> str:
    if not base_url or not query.strip():
        return ""
    top_k = top_k or 6
    root = base_url.rstrip("/")
    # XHS 运营台：GET /api/xhs/knowledge/retrieve?q=
    if "/api/xhs/" in root or root.endswith(":8097") or "kb_xhs" in kb_ids:
        res = httpx.get(root + "/api/xhs/knowledge/retrieve", params={"q": query.strip()}, timeout=40)
        if res.status_code >= 300:
            raise RuntimeError(f"knowledge http {res.status_code}")
        data = res.json() if res.content else {}
        rows = (data or {}).get("sources") if isinstance(data, dict) else []
        parts = []
        for row in rows[:top_k]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("title") or row.get("path") or "")
            content = str(row.get("excerpt") or row.get("body") or "").strip()
            if content:
                parts.append(f"来源：{name}\n{content[:800]}")
        return "\n\n".join(parts)
    if not kb_ids:
        return ""
    payload = {
        "query": query,
        "kbIds": kb_ids,
        "topK": top_k,
        "searchMode": "hybrid",
        "retrievalPath": "merge" if merge else "native",
    }
    res = httpx.post(root + "/api/knowledge/retrieve", json=payload, timeout=40)
    if res.status_code >= 300:
        raise RuntimeError(f"knowledge http {res.status_code}")
    data = res.json()
    rows = data if isinstance(data, list) else (data or {}).get("results") or []
    parts = []
    for row in rows[:top_k]:
        name = row.get("docName") or (row.get("location") or {}).get("docName") or ""
        content = str(row.get("content") or "").strip()
        if content:
            parts.append(f"来源：{name}\n{content[:500]}")
    return "\n\n".join(parts)
