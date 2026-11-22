from __future__ import annotations

import hashlib
import json
import math
import urllib.error
import urllib.request
from typing import Any


def embed_texts(settings: dict[str, Any], texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    provider = str(settings.get("provider") or "")
    dim = int(settings.get("dimension") or 1536)
    if provider == "mock":
        return [_mock(text, dim) for text in texts]
    key = str(settings.get("apiKey") or "").strip()
    base = str(settings.get("baseUrl") or "").rstrip("/")
    model = str(settings.get("defaultModel") or settings.get("model") or "").strip()
    if not key or not base or not model:
        raise RuntimeError("Embedding 还没配置地址、模型或密钥")
    body = json.dumps({"model": model, "input": texts}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + "/embeddings",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:180]
        raise RuntimeError("Embedding 请求失败：HTTP %s %s" % (exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Embedding 请求失败：%s" % exc) from exc
    data = payload.get("data") or []
    vectors = [item.get("embedding") or [] for item in sorted(data, key=lambda item: item.get("index") or 0)]
    if len(vectors) != len(texts) or any(not item for item in vectors):
        raise RuntimeError("Embedding 没有返回对应数量的向量")
    return vectors


def _mock(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        digest = hashlib.sha256(digest).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1)
            if len(values) == dim:
                break
    norm = math.sqrt(sum(item * item for item in values)) or 1
    return [item / norm for item in values]
