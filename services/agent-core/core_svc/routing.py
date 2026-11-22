from __future__ import annotations

import json
from pathlib import Path


LOCAL_ENGINE = "agent-core"
LEGACY_ENGINE = "go-agent-core"
ENGINES = (LOCAL_ENGINE, "codex")


def canon(name: str) -> str:
    name = name.strip()
    if name == LEGACY_ENGINE:
        return LOCAL_ENGINE
    return name


FUNCTIONS = (
    {"function_id": "general_qa", "name": "问询助手"},
    {"function_id": "brainstorm", "name": "知识头脑风暴"},
    {"function_id": "xhs_ops", "name": "小红书运营助手"},
)


class Routing:
    def __init__(self, state_root: str, default_engine: str, allow_override: bool) -> None:
        self.path = Path(state_root) / "config" / "engine-routing.json"
        default_engine = canon(default_engine)
        self.default_engine = default_engine if default_engine in ENGINES else LOCAL_ENGINE
        self.allow_override = allow_override
        self.function_defaults: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        engine = canon(str(data.get("default_engine") or ""))
        if engine in ENGINES:
            self.default_engine = engine
        defaults = data.get("function_defaults") or {}
        if isinstance(defaults, dict):
            self.function_defaults = {
                str(key): canon(str(value))
                for key, value in defaults.items()
                if canon(str(value)) in ENGINES
            }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"default_engine": self.default_engine, "function_defaults": self.function_defaults}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def update(self, default_engine: str, function_defaults: dict | None) -> None:
        default_engine = canon(default_engine)
        if default_engine not in ENGINES:
            raise ValueError("default_engine 必须是 agent-core 或 codex")
        self.default_engine = default_engine
        if function_defaults is not None:
            cleaned = {}
            for key, value in function_defaults.items():
                chosen = canon(str(value))
                if chosen in ENGINES:
                    cleaned[str(key)] = chosen
            self.function_defaults = cleaned
        self.save()

    def choose(self, header: str, function_id: str, codex_ok: bool) -> str:
        header = canon(header)
        if self.allow_override and header in ENGINES:
            name = header
        elif function_id in self.function_defaults:
            name = self.function_defaults[function_id]
        else:
            name = self.default_engine
        if name == "codex" and not codex_ok and header != "codex":
            return LOCAL_ENGINE
        return name

    def view(self, engines: list[dict]) -> dict:
        functions = []
        for item in FUNCTIONS:
            chosen = self.function_defaults.get(item["function_id"])
            functions.append(
                {
                    "function_id": item["function_id"],
                    "name": item["name"],
                    "engine": chosen or self.default_engine,
                    "inherited": chosen is None,
                }
            )
        return {
            "default_engine": self.default_engine,
            "function_defaults": dict(self.function_defaults),
            "functions": functions,
            "engines": engines,
            "allow_override": self.allow_override,
            "allow_write_turns": True,
        }
