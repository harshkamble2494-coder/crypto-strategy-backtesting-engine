from __future__ import annotations

import pandas as pd

from crypto_futures_bot.config.models import StrategyConfig
from crypto_futures_bot.strategy.base import Strategy
from crypto_futures_bot.strategy.signals import SignalType


class TrendQualityEmaRsiStrategy(Strategy):
    """EMA/RSI crossover with trend-strength, slope, volatility, and participation filters."""

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def generate_signal(self, previous: pd.Series, current: pd.Series) -> SignalType:
        required = [
            "ema_fast",
            "ema_slow",
            "ema_trend",
            "ema_trend_slope",
            "rsi",
            "atr",
            "adx",
            "volume_ratio",
        ]
        if current[required].isna().any() or previous[required].isna().any():
            return SignalType.NONE

        trend_distance = self.config.min_trend_distance_atr * current["atr"]
        enough_volume = current["volume_ratio"] >= self.config.min_volume_ratio
        strong_trend = current["adx"] >= self.config.min_adx

        long_signal = (
            previous["ema_fast"] <= previous["ema_slow"]
            and current["ema_fast"] > current["ema_slow"]
            and current["close"] > current["ema_trend"] + trend_distance
            and current["ema_trend_slope"] > 0
            and current["rsi"] > self.config.rsi_long_threshold
            and strong_trend
            and enough_volume
        )
        if long_signal:
            return SignalType.LONG

        short_signal = (
            previous["ema_fast"] >= previous["ema_slow"]
            and current["ema_fast"] < current["ema_slow"]
            and current["close"] < current["ema_trend"] - trend_distance
            and current["ema_trend_slope"] < 0
            and current["rsi"] < self.config.rsi_short_threshold
            and strong_trend
            and enough_volume
        )
        if short_signal:
            return SignalType.SHORT

        return SignalType.NONE

