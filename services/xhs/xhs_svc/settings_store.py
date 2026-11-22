from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def _keep_key(patch: str) -> bool:
    key = patch.strip()
    return bool(key) and "*" not in key and not key.startswith("****")


class SettingsStore:
    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def embedding_path(self) -> Path:
        return self.folder / "embedding.settings.json"

    def llm_path(self) -> Path:
        return self.folder / "llm.settings.json"

    def load_embedding(self) -> dict[str, Any]:
        data = self._read(self.embedding_path())
        if not data:
            data = {
                "provider": "openai_compatible",
                "baseUrl": "",
                "apiKey": "",
                "defaultModel": "text-embedding-3-small",
                "dimension": 1536,
                "batchSize": 32,
            }
        data.setdefault("provider", "openai_compatible")
        data.setdefault("defaultModel", "text-embedding-3-small")
        data.setdefault("dimension", 1536)
        data.setdefault("batchSize", 32)
        return data

    def save_embedding(self, current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current)
        for key in ("provider", "baseUrl", "defaultModel"):
            if str(patch.get(key) or "").strip():
                merged[key] = str(patch[key]).strip()
        if patch.get("dimension"):
            merged["dimension"] = int(patch["dimension"])
        if patch.get("batchSize"):
            merged["batchSize"] = int(patch["batchSize"])
        if _keep_key(str(patch.get("apiKey") or "")):
            merged["apiKey"] = str(patch["apiKey"]).strip()
        self._write(self.embedding_path(), merged)
        return merged

    def load_llm(self) -> dict[str, Any]:
        data = self._read(self.llm_path())
        if not data:
            data = {
                "provider": "openai_compatible",
                "baseUrl": "",
                "apiKey": "",
                "model": "",
                "temperature": 0.3,
            }
        data.setdefault("provider", "openai_compatible")
        data.setdefault("temperature", 0.3)
        return data

    def merge_llm(self, current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current)
        for key in ("provider", "baseUrl", "model"):
            if str(patch.get(key) or "").strip():
                merged[key] = str(patch[key]).strip()
        if patch.get("temperature") is not None and str(patch.get("temperature")).strip() != "":
            merged["temperature"] = float(patch["temperature"])
        if _keep_key(str(patch.get("apiKey") or "")):
            merged["apiKey"] = str(patch["apiKey"]).strip()
        return merged

    def save_llm(self, current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = self.merge_llm(current, patch)
        self._write(self.llm_path(), merged)
        return merged

    def _read(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def public_settings(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    out["apiKey"] = mask_secret(str(out.get("apiKey") or ""))
    return out
