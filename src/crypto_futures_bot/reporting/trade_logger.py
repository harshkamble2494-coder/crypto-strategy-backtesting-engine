from __future__ import annotations

from pathlib import Path

import pandas as pd

from crypto_futures_bot.backtesting.trade import Trade


class TradeLogger:
    def write_csv(self, trades: list[Trade], output_path: Path) -> None:
        rows = [
            {
                "Entry Time": trade.entry_time,
                "Exit Time": trade.exit_time,
                "Trade Direction": trade.direction,
                "Entry Price": trade.entry_price,
                "Exit Price": trade.exit_price,
                "Stop Loss": trade.stop_loss,
                "Take Profit": trade.take_profit,
                "Position Size": trade.position_size,
                "Gross Profit/Loss": trade.gross_profit_loss,
                "Net Profit/Loss": trade.net_profit_loss,
                "Account Balance": trade.account_balance,
                "Trade Duration": trade.trade_duration,
                "Exit Reason": trade.exit_reason,
            }
            for trade in trades
        ]
        pd.DataFrame(rows).to_csv(output_path, index=False)

