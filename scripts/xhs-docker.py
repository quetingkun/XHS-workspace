#!/usr/bin/env python3
"""兼容入口，请改用 python scripts/xhs.py pack|start。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from xhs import main  # noqa: E402


if __name__ == "__main__":
    legacy = sys.argv[1:] if len(sys.argv) > 1 else []
    mapped: list[str] = []
    for item in legacy:
        if item == "up":
            mapped.append("start")
        elif item == "down":
            mapped.extend(["stop", "--down"])
        elif item == "build":
            mapped.append("pack")
        elif item == "sync-env":
            continue
        else:
            mapped.append(item)
    if "start" not in mapped and "pack" not in mapped:
        mapped = ["start", *mapped]
    main(mapped if mapped else None)