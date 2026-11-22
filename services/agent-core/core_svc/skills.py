"""从 skills 目录热加载 SKILL.md。每次选择前看文件修改时间。"""

from __future__ import annotations

import re
from pathlib import Path

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TRIGGERS = re.compile(r"[^、，,。；;\n]{2,}")


class SkillBook:
    def __init__(self, paths: list[str]) -> None:
        self.paths = [Path(item) for item in paths if str(item).strip()]
        self._stamp: tuple = ()
        self._skills: list[dict] = []

    def select(self, prompt: str) -> str:
        self._reload()
        text = prompt.strip()
        if not text or not self._skills:
            return ""
        picked = []
        for skill in self._skills:
            if _hit(text, skill["triggers"]):
                picked.append(skill)
        if not picked:
            return ""
        blocks = []
        for skill in picked[:3]:
            blocks.append("### %s\n%s" % (skill["name"], skill["body"][:2000]))
        return "\n\n".join(blocks)

    def _reload(self) -> None:
        files = []
        for root in self.paths:
            if not root.is_dir():
                continue
            files.extend(sorted(root.rglob("SKILL.md")))
        stamp = tuple((str(path), path.stat().st_mtime_ns) for path in files if path.is_file())
        if stamp == self._stamp:
            return
        skills = []
        for path in files:
            if not path.is_file():
                continue
            parsed = _parse(path.read_text(encoding="utf-8", errors="replace"))
            if parsed:
                skills.append(parsed)
        self._skills = skills
        self._stamp = stamp


def _parse(text: str) -> dict | None:
    match = _FRONT.match(text)
    meta = match.group(1) if match else ""
    body = text[match.end() :] if match else text
    name = _field(meta, "name") or "skill"
    description = _field(meta, "description")
    scene = ""
    if "## 适用场景" in body:
        scene = body.split("## 适用场景", 1)[1].split("##", 1)[0]
    triggers = []
    for source in (description, scene, name):
        for item in _TRIGGERS.findall(source.replace("\n", "、")):
            item = item.strip(" -\t\"'`")
            if len(item) >= 2 and item not in triggers:
                triggers.append(item)
    triggers = [item for item in triggers if len(item) >= 4 or item == name]
    if not triggers:
        return None
    return {"name": name, "triggers": triggers[:40], "body": body.strip()}


def _field(meta: str, key: str) -> str:
    lines = meta.splitlines()
    found = []
    capture = False
    for line in lines:
        if line.startswith(key + ":"):
            rest = line.split(":", 1)[1].strip()
            if rest in (">", "|", ""):
                capture = True
                continue
            return rest.strip("\"'")
        if capture:
            if line.startswith(" ") or line.startswith("\t"):
                found.append(line.strip())
            else:
                break
    return " ".join(found).strip()


def _hit(prompt: str, triggers: list[str]) -> bool:
    for item in triggers:
        if item and item in prompt:
            return True
    return False
