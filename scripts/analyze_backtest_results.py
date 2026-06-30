from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def profit_factor(series: pd.Series) -> float:
    wins = series[series > 0].sum()
    losses = series[series < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze generated backtest artifacts.")
    parser.add_argument("result_dir")
    args = parser.parse_args()

    base = Path(args.result_dir)
    trades = pd.read_csv(base / "trades.csv", parse_dates=["Entry Time", "Exit Time"])
    equity = pd.read_csv(base / "equity_curve.csv", parse_dates=["timestamp"])

    trades["month"] = trades["Exit Time"].dt.to_period("M").astype(str)
    trades["duration_h"] = (trades["Exit Time"] - trades["Entry Time"]).dt.total_seconds() / 3600
    trades["ret_pct"] = trades["Net Profit/Loss"] / (trades["Entry Price"] * trades["Position Size"]) * 100

    print("rows", len(trades), "equity rows", len(equity))
    print("\nBy direction")
    print(
        trades.groupby("Trade Direction")
        .agg(
            trades=("Net Profit/Loss", "size"),
            net=("Net Profit/Loss", "sum"),
            win_rate=("Net Profit/Loss", lambda s: (s > 0).mean() * 100),
            avg=("Net Profit/Loss", "mean"),
            avg_ret=("ret_pct", "mean"),
            pf=("Net Profit/Loss", profit_factor),
        )
        .round(4)
    )

    print("\nBy exit reason")
    print(
        trades.groupby("Exit Reason")
        .agg(
            trades=("Net Profit/Loss", "size"),
            net=("Net Profit/Loss", "sum"),
            win_rate=("Net Profit/Loss", lambda s: (s > 0).mean() * 100),
            avg=("Net Profit/Loss", "mean"),
            avg_duration_h=("duration_h", "mean"),
        )
        .round(4)
    )

    print("\nBy direction/exit")
    print(
        trades.groupby(["Trade Direction", "Exit Reason"])
        .agg(trades=("Net Profit/Loss", "size"), net=("Net Profit/Loss", "sum"), avg=("Net Profit/Loss", "mean"))
        .round(2)
    )

    print("\nMonthly pnl/trades")
    print(
        trades.groupby("month")
        .agg(
            trades=("Net Profit/Loss", "size"),
            net=("Net Profit/Loss", "sum"),
            win_rate=("Net Profit/Loss", lambda s: (s > 0).mean() * 100),
        )
        .round(2)
        .to_string()
    )

    print("\nWorst 10 trades")
    print(
        trades.nsmallest(10, "Net Profit/Loss")[
            ["Entry Time", "Exit Time", "Trade Direction", "Net Profit/Loss", "Exit Reason", "duration_h", "ret_pct"]
        ].to_string(index=False)
    )

    print("\nBest 10 trades")
    print(
        trades.nlargest(10, "Net Profit/Loss")[
            ["Entry Time", "Exit Time", "Trade Direction", "Net Profit/Loss", "Exit Reason", "duration_h", "ret_pct"]
        ].to_string(index=False)
    )

    print("\nDurations by outcome")
    print(
        trades.assign(win=trades["Net Profit/Loss"] > 0)
        .groupby("win")
        .agg(
            trades=("Net Profit/Loss", "size"),
            avg_duration=("duration_h", "mean"),
            median_duration=("duration_h", "median"),
            avg_pnl=("Net Profit/Loss", "mean"),
        )
        .round(3)
    )

    curve = equity.copy()
    curve["peak"] = curve["equity"].cummax()
    curve["dd"] = curve["equity"] / curve["peak"] - 1
    print("\nMax DD point")
    print(curve.loc[curve["dd"].idxmin(), ["timestamp", "equity", "peak", "dd"]])

    print("\nMonthly equity returns")
    monthly = equity.set_index("timestamp")["equity"].resample("ME").last().pct_change().dropna() * 100
    print(monthly.round(2).to_string())

    print("\nCost impact")
    print("gross pnl", trades["Gross Profit/Loss"].sum())
    print("net pnl", trades["Net Profit/Loss"].sum())
    print("fees", (trades["Gross Profit/Loss"] - trades["Net Profit/Loss"]).sum())
    print("gross win rate", (trades["Gross Profit/Loss"] > 0).mean() * 100)
    print("net win rate", (trades["Net Profit/Loss"] > 0).mean() * 100)


if __name__ == "__main__":
    main()
