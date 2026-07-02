from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    side: PositionSide
    entry_time: pd.Timestamp
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    entry_fee: float
    entry_atr: float | None = None
    break_even_activated: bool = False
    trailing_stop_activated: bool = False

    @property
    def notional(self) -> float:
        return self.entry_price * self.quantity
