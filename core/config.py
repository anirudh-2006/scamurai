from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    local = ROOT / "config.local.yaml"
    if local.exists():
        cfg.update(yaml.safe_load(local.read_text(encoding="utf-8")) or {})
    return cfg
