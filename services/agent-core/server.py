#!/usr/bin/env python3
"""Agent-core。默认监听 :8081。"""

from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

from core_svc.api import create_app
from core_svc.codex import CodexSession
from core_svc.config import load_config, parse_addr
from core_svc.routing import Routing


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="XHS-workspace agent-core")
    parser.add_argument("--addr", default=":8081")
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--state-root", default="./data/xhs/agent-core")
    parser.add_argument("--config", default="configs/xhs.toml")
    parser.add_argument("--agent-config-root", default="configs")
    parser.add_argument("--cors-origins", default="*")
    raw = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(["--config" if item == "-config" else item for item in raw])
    try:
        cfg = load_config(args.config)
        cfg.addr = args.addr or cfg.addr
        cfg.state_root = args.state_root
        cfg.workspace_root = args.workspace_root
        cfg.agent_config_root = args.agent_config_root
        cfg.cors_origins = [item.strip() for item in args.cors_origins.split(",") if item.strip()] or ["*"]
        llm_path = __import__("pathlib").Path(cfg.workspace_root) / "data" / "xhs" / "settings" / "llm.settings.json"
        alt = __import__("pathlib").Path("/settings/llm.settings.json")
        if llm_path.is_file():
            cfg.llm_settings = str(llm_path)
        elif alt.is_file():
            cfg.llm_settings = str(alt)
        if not cfg.codex_home:
            cfg.codex_home = str(__import__("pathlib").Path(cfg.state_root) / "codex-home")
        routing = Routing(cfg.state_root, cfg.default_engine, cfg.allow_override)
        codex = (
            CodexSession(
                cfg.codex_binary,
                cfg.codex_home,
                cfg.workspace_root,
                cfg.model,
                cfg.provider,
                cfg.codex_sha256,
                cfg.sandbox_mode,
                cfg.approval_mode,
            )
            if cfg.codex_binary
            else None
        )
        if codex is not None and codex.sha_error():
            logging.getLogger("agent-core").error("%s", codex.sha_error())
        app = create_app(cfg, routing, codex)
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1
    host, port = parse_addr(cfg.addr)
    logging.getLogger("agent-core").info("agent-core listening addr=%s default_engine=%s", cfg.addr, routing.default_engine)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
