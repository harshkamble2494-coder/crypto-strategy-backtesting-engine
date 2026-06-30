from __future__ import annotations

from datetime import datetime
from pathlib import Path


def create_backtest_output_dir(results_dir: Path, symbol: str, timeframe: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = results_dir / f"{symbol}_{timeframe}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

