from crypto_futures_bot.config.models import RiskConfig
from crypto_futures_bot.risk_management.position_sizer import PositionSizer


def test_position_sizing_uses_risk_and_stop_distance() -> None:
    config = RiskConfig(
        leverage=2.0,
        risk_per_trade=0.01,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
    )

    quantity = PositionSizer(config).calculate_quantity(equity=10_000, entry_price=50_000)

    assert round(quantity, 8) == round(100 / 750, 8)


def test_position_sizing_respects_leverage_cap() -> None:
    config = RiskConfig(
        leverage=1.0,
        risk_per_trade=0.50,
        stop_loss_pct=0.01,
        take_profit_pct=0.03,
        max_daily_loss_pct=0.03,
    )

    quantity = PositionSizer(config).calculate_quantity(equity=10_000, entry_price=50_000)

    assert quantity == 0.2

