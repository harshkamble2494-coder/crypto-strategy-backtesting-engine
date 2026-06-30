import pandas as pd

from crypto_futures_bot.config.models import CostConfig, RiskConfig
from crypto_futures_bot.execution.execution_engine import ExecutionEngine
from crypto_futures_bot.strategy.signals import SignalType


def _cost_config() -> CostConfig:
    return CostConfig(fee_rate=0.0005, slippage_pct=0.0)


def test_atr_exit_prices_for_long_position() -> None:
    risk = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
        exit_mode="atr",
        atr_stop_loss_multiplier=1.5,
        atr_take_profit_multiplier=3.0,
    )

    position = ExecutionEngine(risk, _cost_config()).open_position(
        signal=SignalType.LONG,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    assert position.stop_loss == 97.0
    assert position.take_profit == 106.0


def test_atr_exit_prices_for_short_position() -> None:
    risk = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
        exit_mode="atr",
        atr_stop_loss_multiplier=1.5,
        atr_take_profit_multiplier=3.0,
    )

    position = ExecutionEngine(risk, _cost_config()).open_position(
        signal=SignalType.SHORT,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    assert position.stop_loss == 103.0
    assert position.take_profit == 94.0


def test_fixed_exit_mode_remains_available() -> None:
    risk = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
        exit_mode="fixed",
    )

    position = ExecutionEngine(risk, _cost_config()).open_position(
        signal=SignalType.LONG,
        timestamp=pd.Timestamp("2026-01-01", tz="UTC"),
        price=100.0,
        quantity=1.0,
        atr=2.0,
    )

    assert position.stop_loss == 98.5
    assert position.take_profit == 103.0
