from __future__ import annotations

import logging

from crypto_futures_bot.config.models import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    config.file_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.file_path, encoding="utf-8"),
        ],
        force=True,
    )

