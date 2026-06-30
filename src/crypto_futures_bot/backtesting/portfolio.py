from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from crypto_futures_bot.execution.position import Position, PositionSide


@dataclass
class EquityPoint:
    timestamp: pd.Timestamp
    equity: float
    balance: float


@dataclass
class Portfolio:
    initial_capital: float
    balance: float = field(init=False)
    position: Position | None = None
    equity_curve: list[EquityPoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.balance = self.initial_capital

    def has_open_position(self) -> bool:
        return self.position is not None

    def current_equity(self, mark_price: float | None = None) -> float:
        if self.position is None or mark_price is None:
            return self.balance
        return self.balance + self._unrealized_pnl(mark_price)

    def record_equity(self, timestamp: pd.Timestamp, mark_price: float) -> None:
        self.equity_curve.append(
            EquityPoint(timestamp=timestamp, equity=self.current_equity(mark_price), balance=self.balance)
        )

    def _unrealized_pnl(self, mark_price: float) -> float:
        if self.position is None:
            return 0.0
        if self.position.side == PositionSide.LONG:
            return (mark_price - self.position.entry_price) * self.position.quantity
        return (self.position.entry_price - mark_price) * self.position.quantity

    def equity_dataframe(self) -> pd.DataFrame:
        if not self.equity_curve:
            return pd.DataFrame(columns=["timestamp", "equity", "balance"])
        return pd.DataFrame([point.__dict__ for point in self.equity_curve])

