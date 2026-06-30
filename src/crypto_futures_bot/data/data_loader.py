from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from crypto_futures_bot.config.models import DataConfig
from crypto_futures_bot.data.validator import validate_ohlcv


class CsvDataLoader:
    def __init__(self, config: DataConfig) -> None:
        self.config = config

    def load(self) -> pd.DataFrame:
        if not self.config.csv_path.exists():
            raise FileNotFoundError(
                f"Historical data file not found: {self.config.csv_path}. "
                "Place BTCUSDT 1h candles there or update config/settings.yaml."
            )

        df = pd.read_csv(self.config.csv_path)
        df = validate_ohlcv(df)
        return self._filter_date_range(df)

    def _filter_date_range(self, df: pd.DataFrame) -> pd.DataFrame:
        end = pd.Timestamp(self.config.end_date) if self.config.end_date else pd.Timestamp(datetime.now(UTC))
        end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")

        if self.config.start_date:
            start = pd.Timestamp(self.config.start_date)
            start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
        else:
            start = end - pd.DateOffset(years=self.config.default_lookback_years)

        filtered = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)].copy()
        if filtered.empty:
            raise ValueError(f"No candles found between {start} and {end}.")
        return filtered.reset_index(drop=True)

