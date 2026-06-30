from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    gross_profit_loss: float
    net_profit_loss: float
    account_balance: float
    trade_duration: pd.Timedelta
    exit_reason: str
    fees: float

    @property
    def return_pct(self) -> float:
        capital_at_risk = self.entry_price * self.position_size
        return self.net_profit_loss / capital_at_risk if capital_at_risk else 0.0

