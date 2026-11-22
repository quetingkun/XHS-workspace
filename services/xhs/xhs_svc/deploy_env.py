from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from xhs_svc.config import workspace_root


@dataclass(frozen=True)
class EnvSyncOutcome:
  """Result of syncing llm.settings.json into deploy/.env."""

  written: bool = False
  unchanged: bool = False
  warn: str | None = None

  @property
  def ok(self) -> bool:
    return self.written or self.unchanged


def _llm_settings_path() -> Path:
  return workspace_root() / "data" / "xhs" / "settings" / "llm.settings.json"


def deploy_env_path() -> Path:
  return workspace_root() / "deploy" / ".env"


def sync_llm_to_deploy_env() -> EnvSyncOutcome:
  """Write OPENAI_* / AGENTX_MODEL from settings file into deploy/.env for agent-core."""
  path = _llm_settings_path()
  if not path.is_file():
    return EnvSyncOutcome(warn="未找到对话模型配置，已跳过 deploy/.env 同步。")
  try:
    data = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return EnvSyncOutcome(warn="对话模型配置无法读取，已跳过 deploy/.env 同步。")
  if not isinstance(data, dict):
    return EnvSyncOutcome(warn="对话模型配置格式无效，已跳过 deploy/.env 同步。")
  api_key = str(data.get("apiKey") or "").strip()
  base_url = str(data.get("baseUrl") or "").strip().rstrip("/")
  model = str(data.get("model") or "").strip()
  if not api_key or "*" in api_key:
    return EnvSyncOutcome(warn="对话模型未配置有效密钥，已跳过 deploy/.env 同步。")

  env_file = deploy_env_path()
  example = workspace_root() / "deploy" / ".env.example"
  try:
    existing = env_file.read_text(encoding="utf-8") if env_file.is_file() else ""
  except OSError:
    existing = ""
  if not existing.strip() and example.is_file():
    try:
      existing = example.read_text(encoding="utf-8")
    except OSError:
      existing = ""

  def upsert(text: str, key: str, value: str) -> str:
    pattern = re.compile(r"(?m)^" + re.escape(key) + r"=.*$")
    line = "%s=%s" % (key, value)
    if pattern.search(text):
      return pattern.sub(line, text)
    if text and not text.endswith("\n"):
      text += "\n"
    return text + line + "\n"

  updated = upsert(existing, "OPENAI_API_KEY", api_key)
  if base_url:
    updated = upsert(updated, "OPENAI_BASE_URL", base_url)
  if model:
    updated = upsert(updated, "AGENTX_MODEL", model)

  if updated == existing:
    return EnvSyncOutcome(unchanged=True)

  env_file.parent.mkdir(parents=True, exist_ok=True)
  try:
    env_file.write_text(updated, encoding="utf-8", newline="\n")
  except PermissionError:
    return EnvSyncOutcome(
      warn=(
        "无法写入 deploy/.env（文件可能被编辑器占用或只读）。"
        "请关闭 Cursor 中的 deploy/.env 后重新执行 start，或在设置页再次保存模型。"
        "本次启动将继续，但 agent-core 可能仍用旧的 OPENAI_*。"
      ),
    )
  except OSError as exc:
    if getattr(exc, "errno", None) == 13:
      return EnvSyncOutcome(
        warn=(
          "无法写入 deploy/.env（权限被拒绝）。请关闭编辑器中的 deploy/.env 后重试。"
          "本次启动将继续。"
        ),
      )
    raise
  return EnvSyncOutcome(written=True)


# Backward-compatible helper for callers that only need bool
def sync_llm_to_deploy_env_ok() -> bool:
  return sync_llm_to_deploy_env().ok