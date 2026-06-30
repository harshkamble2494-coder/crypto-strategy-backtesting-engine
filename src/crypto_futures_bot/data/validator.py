from __future__ import annotations

import pandas as pd

from crypto_futures_bot.data.schema import REQUIRED_COLUMNS


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"OHLCV data missing required columns: {missing}")

    clean = df.copy()
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], utc=True)
    clean = clean.sort_values("timestamp").drop_duplicates("timestamp")

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    if clean[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("OHLCV data contains missing or non-numeric values.")

    invalid_prices = (
        (clean["open"] <= 0)
        | (clean["high"] <= 0)
        | (clean["low"] <= 0)
        | (clean["close"] <= 0)
        | (clean["high"] < clean["low"])
    )
    if invalid_prices.any():
        raise ValueError("OHLCV data contains invalid price rows.")

    return clean.reset_index(drop=True)

