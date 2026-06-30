from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from crypto_futures_bot.backtesting.trade import Trade


class ChartGenerator:
    def generate_all(self, equity_curve: pd.DataFrame, trades: list[Trade], output_dir: Path) -> None:
        self.equity_curve(equity_curve, output_dir / "equity_curve.png")
        self.drawdown_curve(equity_curve, output_dir / "drawdown_curve.png")
        self.monthly_returns(equity_curve, output_dir / "monthly_returns.png")
        self.trade_return_distribution(trades, output_dir / "trade_return_distribution.png")

    def equity_curve(self, equity_curve: pd.DataFrame, output_path: Path) -> None:
        if equity_curve.empty:
            return
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(equity_curve["timestamp"], equity_curve["equity"], color="#1f77b4")
        ax.set_title("Equity Curve")
        ax.set_xlabel("Time")
        ax.set_ylabel("Equity")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)

    def drawdown_curve(self, equity_curve: pd.DataFrame, output_path: Path) -> None:
        if equity_curve.empty:
            return
        equity = equity_curve["equity"]
        drawdown = equity / equity.cummax() - 1
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.fill_between(equity_curve["timestamp"], drawdown * 100, color="#d62728", alpha=0.35)
        ax.set_title("Drawdown Curve")
        ax.set_xlabel("Time")
        ax.set_ylabel("Drawdown (%)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)

    def monthly_returns(self, equity_curve: pd.DataFrame, output_path: Path) -> None:
        if equity_curve.empty:
            return
        monthly = equity_curve.set_index("timestamp")["equity"].resample("ME").last().pct_change().dropna() * 100
        if monthly.empty:
            return
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(monthly.index, monthly.values, width=20, color=["#2ca02c" if value >= 0 else "#d62728" for value in monthly.values])
        ax.set_title("Monthly Returns")
        ax.set_xlabel("Month")
        ax.set_ylabel("Return (%)")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)

    def trade_return_distribution(self, trades: list[Trade], output_path: Path) -> None:
        returns = [trade.return_pct * 100 for trade in trades]
        if not returns:
            return
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.hist(returns, bins=30, color="#9467bd", edgecolor="white")
        ax.set_title("Distribution of Trade Returns")
        ax.set_xlabel("Trade Return (%)")
        ax.set_ylabel("Frequency")
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)
