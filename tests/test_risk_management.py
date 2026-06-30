import pandas as pd

from crypto_futures_bot.config.models import RiskConfig
from crypto_futures_bot.risk_management.risk_manager import RiskManager


def test_daily_loss_lockout_blocks_new_trades_after_threshold() -> None:
    config = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
    )
    manager = RiskManager(config, initial_capital=10_000)
    timestamp = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")

    manager.register_day(timestamp, equity=10_000)
    manager.record_realized_pnl(timestamp, pnl=-300)

    assert manager.can_open_new_trade(timestamp) is False


def test_daily_loss_lockout_resets_next_day() -> None:
    config = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
    )
    manager = RiskManager(config, initial_capital=10_000)
    day_one = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")
    day_two = pd.Timestamp("2026-01-02 00:00:00", tz="UTC")

    manager.register_day(day_one, equity=10_000)
    manager.record_realized_pnl(day_one, pnl=-300)
    manager.register_day(day_two, equity=9_700)

    assert manager.can_open_new_trade(day_two) is True
