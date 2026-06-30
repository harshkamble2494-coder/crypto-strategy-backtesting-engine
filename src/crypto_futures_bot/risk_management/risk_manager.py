from __future__ import annotations

from collections import defaultdict

import pandas as pd

from crypto_futures_bot.config.models import RiskConfig


class RiskManager:
    def __init__(self, config: RiskConfig, initial_capital: float) -> None:
        self.config = config
        self.initial_capital = initial_capital
        self._daily_realized_pnl: defaultdict[pd.Timestamp, float] = defaultdict(float)
        self._daily_start_equity: dict[pd.Timestamp, float] = {}

    def register_day(self, timestamp: pd.Timestamp, equity: float) -> None:
        day = timestamp.normalize()
        self._daily_start_equity.setdefault(day, equity)

    def can_open_new_trade(self, timestamp: pd.Timestamp) -> bool:
        day = timestamp.normalize()
        start_equity = self._daily_start_equity.get(day, self.initial_capital)
        max_loss = start_equity * self.config.max_daily_loss_pct
        return self._daily_realized_pnl[day] > -max_loss

    def record_realized_pnl(self, timestamp: pd.Timestamp, pnl: float) -> None:
        self._daily_realized_pnl[timestamp.normalize()] += pnl

