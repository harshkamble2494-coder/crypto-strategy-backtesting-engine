import pandas as pd

from crypto_futures_bot.config.models import CostConfig, RiskConfig
from crypto_futures_bot.execution.execution_engine import ExecutionEngine
from crypto_futures_bot.strategy.signals import SignalType


def _cost_config() -> CostConfig:
    return CostConfig(fee_rate=0.0005, slippage_pct=0.0)


def _risk_config(enabled: bool, trigger: float = 1.0) -> RiskConfig:
    return RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
        exit_mode="fixed",
        break_even_enabled=enabled,
        break_even_trigger_atr_multiplier=trigger,
    )


def test_break_even_moves_long_stop_to_entry_after_trigger() -> None:
    engine = ExecutionEngine(_risk_config(enabled=True, trigger=1.0), _cost_config())
    position = engine.open_position(
        signal=SignalType.LONG,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    exit_check = engine.check_exit(
        position,
        pd.Series({"high": 102.5, "low": 100.0, "close": 101.0}),
        opposite_signal=False,
    )

    assert position.break_even_activated is True
    assert position.stop_loss == position.entry_price
    assert exit_check == (100.0, "BREAK_EVEN_STOP")


def test_break_even_moves_short_stop_to_entry_after_trigger() -> None:
    engine = ExecutionEngine(_risk_config(enabled=True, trigger=1.0), _cost_config())
    position = engine.open_position(
        signal=SignalType.SHORT,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    exit_check = engine.check_exit(
        position,
        pd.Series({"high": 100.0, "low": 97.5, "close": 99.0}),
        opposite_signal=False,
    )

    assert position.break_even_activated is True
    assert position.stop_loss == position.entry_price
    assert exit_check == (100.0, "BREAK_EVEN_STOP")


def test_break_even_disabled_keeps_original_stop() -> None:
    engine = ExecutionEngine(_risk_config(enabled=False), _cost_config())
    position = engine.open_position(
        signal=SignalType.LONG,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    exit_check = engine.check_exit(
        position,
        pd.Series({"high": 102.5, "low": 100.0, "close": 101.0}),
        opposite_signal=False,
    )

    assert position.break_even_activated is False
    assert position.stop_loss == 98.5
    assert exit_check is None
