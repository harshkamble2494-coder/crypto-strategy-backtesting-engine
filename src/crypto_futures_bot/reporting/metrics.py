from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from crypto_futures_bot.backtesting.trade import Trade


@dataclass(frozen=True)
class PerformanceMetrics:
    net_profit: float
    total_return_pct: float
    cagr_pct: float
    win_rate_pct: float
    profit_factor: float
    sharpe_ratio: float
    maximum_drawdown_pct: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    total_trades: int
    long_trades: int
    long_win_rate_pct: float
    short_trades: int
    short_win_rate_pct: float
    average_holding_time: str

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


class MetricsCalculator:
    def calculate(self, trades: list[Trade], equity_curve: pd.DataFrame, initial_capital: float) -> PerformanceMetrics:
        pnls = np.array([trade.net_profit_loss for trade in trades], dtype=float)
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]
        ending_equity = float(equity_curve["equity"].iloc[-1]) if not equity_curve.empty else initial_capital
        net_profit = ending_equity - initial_capital
        total_return = net_profit / initial_capital if initial_capital else 0.0

        years = self._years(equity_curve)
        cagr = ((ending_equity / initial_capital) ** (1 / years) - 1) if years > 0 and initial_capital > 0 else 0.0

        profit_factor = wins.sum() / abs(losses.sum()) if losses.sum() < 0 else math.inf if wins.size else 0.0
        returns = equity_curve["equity"].pct_change().dropna() if not equity_curve.empty else pd.Series(dtype=float)
        sharpe = self._sharpe(returns)
        max_dd = self._maximum_drawdown(equity_curve)
        long_trades = [trade for trade in trades if trade.direction == "LONG"]
        short_trades = [trade for trade in trades if trade.direction == "SHORT"]

        return PerformanceMetrics(
            net_profit=net_profit,
            total_return_pct=total_return * 100,
            cagr_pct=cagr * 100,
            win_rate_pct=self._win_rate(trades),
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            maximum_drawdown_pct=max_dd * 100,
            average_win=float(wins.mean()) if wins.size else 0.0,
            average_loss=float(losses.mean()) if losses.size else 0.0,
            largest_win=float(wins.max()) if wins.size else 0.0,
            largest_loss=float(losses.min()) if losses.size else 0.0,
            total_trades=len(trades),
            long_trades=len(long_trades),
            long_win_rate_pct=self._win_rate(long_trades),
            short_trades=len(short_trades),
            short_win_rate_pct=self._win_rate(short_trades),
            average_holding_time=str(self._average_holding_time(trades)),
        )

    @staticmethod
    def _years(equity_curve: pd.DataFrame) -> float:
        if equity_curve.empty or len(equity_curve) < 2:
            return 0.0
        delta = equity_curve["timestamp"].iloc[-1] - equity_curve["timestamp"].iloc[0]
        return max(delta.total_seconds() / (365.25 * 24 * 3600), 0.0)

    @staticmethod
    def _sharpe(returns: pd.Series) -> float:
        if returns.empty or returns.std(ddof=0) == 0:
            return 0.0
        periods_per_year = 365.25 * 24
        return float((returns.mean() / returns.std(ddof=0)) * np.sqrt(periods_per_year))

    @staticmethod
    def _maximum_drawdown(equity_curve: pd.DataFrame) -> float:
        if equity_curve.empty:
            return 0.0
        equity = equity_curve["equity"]
        drawdown = equity / equity.cummax() - 1
        return abs(float(drawdown.min()))

    @staticmethod
    def _win_rate(trades: list[Trade]) -> float:
        if not trades:
            return 0.0
        wins = sum(1 for trade in trades if trade.net_profit_loss > 0)
        return wins / len(trades) * 100

    @staticmethod
    def _average_holding_time(trades: list[Trade]) -> pd.Timedelta:
        if not trades:
            return pd.Timedelta(0)
        return sum((trade.trade_duration for trade in trades), pd.Timedelta(0)) / len(trades)

