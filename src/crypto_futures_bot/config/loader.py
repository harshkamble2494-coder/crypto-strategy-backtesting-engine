from __future__ import annotations

from pathlib import Path

import yaml

from crypto_futures_bot.config.models import AppConfig


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a YAML mapping.")

    project_root = path.parent.parent
    return AppConfig.from_dict(raw, project_root)

