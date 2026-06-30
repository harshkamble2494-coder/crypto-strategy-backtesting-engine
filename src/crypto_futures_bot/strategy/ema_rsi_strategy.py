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
        if current[required].isna().any() or previous[required].isna().any():
            return SignalType.NONE

        long_signal = (
            previous["ema_fast"] <= previous["ema_slow"]
            and current["ema_fast"] > current["ema_slow"]
            and current["close"] > current["ema_trend"]
            and current["rsi"] > self.config.rsi_long_threshold
        )
        if long_signal:
            return SignalType.LONG

        short_signal = (
            previous["ema_fast"] >= previous["ema_slow"]
            and current["ema_fast"] < current["ema_slow"]
            and current["close"] < current["ema_trend"]
            and current["rsi"] < self.config.rsi_short_threshold
        )
        if short_signal:
            return SignalType.SHORT

        return SignalType.NONE
