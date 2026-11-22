"""agent-core 薄配置：只读产品用到的 toml 字段，环境变量可覆盖。"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from core_svc.routing import canon as _canon_engine


@dataclass
class Config:
    addr: str = ":8081"
    state_root: str = "./data/state"
    workspace_root: str = "."
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    model: str = "qwen3.6-plus"
    provider: str = "openai-compatible"
    api_key_env: str = "OPENAI_API_KEY"
    instructions: str = "你是 AI-workspace 个人知识助手。优先使用中文。"
    knowledge_url: str = "http://127.0.0.1:8092"
    knowledge_top_k: int = 6
    default_kb_ids: list[str] = field(default_factory=lambda: ["kb_default"])
    codex_enabled: bool = False
    codex_binary: str = ""
    codex_sha256: str = ""
    codex_version: str = ""
    codex_home: str = ""
    sandbox_mode: str = "read-only"
    approval_mode: str = "unless-trusted"
    trusted_tools: list[str] = field(
        default_factory=lambda: ["mcp__knowledge__search", "mcp__web_search__search"]
    )
    mcp_servers: list[dict] = field(default_factory=list)
    skill_paths: list[str] = field(default_factory=list)
    default_engine: str = "agent-core"
    allow_override: bool = True
    agent_config_root: str = ""
    llm_settings: str = ""


def load_config(path: str) -> Config:
    raw = {}
    if path and Path(path).is_file():
        raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    knowledge = raw.get("knowledge") or {}
    codex = raw.get("codex") or {}
    routing = codex.get("routing") or {}
    model_block = codex.get("model") or {}
    mcp = raw.get("mcp") or {}
    skills = raw.get("skills") or {}
    servers = []
    for name, block in (raw.get("mcp_servers") or {}).items():
        if isinstance(block, dict) and str(block.get("url") or "").strip():
            servers.append(
                {
                    "name": str(name),
                    "url": str(block.get("url")).strip(),
                    "required": bool(block.get("required")),
                }
            )
    trusted = list(mcp.get("trusted_tools") or ["mcp__knowledge__search", "mcp__web_search__search"])
    cfg = Config(
        model=str(raw.get("model") or "qwen3.6-plus"),
        provider=str(model_block.get("provider") or raw.get("model_provider") or "openai-compatible"),
        api_key_env=str(model_block.get("env_key") or raw.get("api_key_env") or "OPENAI_API_KEY"),
        instructions=str(raw.get("instructions") or "你是 AI-workspace 个人知识助手。优先使用中文。"),
        knowledge_url=str(knowledge.get("base_url") or "http://127.0.0.1:8092"),
        knowledge_top_k=int(knowledge.get("default_top_k") or 6),
        default_kb_ids=list(knowledge.get("default_kb_ids") or ["kb_default"]),
        codex_enabled=bool(codex.get("enabled")),
        codex_binary=str(codex.get("binary_path") or ""),
        codex_sha256=str(codex.get("binary_sha256") or ""),
        codex_version=str(codex.get("version") or ""),
        codex_home=str(codex.get("home_root") or ""),
        sandbox_mode=str(raw.get("sandbox_mode") or "read-only"),
        approval_mode=str(raw.get("approval_mode") or "unless-trusted"),
        trusted_tools=[str(item) for item in trusted],
        mcp_servers=servers,
        skill_paths=[str(item) for item in (skills.get("paths") or []) if str(item).strip()],
        default_engine=_canon_engine(str(routing.get("default_engine") or "agent-core")),
        allow_override=bool(routing.get("allow_override", True)),
    )
    if os.environ.get("AIW_CODEX_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        cfg.codex_enabled = True
    if os.environ.get("AIW_CODEX_ENABLED", "").strip().lower() in ("0", "false", "no"):
        cfg.codex_enabled = False
    if os.environ.get("AIW_CODEX_BINARY_PATH", "").strip():
        cfg.codex_binary = os.environ["AIW_CODEX_BINARY_PATH"].strip()
    if os.environ.get("AIW_CODEX_BINARY_SHA256", "").strip():
        cfg.codex_sha256 = os.environ["AIW_CODEX_BINARY_SHA256"].strip()
    if os.environ.get("AIW_CODEX_DEFAULT_ENGINE", "").strip():
        cfg.default_engine = _canon_engine(os.environ["AIW_CODEX_DEFAULT_ENGINE"].strip())
    if os.environ.get("AGENTX_MODEL", "").strip():
        cfg.model = os.environ["AGENTX_MODEL"].strip()
    if not cfg.codex_home:
        cfg.codex_home = str(Path(cfg.state_root) / "codex-home")
    return cfg


def llm_runtime(cfg: Config) -> dict[str, str]:
    settings = _read_llm(cfg.llm_settings)
    key = os.environ.get(cfg.api_key_env, "").strip() or os.environ.get("OPENAI_API_KEY", "").strip() or str(settings.get("apiKey") or "")
    base = os.environ.get("OPENAI_BASE_URL", "").strip() or str(settings.get("baseUrl") or "") or "https://api.deepseek.com"
    model = os.environ.get("AGENTX_MODEL", "").strip() or str(settings.get("model") or "") or cfg.model
    return {"apiKey": key, "baseUrl": base.rstrip("/"), "model": model}


def _read_llm(path: str) -> dict:
    candidates = [path] if path else []
    candidates.extend(
        [
            "/settings/llm.settings.json",
            str(Path("data/xhs/settings/llm.settings.json")),
            str(Path("services/knowledge/data/llm.settings.json")),
            str(Path("../knowledge/data/llm.settings.json")),
        ]
    )
    for item in candidates:
        if item and Path(item).is_file():
            import json

            try:
                data = json.loads(Path(item).read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
            return data if isinstance(data, dict) else {}
    return {}


def parse_addr(addr: str) -> tuple[str, int]:
    addr = addr.strip()
    if addr.startswith(":"):
        return "0.0.0.0", int(addr[1:])
    host, port = addr.rsplit(":", 1)
    return host or "0.0.0.0", int(port)
