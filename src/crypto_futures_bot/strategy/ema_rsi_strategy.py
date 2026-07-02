from __future__ import annotations

import pandas as pd

from crypto_futures_bot.config.models import StrategyConfig
from crypto_futures_bot.strategy.base import Strategy
from crypto_futures_bot.strategy.signals import SignalType


class EmaRsiStrategy(Strategy):
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def generate_signal(self, previous: pd.Series, current: pd.Series) -> SignalType:
        required = ["ema_fast", "ema_slow", "ema_trend", "rsi"]
        if self.config.use_adx_filter:
            required.append("adx")
        if self.config.use_trend_slope_filter:
            required.append("ema_trend_slope")
        if current[required].isna().any() or previous[required].isna().any():
            return SignalType.NONE

        if self.config.use_adx_filter and current["adx"] < self.config.min_adx:
            return SignalType.NONE

        trend_slope_allows_long = (
            not self.config.use_trend_slope_filter or current["ema_trend_slope"] > 0
        )
        trend_slope_allows_short = (
            not self.config.use_trend_slope_filter or current["ema_trend_slope"] < 0
        )

        long_signal = (
            previous["ema_fast"] <= previous["ema_slow"]
            and current["ema_fast"] > current["ema_slow"]
            and current["close"] > current["ema_trend"]
            and current["rsi"] > self.config.rsi_long_threshold
            and trend_slope_allows_long
        )
        if long_signal:
            return SignalType.LONG

        short_signal = (
            previous["ema_fast"] >= previous["ema_slow"]
            and current["ema_fast"] < current["ema_slow"]
            and current["close"] < current["ema_trend"]
            and current["rsi"] < self.config.rsi_short_threshold
            and trend_slope_allows_short
        )
        if short_signal:
            return SignalType.SHORT

        return SignalType.NONE
