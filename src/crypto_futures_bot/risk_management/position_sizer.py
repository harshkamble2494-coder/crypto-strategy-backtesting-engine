from __future__ import annotations

from crypto_futures_bot.config.models import RiskConfig


class PositionSizer:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def calculate_quantity(self, equity: float, entry_price: float) -> float:
        risk_amount = equity * self.config.risk_per_trade
        stop_distance = entry_price * self.config.stop_loss_pct
        if stop_distance <= 0:
            raise ValueError("Stop distance must be greater than zero.")

        risk_based_quantity = risk_amount / stop_distance
        max_leveraged_quantity = (equity * self.config.leverage) / entry_price
        return max(0.0, min(risk_based_quantity, max_leveraged_quantity))

