from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

from xhs_svc.db import DB, dumps, loads, new_id, now
from xhs_svc.embedder import embed_texts
from xhs_svc.settings_store import SettingsStore


FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def knowledge_root(data: Path) -> Path:
    path = data / "knowledge"
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_markdown(text: str) -> tuple[dict, str]:
    meta: dict = {}
    body = text
    match = FRONT_RE.match(text)
    if match:
        meta = _meta(match.group(1))
        body = text[match.end() :]
    return meta, body.strip()


def import_approved(db: DB, data: Path) -> dict:
    root = knowledge_root(data)
    imported = 0
    skipped = 0
    seen: set[str] = set()
    for path in sorted(root.rglob("*.md")):
        meta, body = parse_markdown(path.read_text(encoding="utf-8"))
        status = str(meta.get("status") or "pending")
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        if status != "approved":
            skipped += 1
            db.run("DELETE FROM knowledge_docs WHERE path=?", (rel,))
            continue
        title = str(meta.get("title") or path.stem)
        existing = db.one("SELECT id FROM knowledge_docs WHERE path=?", (rel,))
        if existing:
            db.run(
                "UPDATE knowledge_docs SET title=?, status=?, body=?, updated_at=? WHERE path=?",
                (title, status, body, now(), rel),
            )
        else:
            db.run(
                "INSERT INTO knowledge_docs (id,path,title,status,body,updated_at) VALUES (?,?,?,?,?,?)",
                (str(meta.get("id") or new_id("doc")), rel, title, status, body, now()),
            )
        imported += 1
    for row in db.all("SELECT path FROM knowledge_docs"):
        if row["path"] not in seen:
            db.run("DELETE FROM knowledge_docs WHERE path=?", (row["path"],))
    embedded, embed_error = index_vectors(db, data)
    return {"imported": imported, "skipped": skipped, "embedded": embedded, "embed_error": embed_error}


def retrieve(db: DB, query: str, limit: int = 4) -> list[dict]:
    embedded = _embed_retrieve(db, query, limit)
    if embedded:
        return embedded
    return _keyword_retrieve(db, query, limit)


def list_docs(db: DB) -> list[dict]:
    docs = db.all("SELECT id, path, title, status, updated_at FROM knowledge_docs ORDER BY updated_at DESC")
    counts = {row["doc_id"]: row["n"] for row in db.all("SELECT doc_id, COUNT(*) AS n FROM knowledge_chunks GROUP BY doc_id")}
    for doc in docs:
        doc["chunks"] = counts.get(doc["id"], 0)
    return docs


def add_document(db: DB, data: Path, title: str, body: str) -> dict:
    title = title.strip()
    body = body.strip()
    if not title or not body:
        raise ValueError("标题和正文都不能为空")
    doc_id = new_id("doc")
    folder = knowledge_root(data) / "library"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("%s.md" % doc_id)
    path.write_text(
        "\n".join(["---", "id: %s" % doc_id, 'title: "%s"' % title.replace('"', ""), "status: approved", "type: note", "---", "", body, ""]),
        encoding="utf-8",
    )
    result = import_approved(db, data)
    result["id"] = doc_id
    return result


def index_vectors(db: DB, data: Path) -> tuple[int, str]:
    settings = _embedding_settings(Path(data))
    if settings.get("provider") != "mock" and not str(settings.get("apiKey") or "").strip():
        db.run("DELETE FROM knowledge_chunks")
        return 0, ""
    docs = db.all("SELECT id, path, title, body FROM knowledge_docs WHERE status='approved'")
    pieces: list[tuple[dict, str]] = []
    for doc in docs:
        for chunk in _chunks(doc["title"] + "\n" + doc["body"]):
            pieces.append((doc, chunk))
    if not pieces:
        db.run("DELETE FROM knowledge_chunks")
        return 0, ""
    try:
        vectors = embed_texts(settings, [text for _doc, text in pieces])
    except RuntimeError as exc:
        return 0, str(exc)
    db.run("DELETE FROM knowledge_chunks")
    stamp = now()
    for (doc, text), vector in zip(pieces, vectors):
        db.run(
            """INSERT INTO knowledge_chunks (id,doc_id,path,title,text,vector_json,updated_at) VALUES (?,?,?,?,?,?,?)""",
            (new_id("chunk"), doc["id"], doc["path"], doc["title"], text, dumps(vector), stamp),
        )
    return len(pieces), ""


def _embed_retrieve(db: DB, query: str, limit: int) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []
    rows = db.all("SELECT doc_id, path, title, text, vector_json FROM knowledge_chunks WHERE vector_json IS NOT NULL AND vector_json != ''")
    if not rows:
        return []
    settings = _embedding_settings(db.path.parent)
    try:
        query_vector = embed_texts(settings, [query])[0]
    except RuntimeError:
        return []
    scored: list[tuple[float, dict]] = []
    for row in rows:
        vector = loads(row["vector_json"], [])
        score = _cosine(query_vector, vector if isinstance(vector, list) else [])
        if score < 0.45:
            continue
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    seen: set[str] = set()
    found = []
    for score, row in scored:
        if row["path"] in seen:
            continue
        seen.add(row["path"])
        found.append(
            {
                "id": row["doc_id"],
                "path": row["path"],
                "title": row["title"],
                "excerpt": row["text"][:420],
                "match": "embedding",
                "score": round(score, 3),
            }
        )
        if len(found) >= limit:
            break
    return found


def _keyword_retrieve(db: DB, query: str, limit: int) -> list[dict]:
    words = _tokens(query)
    if not words:
        return []
    docs = db.all("SELECT id, path, title, body FROM knowledge_docs WHERE status='approved'")
    scored: list[tuple[int, dict]] = []
    for doc in docs:
        hay = doc["title"] + "\n" + doc["body"]
        score = len({word for word in words if word in hay})
        if score <= 0:
            continue
        excerpt = _excerpt(doc["body"], words)
        scored.append((score, {"id": doc["id"], "path": doc["path"], "title": doc["title"], "excerpt": excerpt, "match": "keyword"}))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def _chunks(text: str, size: int = 480, overlap: int = 60) -> list[str]:
    raw = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if not raw:
        return []
    if len(raw) <= size:
        return [raw]
    chunks = []
    start = 0
    while start < len(raw):
        chunks.append(raw[start : start + size])
        if start + size >= len(raw):
            break
        start += size - overlap
    return chunks


def _embedding_settings(data: Path) -> dict:
    override = os.environ.get("XHS_EMBEDDING_SETTINGS")
    if override:
        path = Path(override)
        if not path.is_file():
            return {"provider": "openai_compatible", "apiKey": "", "baseUrl": "", "defaultModel": "", "dimension": 1536}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"provider": "openai_compatible", "apiKey": "", "dimension": 1536}
        return loaded if isinstance(loaded, dict) else {}
    return SettingsStore(Path(data) / "settings").load_embedding()


def _cosine(left: list, right: list) -> float:
    if not left or len(left) != len(right):
        return 0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right):
        dot += float(a) * float(b)
        left_norm += float(a) * float(a)
        right_norm += float(b) * float(b)
    if left_norm <= 0 or right_norm <= 0:
        return 0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


def confirm_file(db: DB, data: Path, rel: str) -> dict:
    rel = rel.replace("\\", "/").lstrip("/")
    root = knowledge_root(data).resolve()
    path = (root / rel).resolve()
    if not path.is_file() or not path.is_relative_to(root):
        raise FileNotFoundError(rel)
    text = path.read_text(encoding="utf-8")
    meta, _body = parse_markdown(text)
    if "status:" in text:
        text = re.sub(r"(?m)^status:\s*\S+", "status: approved", text, count=1)
    else:
        text = text.replace("---\n", "---\nstatus: approved\n", 1) if text.startswith("---") else text
    if not meta:
        text = f"---\nstatus: approved\ntitle: {path.stem}\n---\n\n" + text
    path.write_text(text, encoding="utf-8")
    return import_approved(db, data)


def _meta(block: str) -> dict:
    meta: dict = {}
    key = ""
    for line in block.splitlines():
        if line.strip().startswith("- ") and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(line.strip()[2:].strip())
            continue
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        key = name.strip()
        value = value.strip().strip('"').strip("'")
        meta[key] = value
    return meta


def _tokens(query: str) -> list[str]:
    pieces = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", query or "")
    words: list[str] = []
    for piece in pieces:
        if re.fullmatch(r"[A-Za-z0-9]+", piece):
            words.append(piece.lower())
            continue
        if len(piece) <= 4:
            words.append(piece)
            continue
        for size in (4, 3, 2):
            for index in range(0, len(piece) - size + 1):
                words.append(piece[index : index + size])
    return words


def _excerpt(body: str, words: list[str], width: int = 420) -> str:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    picked: list[str] = []
    for line in lines:
        if any(word in line for word in words) or line.startswith("#"):
            picked.append(line)
        if sum(len(item) for item in picked) > width:
            break
    text = "\n".join(picked) if picked else body[:width]
    return text[:width]
